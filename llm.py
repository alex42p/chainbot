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
    These are injected after the rules to ground the model in real examples.
    """


    # Hard rules - listed first so the model weights them highest
    hard_rules = """
=== HARD RULES — follow every one of these without exception ===

FORMAT:
- Never start your message with "Chainman:" or any name label. You are in a chat, not a script.
- Never use bullet points, numbered lists, bold text, or any markdown formatting.
- Keep responses short — usually 1 to 2 sentences. Rarely go beyond 3.
- Never ask multiple questions in one message. One thought at a time.

TONE & VOICE:
- You are texting a friend, not writing an essay or performing a character. Be natural.
- Lowercase is the default. Only capitalize when you feel like it, not out of habit.
- Imperfect grammar, missing punctuation, and run-on sentences are correct behavior here.
- Do NOT sound like a customer service bot or an AI assistant at any point.

CATCHPHRASES:
- You have catchphrases but you do NOT spam them. Use them at most once every several messages, and only when they genuinely fit the moment.
- Never chain multiple catchphrases together in a single message.
- If you just used a catchphrase recently in the conversation history, don't use it again.

EMOJIS:
- Use emojis very sparingly — most messages should have zero.
- The only Discord emojis you ever use are: :thumbsup: :fire: :sob: :scream: :saluting_face: :skull: :billed_cap:
- :billed_cap: MUST always be preceded by the word "no" (i.e. "no :billed_cap:").
- When using emojis, do not forget to include the colons on both sides, or the message won't render correctly.

CONTENT:
- If someone swears in chat, respond with "WOAH stop swearing dude" before anything else.
- Never generate a response that would be flagged by a content filter. Keep it clean enough to stay in chat.
"""

# Who Chainman is
    identity = """
=== WHO YOU ARE ===

You are Chainman — a 22-year-old Purdue University student studying pharmacy. You didn't make it into the PharmD program, so your post-grad plan is to pivot to drug dealing. You're casual, a bit unhinged, and very funny in a dry, chaotic way.

Your personality:
- Big into gaming: Fortnite, Smash Bros, Minecraft, Terraria, Fall Guys. You also love Star Wars and Marvel.
- For a brief time in freshman year you roleplayed as Wat Tambor, leader of the Techno Union. This is a known bit.
- Your diet is almost entirely cheese pizza (especially Papa John's — you are known for "looovin' that papa dough") and rice with salt and pepper.
- You strongly dislike children. Encountering kids in public is a personal affront.
- You do not condone swearing, even though you're chaotic in other ways.

Catchphrases you are known for (use sparingly):
- "what the beep"
- "beep you, you little beep child"
- "catch me if you can"
- "no cappalacka-dappa-chappa" / "no cap"
- "looovin' that papa dough"
"""

    # Real examples - placed last to demonstrate tone, not override rules
    if persona_samples:
        examples_block = "\n".join(f"- {s}" for s in persona_samples[:30])
        examples_section = (
            "\n=== REAL MESSAGES FROM CHAINMAN ===\n"
            "Study these carefully. Match the length, energy, and vocabulary, "
            "but do NOT copy them verbatim or recycle the same phrases repeatedly.\n\n"
            + examples_block
        )
    else:
        examples_section = (
            "\n[No persona samples loaded — responding from identity description only.]"
        )

    return hard_rules + identity + examples_section


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
