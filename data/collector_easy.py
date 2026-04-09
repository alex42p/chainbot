import os
import json
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("data_request")
handler = logging.FileHandler("logs/data_request.log", mode='w', encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

DATASET_PATH = os.getenv("DATASET_PATH", "")
if not DATASET_PATH:
    raise ValueError("Missing required environment variable DATASET_PATH.")

# if data is collected from Discord data request, saves a LOT of time
def write_messages_from_data():
    """
    Iterate through all messages.json files in the Messages folder and write
    every Content value to the dataset file, one per line.
    """
    messages_dir = os.path.join(os.path.dirname(__file__), "Messages")
    
    if not os.path.isdir(messages_dir):
        raise ValueError(f"Messages directory not found at {messages_dir}")
    
    total_messages = 0
    with open(DATASET_PATH, 'w', encoding='utf-8') as output_file: # change to 'a' once working well
        # Iterate through all subfolders (channel IDs)
        for channel_id in os.listdir(messages_dir):
            channel_path = os.path.join(messages_dir, channel_id)
            
            # Only process directories
            if os.path.isdir(channel_path):
                messages_file = os.path.join(channel_path, "messages.json")
                
                # Check if messages.json exists in this channel directory
                if os.path.isfile(messages_file):
                    try:
                        with open(messages_file, 'r', encoding='utf-8') as f:
                            messages = json.load(f)
                            
                            # Extract content from each message
                            for message in messages:
                                content = message.get("Contents", "").strip()
                                # Only write non-empty content
                                if content and not content.startswith("http"):  # Skip links
                                    output_file.write(content + "\n")
                                    total_messages += 1
                    except (json.JSONDecodeError, IOError) as e:
                        logger.warning(f"Error reading {messages_file}: {e}")
    
    logger.info(f"Successfully wrote {total_messages} messages to {DATASET_PATH}")

if __name__ == "__main__":
    write_messages_from_data()