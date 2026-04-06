# Data Collection Tools

This folder contains scripts to collect and process persona samples for the bot. These samples are used to ground the AI so it mimics the target user's style.

## Files

### collector_bot.py

A Discord scraper that collects messages from specified channels in real-time.

**Purpose**: Fetches recent messages from Discord channels where the target user has posted, filters them, and saves to a dataset file.

**Requirements**:
- `DISCORD_SCRAPER_TOKEN`: A separate Discord bot token for scraping (different from the main bot token).
- `DISCORD_CHANNEL_ID`: Comma-separated list of channel IDs to scrape.
- `DISCORD_TEST_CHANNEL_ID`: For testing mode.
- `USER_ID`: The Discord user ID of the persona to mimic.
- `DATASET_PATH`: Path to the output dataset file (e.g., `data/samples.txt`).

**Usage**:
1. Create another [Discord bot](https://discord.com/developers/applications) to scrape message data.
2. Set environment variables in `.env`.
3. Run `python data/collector_bot.py`.
4. It will log in, collect messages from channels, and overwrite the dataset file with new samples.

**Notes**:
- Filters out short messages, links, mentions.
- Collects from oldest to newest after a certain date.
- Use `TESTING = True` for test mode with `DISCORD_TEST_CHANNEL_ID` and `TEST_USER_ID`.

### collector_easy.py

Processes JSON files from Discord's data export to create a dataset.

**Purpose**: If you have a Discord data export (requested via User Settings → Privacy & Safety → Request Data), this script extracts messages from the `Messages/` folder and writes them to the dataset file.

**Requirements**:
- `DATASET_PATH`: Path to the output dataset file.

**Usage**:
1. Place the exported `Messages/` folder (containing channel subfolders with `messages.json`) in `data/`.
2. Run `python data/collector_easy.py`.
3. It will iterate through all `messages.json` files, extract content, and write to the dataset (overwrites existing file).

**Notes**:
- Skips links and empty messages.
- Much faster than live scraping if you have historical data.
- The `Messages/index.json` and channel folders are expected.

## Dataset Format

The output is a plain text file with one message per line:

```
Hello my loyal subjects
man... I'm good
what the beep
```

Blank lines and comments (#) are ignored when loading.

## Environment Variables

Add these to your `.env` file for collectors:

```env
# For collector_bot.py
DISCORD_SCRAPER_TOKEN=your_scraper_token
DISCORD_CHANNEL_ID=123456789,987654321
DISCORD_TEST_CHANNEL_ID=111222333
USER_ID=444555666
TEST_USER_ID=777888999
DATASET_PATH=data/samples.txt

# For collector_easy.py
DATASET_PATH=data/samples.txt
```

## Tips

- Run collectors periodically to update the dataset with new messages.
- Combine both methods: use `collector_easy.py` for bulk historical data, `collector_bot.py` for recent updates.
- Ensure the dataset file is readable by the bot (set via `DATASET_PATH` in main `.env`).