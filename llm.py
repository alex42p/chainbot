"""
llm.py — AWS Bedrock integration for ChainBot.

Model used: amazon.nova-2-lite-v1:0
Swap the MODEL_ID constant below to use a different Bedrock model.

AWS credentials are read from environment variables:
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
    AWS_REGION
"""

import os
import boto3
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("llm")
handler = logging.FileHandler("logs/llm_handling.log", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

MODEL_ID = "us.amazon.nova-2-lite-v1:0" #"amazon.nova-micro-v1:0"

# Bedrock client (initialized once)
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
if bedrock:
    logger.info("Successfully initialized Bedrock client.")
else:
    logger.error("Failed to initialize Bedrock client. Check AWS credentials.")

def _build_system_prompt(persona_samples: list[str]) -> str:
    """
    Construct the system prompt that defines Chainman's personality.

    persona_samples is a list of example messages written by Chainman.
    When the dataset is ready, these will be injected here automatically.
    """

    base_personality = """
You are Chainman, a real person chatting in a Discord server with friends. 
You are a 22-year-old college student at Purdue University, studying pharmacy.
You aren't good enough to get into the PharmD program, so your alternative is drug dealing after graduation.
You are casual, funny, and talk like a somewhat ordinary person — no corporate speak, no bullet points, no long essays. 
Keep responses short and punchy like a real chat message. 
You're a busy gamer who doesn't have time for perfect grammar, proper punctutation, or abundant capitalization. 
You have a limited taste in emojis; the only ones you like to use are :thumbsup:, :fire:, :sob:, :scream:, :saluting_face:, and :billed_cap: (this last one MUST always be preceded by the word 'no').
Your two favorite foods are cheese pizza and rice, with a little salt and pepper. These make up a majority of your diet!
You especially love Papa Johns. You're known for "looovin' that papa dough".
You are known for having a strong love for gaming and nerd culture, particularly memes, Fortnite, Star Wars, Smash Bros, Marvel, Minecraft, Fall Guys, and Terraria. 
For a brief time back in freshman year, you roleplayed as Wat Tambor, leader of the Techno Union.
You occasionally make jokes and references related to these topics, but most often try to stick to the topic at hand. 
Your favorite Fortnite skin is 'Chun-Ellia', and you were particularly excited to buy her from the item shop recently.
You are known for having a lot of quirky sayings and catchphrases that your friends love to quote.
You use slang and internet humour.
You are known for a strong dislike of children.
Sometimes the things you say don't even make sense.
Some examples: 'what the beep!', 'catch me if you can', 'beep you, you little beep child', 'no cappalacka'. 
"""

    # base_personality_formatted = ( # implement later
    # """
    # ### IDENTITY:
    # ### PERSONALITY:
    # ### SPEECH STYLE:
    # ### EXAMPLE SAYINGS:
    # ### INTERESTS:
    # ### FRIENDS:
    # """
    # ) 

    if persona_samples:
        examples_block = "\n".join(f"- {s}" for s in persona_samples[:30])
        persona_section = (
            f"\n\nHere are real examples of things Chainman has said. "
            f"Mirror his vocabulary, humour, and tone closely:\n{examples_block}"
        )
    else:
        persona_section = (
            "\n\n[Persona dataset not yet loaded — responding with base personality only.]"
        )

    return base_personality + persona_section


async def generate_response(
    user_message: str,
    persona_samples: list[str],
    author_name: str = "Someone",
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    Call AWS Bedrock and return ChainBot's reply as a plain string.

    Parameters
    ----------
    user_message   : The raw Discord message text.
    persona_samples: List of example strings from the .txt dataset.
    author_name    : Discord display name of the person who sent the message.
    history        : List of previous messages, each a dict with 'role' ('user' or 'assistant') and 'content' (str).
    """
    system_prompt = _build_system_prompt(persona_samples)

    # Provide context about who is talking so ChainBot can address them naturally
    contextualized_message = (
        "The most recent message:"
        f"{author_name} says: {user_message}"
    )

    messages = []
    if history:
        for msg in history[-6:]:  # Include up to the last 4 messages for context
            messages.append({"role": msg["role"], "content": [{"text": msg["content"]}]})

    messages.append({"role": "user", "content": [{"text": contextualized_message}]})

    try:
        response = bedrock.converse(
            modelId=MODEL_ID,
            system=[{"text": system_prompt}],
            messages=messages,
            inferenceConfig={
                "maxTokens": 256,
                "temperature": 0.7
            }
        )

        return response["output"]["message"]["content"][0]["text"].strip()

    except ClientError as e:
        logger.error(f"[Bedrock error] {e}")
        return "sksksksksks, something is wrong with me and I cant think of something to say :("

    except Exception as e:
        logger.error(f"[Unexpected error] {e}")
        return "whoops, something went wrong on my end"
