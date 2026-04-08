"""
data/collector_bot.py — Collects Chainman's sample messages from Discord
                    and saves them to a plain-text dataset file.

This script scrapes messages from a specified Discord channel and saves them to a .txt file, 
which is then used as training data to ground Chainman's persona. Run this script
periodically (e.g. once a week) to keep the dataset up to date with Chainman's latest sayings.
"""

import os
import discord
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

DISCORD_SCRAPER_TOKEN = os.getenv("DISCORD_SCRAPER_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "") # can be one or more comma-separated IDs
DISCORD_TEST_CHANNEL_ID = os.getenv("DISCORD_TEST_CHANNEL_ID", "")
DATASET_PATH = os.getenv("DATASET_PATH", "")
intents = discord.Intents.default()
intents.message_content = True # allows to read messages
intents.guilds = True
client = discord.Client(intents=intents)

TESTING = False # change to False when collecting real user's data

if not all([DISCORD_SCRAPER_TOKEN, DISCORD_CHANNEL_ID, DATASET_PATH]):
    raise ValueError(
        "Missing required environment variables. "
        "Please set DISCORD_SCRAPER_TOKEN, DISCORD_CHANNEL_ID, and DATASET_PATH."
    )

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    messages = await collect_messages()

    with open(DATASET_PATH, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(msg + "\n")

    print(f"Collected and saved {len(messages)} messages")

    # await client.close()


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
                print(f"Invalid channel ID: {cid}")
    else: # just a single channel ID
        try:
            channel_ids.append(int(ids))
        except ValueError:
            print(f"Invalid channel ID: {ids}")
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
                print(f"Collecting messages from channel: {channel.name} (ID: {cid})")
                async for message in channel.history(limit=None, oldest_first=True, after=datetime(2023, 1, 1)): # Adjust limit as needed
                    if message.author.id == target_user_id and message.content.strip() and not message.content.startswith("http") and not message.content.startswith("@") and not message.content.startswith("<@") and len(message.content) > 3:
                        messages.append(message.content)
        except discord.HTTPException as e:
            print(f"Error fetching channel {cid}: {e}")
        except discord.InvalidData:
            print(f"Invalid channel ID: {cid}")
    return messages

def write_messages():
    """Append collected messages to the dataset file, one per line."""
    messages = client.loop.run_until_complete(collect_messages())
    with open(DATASET_PATH, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(msg + "\n")
    print(f"Collected and saved {len(messages)} message(s) to '{DATASET_PATH}'.")


if __name__ == "__main__": #TODO: improve ts 
    if not DISCORD_SCRAPER_TOKEN:
        raise ValueError("DISCORD_SCRAPER_TOKEN is not set in your .env file.")
    if not DATASET_PATH:
        raise ValueError("DATASET_PATH is not set in your .env file.")
    client.run(DISCORD_SCRAPER_TOKEN)
    # write_messages()
