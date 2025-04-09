import os
import time
import logging
import asyncio  # Import asyncio to get the running loop
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from openai import OpenAI  # Using the OpenAI client with OpenRouter configuration
from dotenv import load_dotenv, find_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Retrieve tokens from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_KEY2 = os.getenv("OPENROUTER_API_KEY2")
MODEL = os.getenv("MODEL")
MODEL2 = os.getenv("MODEL2")

if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY:
    logger.error("Please set TELEGRAM_TOKEN and OPENROUTER_API_KEY environment variables")
    exit(1)

# Initialize the OpenRouter API client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Dictionary to track the last analysis time per chat (for 10s delay)
last_analysis_time = {}
# Set of active chat IDs (those that have sent /start or /analyze)
active_chats = set()

def perform_analysis(sentence: str) -> str:
    """
    Calls the OpenRouter API to perform sentiment analysis on the provided sentence.
    Returns the analysis text, or None if an error occurs or a placeholder is returned.
    """
    print(f"\nInput: {sentence}\n")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful sentiment analysis assistant. For the given sentence, "
                        "provide a concise analysis of its sentiment: state whether it is positive, negative, or neutral, "
                        "and include a sentiment score from -10 (very negative) to 10 (very positive)."
                    )
                },
                {"role": "user", "content": f"Sentence: {sentence}"}
            ]
        )
        print(response)
        analysis = response.choices[0].message.content
        # Check for placeholder response
        placeholder = (
            "Sentiment Analysis:\n<tool_response>\n<tool_response>\n<tool_response>\n"
            "<tool_response>\n<tool_response>\n<tool_response>"
        )
        if analysis.strip() == placeholder:
            logger.error("Received placeholder response from the API")
            return None
        return analysis
    except Exception as e:
        logger.error(f"Error during perform_analysis: {e}")
        return None

async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE, sentence: str) -> None:
    """
    Runs the analysis in an executor and sends the result back to the user.
    """
    loop = asyncio.get_running_loop()
    analysis = await loop.run_in_executor(None, perform_analysis, sentence)
    if analysis is None:
        await update.message.reply_text("Sorry, an error occurred during sentiment analysis. Please try again later.")
    else:
        await update.message.reply_text(f"Sentiment Analysis:\n{analysis}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Marks the chat as active and sends a welcome message.
    """
    chat_id = update.message.chat_id
    active_chats.add(chat_id)
    # Allow immediate processing for the first message
    last_analysis_time[chat_id] = time.time() - 5
    await update.message.reply_text(
        "Hi! Your messages will now be analyzed for sentiment. "
        "Send any text and I'll provide an analysis (with at least a 5-second interval between analyses)."
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes the /analyze command and marks the chat as active.
    """
    chat_id = update.message.chat_id
    active_chats.add(chat_id)
    last_analysis_time[chat_id] = time.time() - 5

    sentence = " ".join(context.args)
    if not sentence:
        await update.message.reply_text("Please provide a sentence after the /analyze command.")
        return
    await analyze_message(update, context, sentence)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles all text messages for active chats, enforcing a 5-second delay between analyses.
    """
    chat_id = update.message.chat_id
    if chat_id not in active_chats:
        return

    current_time = time.time()
    last_time = last_analysis_time.get(chat_id, 0)
    if current_time - last_time < 5:
        await update.message.reply_text("Please wait 5 seconds between analyses.")
        return

    last_analysis_time[chat_id] = current_time
    sentence = update.message.text
    await analyze_message(update, context, sentence)

def main() -> None:
    """Start the bot."""
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
