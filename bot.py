import discord
import logging
import os
from llm import generate_response
from persona import load_persona_samples, sample_persona_samples
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("bot")
os.makedirs("logs", exist_ok=True)
handler = logging.FileHandler("logs/messages.log", mode='w', encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

TRIGGER_KEYWORDS = [
    "battle pass",
    "bot",
    "beep",
    "catch me", # if you can
    "chain",
    "children",
    "chud",
    "fall guys",
    "fcg", 
    "fort", # nite
    "game",
    "gaming",
    "gimme that", # crown
    "no cap",
    "papa john",
    "pharm", 
    "pizza",
    "pookie",
    "rice",
    "saber",
    "skin",
    "smash",
    "star wars",
    "starwars",
    "techno union",
    "terraria",
    "what the", # beep
]

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
client = discord.Client(intents=intents)

# Load all persona samples once at startup, then sample from them per request
persona_samples = load_persona_samples("s3")
chat_history = []

def message_contains_keyword(content: str) -> bool:
    """Return True if any trigger keyword appears in the message (case-insensitive)."""
    lowered = content.lower()
    return any(keyword in lowered for keyword in TRIGGER_KEYWORDS)


@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user} ")
    logger.info(f"Loaded {len(persona_samples)} persona samples.")
    logger.info("Bot is ready and listening...")


@client.event
async def on_message(message: discord.Message):
    # Bot should not respond to itself
    if message.author == client.user:
        return

    content = message.content
    is_mention = client.user in message.mentions
    is_keyword_trigger = message_contains_keyword(content)

    if not is_mention and not is_keyword_trigger:
        return

    # Use a random subset of persona samples on every request to limit prompt size.
    sampled_persona = sample_persona_samples(persona_samples)

    # Show a typing indicator while we call the LLM.
    async with message.channel.typing():
        response = await generate_response(
            user_message=content,
            persona_samples=sampled_persona,
            author_name=message.author.display_name,
            history=chat_history
        )

    chat_history.append({"role": "user", "content": content})
    chat_history.append({"role": "assistant", "content": response})
    if len(chat_history) > 6: # add 2 msgs, pop 2 msgs
        chat_history.pop(0)
        chat_history.pop(0)

    logger.info(f"\"{response}\"")

    await message.channel.send(response)


if __name__ == "__main__":
    try:
        if not DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is not set.")
        client.run(DISCORD_TOKEN)
    except KeyboardInterrupt as e:
        logger.error(f"Killed the bot. Restarting soon...")
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")