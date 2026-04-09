"""
persona.py — Loads user's sample messages from a plain-text dataset.

Expected dataset format (one message per line):
────────────────────────────────────────────────
Hello my loy-dhdjdbsbudjjd-al subjects
man... I'm good
what the beep
...
────────────────────────────────────────────────

Blank lines and lines starting with # are ignored so you can add comments
or section breaks to the .txt file.
"""

import os
import random
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("persona")
handler = logging.FileHandler("logs/persona_setup.log", mode='w', encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

DATASET_PATH = os.getenv("DATASET_PATH", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_KEY = os.getenv("S3_KEY", "")
MAX_PERSONA_SAMPLES = 400

if not DATASET_PATH and not S3_BUCKET:
    logger.warning("Need to get a persona from somewhere big dawg. Pick one")

def load_persona_samples(load_type: str = "") -> list[str]:
    if load_type == "s3":
        return load_persona_samples_from_s3()
    return load_persona_samples_from_file()
    

def load_persona_samples_from_s3() -> list[str]:
    """
    Load persona samples from an S3 bucket and return the sample list.

    The bucket is defined by the S3_BUCKET environment variable,
    and the object key is fixed to the samples filename.
    """
    if not S3_BUCKET:
        logger.warning(
            "S3_BUCKET is not set. Falling back to local dataset file."
        )
        return load_persona_samples_from_file()

    try:
        s3 = boto3.client(
            service_name="s3",
            region_name=os.getenv("AWS_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")    
        )
        response = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        body = response["Body"].read().decode("utf-8")
    except ClientError as e:
        logger.error(
            f"Failed to load persona samples from S3 bucket "
            f"'{S3_BUCKET}': {e.response['Error']['Message']}.")
        return load_persona_samples_from_file()
    except Exception as e:
        logger.error(f"Unexpected error loading S3 persona samples: {e}")
        return load_persona_samples_from_file()

    samples: list[str] = []
    for raw_line in body.splitlines():
        line: str = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        samples.append(line)

    logger.info(f"Loaded {len(samples)} persona samples from S3 bucket.")
    return samples

def load_persona_samples_from_file() -> list[str]:
    """
    Read the dataset file and return a list of sample message strings.

    Returns an empty list (with a warning) if the file doesn't exist yet —
    the bot will still run, just without persona grounding.
    """
    logger.info("Attempting to load persona samples from local file...")
    if not os.path.exists(DATASET_PATH):
        logger.warning(
            f"Dataset not found at '{DATASET_PATH}'. "
            "Bot will run without persona samples until the file is added."
        )
        return []

    samples: list[str] = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            # Skip blanks and comment lines
            if not line or line.startswith("#"):
                continue
            samples.append(line)

    logger.info(f"Loaded {len(samples)} sample(s) from local dataset.")
    return samples

def sample_persona_samples(
    samples: list[str],
    max_samples: int = MAX_PERSONA_SAMPLES,
) -> list[str]:
    """Return a random subset of persona samples up to max_samples."""
    if len(samples) <= max_samples:
        return list(samples)
    return random.sample(samples, max_samples)
