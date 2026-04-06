# ChainBot 🔗

A Discord AI bot that mimics a specific user's persona using AWS Bedrock LLM and a dataset of sample messages. The bot responds in a casual, humorous style based on the persona samples, integrating seamlessly into Discord chats.

## Features

- **Persona Mimicry**: Uses a dataset of real messages to ground the AI's responses in the target persona's style.
- **Keyword Triggers**: Responds to mentions or specific keywords like "bot", "chain", etc.
- **AWS Bedrock Integration**: Leverages Amazon Nova Micro model for fast, cost-effective responses.
- **Logging**: Saves bot responses to `logs/messages.log` for monitoring and debugging.
- **Data Collection Tools**: Scripts to collect and process persona samples from Discord.

## Project Structure

```
root/
├── bot.py                  # Main Discord bot client and event handling
├── llm.py                  # AWS Bedrock LLM integration for generating responses
├── persona.py              # Loads and samples persona messages from dataset
├── test_bot.py             # Unit tests for bot functionality
├── test_llm.py             # Tests for LLM integration
├── test_persona.py         # Tests for persona loading
├── requirements.txt        # Python dependencies
├── logs/
│   └── messages.log        # Bot response logs (created automatically)
├── data/
│   ├── README.md           # Explanation of data collection tools
│   ├── collector_bot.py    # Discord scraper for collecting persona messages
│   ├── collector_easy.py   # Processes Discord data export JSON to create dataset
│   ├── __chain_samples.txt # Backup or example dataset
│   ├── alex_samples.txt    # Additional sample data
│   ├── samples.txt         # More sample messages
│   └── Messages/           # Discord data export (JSON files)
└── README.md               # This file
```

### File Descriptions

- **bot.py**: The core Discord bot using discord.py. Handles events like `on_ready` and `on_message`, checks for triggers, generates responses via LLM, and logs them.
- **llm.py**: Manages interactions with AWS Bedrock. Builds system prompts from persona samples and calls the Nova Micro model.
- **persona.py**: Loads persona samples from a text file (path set via `DATASET_PATH` env var), samples a subset for each request to limit prompt size.
- **requirements.txt**: Lists Python packages needed (discord.py, boto3, python-dotenv, etc.).
- **data/collector_bot.py**: Scrapes messages from specified Discord channels using a scraper token, filters for the target user, and saves to dataset.
- **data/collector_easy.py**: Processes JSON files from Discord's data export to extract messages and write to dataset file.
- **data/Messages/**: Contains exported Discord data in JSON format for processing.

## Setup

### Prerequisites

- Python 3.8+
- AWS account with Bedrock access
- Discord bot token

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root directory:

```env
DISCORD_TOKEN=your_discord_bot_token
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
DATASET_PATH=data/samples.txt  # Path to persona dataset file
```

- `DISCORD_TOKEN`: From [Discord Developer Portal](https://discord.com/developers/applications).
- AWS credentials: From AWS IAM console.
- `DATASET_PATH`: Path to the text file containing persona samples (one per line).

### 3. Enable AWS Bedrock Model Access

In AWS Console → Bedrock → Model access, request access to:
- `amazon.nova-micro-v1:0` (default model)

### 4. Discord Bot Setup

- Create a bot in Discord Developer Portal.
- Under Bot settings, enable "Message Content Intent".
- Add bot to your server with permissions: Read Messages, Send Messages, Read Message History.

## Running the Bot

```bash
python bot.py
```

The bot will log in, load persona samples, and start listening for messages.

## Collecting Persona Data

To build the dataset:

1. **Using Discord Data Export**:
   - Request your data from Discord (User Settings → Privacy & Safety → Request Data).
   - Place the exported `Messages/` folder in `data/`.
   - Run `python data/collector_easy.py` to process JSON and create/update the dataset file.

2. **Using Live Scraper** (requires additional env vars):
   - Set `DISCORD_SCRAPER_TOKEN`, `DISCORD_CHANNEL_ID`, `USER_ID`, `DATASET_PATH`.
   - Run `python data/collector_bot.py` to scrape recent messages from channels.

See `data/README.md` for detailed instructions on collectors.

## Configuration

- **Trigger Keywords**: Edit `TRIGGER_KEYWORDS` in `bot.py`.
- **LLM Model**: Change `MODEL_ID` in `llm.py` (ensure Bedrock access).
- **Persona Samples**: Adjust `MAX_PERSONA_SAMPLES` in `persona.py` for prompt size.
- **Logging**: Modify logging config in `bot.py` for different levels or formats.
