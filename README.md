## Studio‑AI Bot

A lightweight Slack bot that delivers GPT‑4‑class answers right inside your workspace—thread‑first, markdown‑aware, and Cloud Run–native.

---

### Table of Contents

1. [Why Studio‑AI?](#why-studio-ai)
2. [Features](#features)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Slash Commands](#slash-commands)
6. [Architecture](#architecture)
7. [Local Development](#local-development)
8. [Deploying to Google Cloud Run](#deploying-to-google-cloud-run)
9. [Troubleshooting & FAQ](#troubleshooting--faq)
10. [Contributing](#contributing)
11. [License](#license)

---

## Why Studio‑AI?  ([FreeCodeCamp][1], [GitHub][2])

* **Thread‑native:** Replies always land in a Slack thread, keeping channels noise‑free.
* **Admin‑tunable:** `/ai‑settings` modal lets trusted users switch model, temperature, history depth, etc.—no redeploy required.
* **Secure by design:** OpenAI key lives in Cloud Run env‑vars/Secret Manager; never passes through Slack.
* **Budget‑friendly:** Scales to zero, or keep a warm instance for instant slash‑command response.

---

## Features  ([GitHub][3], [GitHub][4])

| Capability                      | Details                                                      |
| ------------------------------- | ------------------------------------------------------------ |
| **GPT‑4o / GPT‑4 selectable**   | Toggle model in the settings modal.                          |
| **Markdown → Slack formatting** | Converts `**bold**`, `~~strike~~`, headings & bullets.       |
| **Duplicate‑line filter**       | Removes the rare “double echo” on first completion.          |
| **Help command**                | `/ai‑help` DMs the quick guide to any user.                  |
| **Extensible events**           | Bolt listeners for `app_mention`, DMs, and threaded replies. |

---

## Quick Start

```bash
# clone & enter
git clone https://github.com/your‑org/studio‑ai-bot.git
cd studio‑ai-bot

# run locally (env vars must be set)
pip install -r requirements.txt
python main.py
```

Invite **@Studio AI** to a channel and mention it:
`@Studio AI what’s our sprint goal?`

---

## Configuration

| Variable               | Where set                         | Description                                  |
| ---------------------- | --------------------------------- | -------------------------------------------- |
| `SLACK_BOT_TOKEN`      | Cloud Run > Environment Variables | xoxb‑ token from Slack OAuth page.           |
| `SLACK_SIGNING_SECRET` | same                              | Verifies Slack signatures.                   |
| `OPENAI_API_KEY`       | Secret Manager / env              | Your OpenAI key.                             |
| `MIN_INSTANCES`        | Cloud Run flag                    | `0` (free but cold‑start) or `1` (\~\$7/mo). |

Settings editable at runtime (`/ai‑settings` modal):

| Field                 | Default                        |
| --------------------- | ------------------------------ |
| Model                 | `gpt‑4o‑mini`                  |
| Temperature           | `0.3`                          |
| Max tokens            | `512`                          |
| System prompt         | “You are a helpful assistant.” |
| Broadcast first reply | off                            |
| Thread history depth  | 8                              |

---

## Slash Commands

| Command        | Who can use                  | Purpose               |
| -------------- | ---------------------------- | --------------------- |
| `/ai-help`     | everyone                     | DM quick usage guide. |
| `/ai-settings` | IDs in `ALLOWED_ADMINS` list | Open settings modal.  |

Register each under **Slack App → Slash Commands** with request URL
`https://<cloud‑run‑url>/slack/events`. ([GitHub][5])

---

## Architecture  ([EHeidi.dev][6], [GitHub][5])

* **Python 3.11** + **Flask** + **Slack Bolt** handle HTTP & events.
* **OpenAI Python SDK** streams completions.
* **Google Cloud Run** containerizes the app; Buildpacks build the image.
* **Cloud Scheduler** (optional) pings `/` every 5 min to keep one warm instance when `min-instances` = 0.

```
Slack  →  /slack/events  →  Bolt listener  →  OpenAI API
                     ↑                       ↓
                 Cloud Run  ← Scheduler ping (optional)
```

---

## Local Development

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate
python -m pip install --upgrade pip
pip install -r requirements.txt
# expose ngrok or Cloudflare tunnel if you want to test Slack events locally
```

---

## Deploying to Google Cloud Run  ([GitHub][5])

```bash
gcloud run deploy studio-ai-bot \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --min-instances 1          # speed ↔ cost toggle
```

Need scale‑to‑zero? Set `--min-instances 0` (expect 3‑5 s cold‑start).

---

## Troubleshooting & FAQ

| Symptom                                      | Fix                                                                                    |
| -------------------------------------------- | -------------------------------------------------------------------------------------- |
| **`operation_timeout` after `/ai-settings`** | Keep one warm instance (`gcloud run services update … --min-instances 1`).             |
| Bot replies twice                            | Ensure only `app_mention` triggers; code already ignores duplicate `message` events.   |
| No reply at all                              | Confirm Event Subscriptions ON, `app_mentions:read` scope, and bot invited to channel. |
| Linter: “decorator line break”               | Use multi‑line decorator style (already fixed).                                        |
| Pip upgrade WinError 123                     | Use `python -m pip install --upgrade --user pip` or a virtual‑env.                     |

---

## Contributing  ([Make a README][7])

Pull requests welcome! Please open an issue first to discuss major changes.
See `CONTRIBUTING.md` for code style and commit message guidelines.

---

## License

Berkeley Goodloe © 2025  See `LICENSE` for details.

