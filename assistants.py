import os
import json
import openai
from time import sleep
from dotenv import load_dotenv
import io
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load your OpenAI API key from the .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def execute_function(function_name, arguments, from_user):
    """
    Execute a function based on the function name and provided arguments.
    """
    if function_name == 'create_ticket':
        subject = arguments.get("subject")
        type_of_question = arguments.get("type_of_question")
        description = arguments.get("description")
        # Note: create_ticket function would need to be implemented separately
        return f"Ticket created: {subject} - {description}"
    else:
        return "Function not recognized"

def process_thread_with_assistant(user_query, assistant_id, model="gpt-4-1106-preview", from_user=None):
    """
    Process a thread with an assistant and handle the response which includes text and images.

    :param user_query: The user's query.
    :param assistant_id: The ID of the assistant to be used.
    :param model: The model version of the assistant.
    :param from_user: The user ID from whom the query originated.
    :return: A dictionary containing text responses and in-memory file objects.
    """
    response_texts = []  # List to store text responses
    response_files = []  # List to store file IDs
    in_memory_files = []  # List to store in-memory file objects

    try:
        logger.info("Creating a thread for the user query...")
        client = openai.OpenAI()
        thread = client.beta.threads.create()
        logger.info(f"Thread created with ID: {thread.id}")

        logger.info("Adding the user query as a message to the thread...")
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_query
        )
        logger.info("User query added to the thread.")

        logger.info("Creating a run to process the thread with the assistant...")
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
            model=model
        )
        logger.info(f"Run created with ID: {run.id}")

        while True:
            logger.info("Checking the status of the run...")
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            logger.info(f"Current status of the run: {run_status.status}")

            if run_status.status == "requires_action":
                logger.info("Run requires action. Executing specified function...")
                tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                function_output = execute_function(function_name, arguments, from_user)
                function_output_str = json.dumps(function_output)

                logger.info("Submitting tool outputs...")
                client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=[{
                        "tool_call_id": tool_call.id,
                        "output": function_output_str
                    }]
                )
                logger.info("Tool outputs submitted.")

            elif run_status.status in ["completed", "failed", "cancelled"]:
                logger.info("Fetching messages added by the assistant...")
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                for message in messages.data:
                    if message.role == "assistant":
                        for content in message.content:
                            if content.type == "text":
                                response_texts.append(content.text.value)
                            elif content.type == "image_file":
                                file_id = content.image_file.file_id
                                response_files.append(file_id)

                logger.info("Messages fetched. Retrieving content for each file ID...")
                for file_id in response_files:
                    try:
                        logger.info(f"Retrieving content for file ID: {file_id}")
                        file_response = client.files.content(file_id)
                        if hasattr(file_response, 'content'):
                            file_content = file_response.content
                        else:
                            file_content = file_response

                        in_memory_file = io.BytesIO(file_content)
                        in_memory_files.append(in_memory_file)
                        logger.info(f"In-memory file object created for file ID: {file_id}")
                    except Exception as e:
                        logger.error(f"Failed to retrieve content for file ID: {file_id}. Error: {e}")

                break
            sleep(1)

        return {"text": response_texts, "in_memory_files": in_memory_files}

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {"text": [], "in_memory_files": []}