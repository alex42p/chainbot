"""
data/collector_bot.py — Collects Chainman's sample messages from Discord
                    and saves them to a plain-text dataset file.

This script scrapes messages from a specified Discord channel and saves them to a .txt file, 
which is then used as training data to ground Chainman's persona. Run this script
periodically (e.g. once a week) to keep the dataset up to date with Chainman's latest sayings.
"""

import os
import sys
import discord
import logging
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("data_scraper")
handler = logging.FileHandler("logs/data_scraper.log", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

DISCORD_SCRAPER_TOKEN = os.getenv("DISCORD_SCRAPER_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "") # can be one or more comma-separated IDs
DISCORD_TEST_CHANNEL_ID = os.getenv("DISCORD_TEST_CHANNEL_ID", "")
DATASET_PATH = os.getenv("DATASET_PATH", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_KEY = os.getenv("S3_KEY", "")

intents = discord.Intents.default()
intents.message_content = True # allows to read messages
intents.guilds = True
client = discord.Client(intents=intents)

TESTING = False # change to False when collecting real user's data
WRITE_TO_S3 = True # set to True to upload the dataset to S3 after writing to local file

if not all([DISCORD_SCRAPER_TOKEN, DISCORD_CHANNEL_ID, DATASET_PATH]):
    raise ValueError(
        "Missing required environment variables. "
        "Please set DISCORD_SCRAPER_TOKEN, DISCORD_CHANNEL_ID, and DATASET_PATH."
    )

@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    messages = await collect_messages()

    with open(DATASET_PATH, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(msg + "\n")

    if WRITE_TO_S3: # after writing to file, upload to S3 bucket if True
        logger.info(f"Uploading dataset to S3 bucket {S3_BUCKET}...")
        s3_client = boto3.client("s3")
        try:
            s3_client.upload_file(DATASET_PATH, S3_BUCKET, S3_KEY)
            logger.info(f"Uploaded dataset of {len(messages)} messages to {S3_BUCKET}")
        except ClientError as e:
            logger.error(f"Error uploading to S3: {e.response['Error']['Message']}")

        # delete the local file after uploading to S3 if you don't want to keep it
        # os.remove(DATASET_PATH)
    
    logger.info(f"Collected and saved {len(messages)} messages")
    await client.close()
    sys.exit(0)


def check_channels() -> list[int]:
    """Check if CHANNEL_ID is a single ID or a comma-separated list, and return a list of channel IDs."""
    channel_ids = []
    if TESTING: 
        ids = DISCORD_TEST_CHANNEL_ID.strip()
    else: 
        ids = DISCORD_CHANNEL_ID.strip()
    
    if "," in ids:
        for cid in ids.split(","):
            try:
                channel_ids.append(int(cid.strip()))
            except ValueError:
                logger.error(f"Invalid channel ID: {cid}")
    else: # just a single channel ID
        try:
            channel_ids.append(int(ids))
        except ValueError:
            logger.error(f"Invalid channel ID: {ids}")
    return channel_ids

async def collect_messages() -> list[str]:
    if TESTING:
        target_user_id = int(os.getenv("TEST_USER_ID") or 0)
    else:
        target_user_id = int(os.getenv("USER_ID") or 0)
    if not target_user_id:
        raise ValueError("Missing USER_ID environment variable.")
    messages: list[str] = []
    for cid in check_channels():
        # channel = client.get_channel(cid)
        try:
            channel = await client.fetch_channel(cid)
            if not channel:
                continue
            if isinstance(channel, discord.abc.Messageable): # non-Messageable channels do not have history
                logger.info(f"Collecting messages from channel: {channel.guild} - {channel.name}")
                async for message in channel.history(limit=None, oldest_first=True, after=datetime(2023, 1, 1)): # Adjust limit as needed
                    if message.author.id == target_user_id and message.content.strip() and not message.content.startswith("http") and not message.content.startswith("@") and not message.content.startswith("<@") and len(message.content) > 3:
                        messages.append(message.content)
        except discord.HTTPException as e:
            logger.error(f"Error fetching channel {cid}: {e}")
        except discord.InvalidData:
            logger.error(f"Invalid channel ID: {cid}")
    return messages

if __name__ == "__main__":
    if not DISCORD_SCRAPER_TOKEN:
        raise ValueError("DISCORD_SCRAPER_TOKEN is not set in your .env file.")
    if not DATASET_PATH:
        raise ValueError("DATASET_PATH is not set in your .env file.")
    client.run(DISCORD_SCRAPER_TOKEN)
