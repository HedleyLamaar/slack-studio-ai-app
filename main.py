import os
import httpx
import re
from openai import OpenAI
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request

# HTTP client
http_client = httpx.Client(trust_env=False)

# OpenAI client
client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    http_client=http_client
)

# Slack app + handler
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)
handler = SlackRequestHandler(app)

def md_to_slack(text: str) -> str:
    # **bold** → *bold*
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)
    # ~~strike~~ → ~strike~
    text = re.sub(r"~~(.+?)~~", r"~\1~", text)
    # ### Heading or ## Heading → *Heading*
    text = re.sub(r"^#{2,3}\s*(.+)$", r"*\1*", text, flags=re.M)
    # Markdown list to bullet
    text = re.sub(r"(?m)^- ", "• ", text)
    return text

@app.message("")
def handle_message(message, say):
    text = message.get("text", "")
    if not text or message.get("subtype") == "bot_message":
        return

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user",   "content": text},
        ],
    )
    raw = resp.choices[0].message.content
    slack_ready = md_to_slack(raw)
    say(text=slack_ready)  # ← explicitly pass as text

# Flask entrypoint
flask_app = Flask(__name__)

@flask_app.route("/", methods=["GET"])
def health_check():
    return "OK"

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
