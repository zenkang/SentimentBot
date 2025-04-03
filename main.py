import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
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
if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY:
    logger.error("Please set TELEGRAM_TOKEN and OPENROUTER_API_KEY environment variables")
    exit(1)

# Initialize the OpenRouter API client without optional parameters
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Hi! Send me a sentence using the /analyze command followed by your sentence, "
        "and I'll perform sentiment analysis on it."
    )

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the /analyze command by sending the sentence to OpenRouter's API for sentiment analysis."""
    sentence = " ".join(context.args)
    if not sentence:
        await update.message.reply_text("Please provide a sentence after the /analyze command.")
        return

    try:
        # Call OpenRouter's chat completion API for sentiment analysis
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
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
        analysis = response.choices[0].message.content
        await update.message.reply_text(f"Sentiment Analysis:\n{analysis}")
    except Exception as e:
        logger.error(f"Error during sentiment analysis: {e}")
        await update.message.reply_text("Sorry, an error occurred while processing your request.")

def main() -> None:
    """Start the bot."""
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))

    app.run_polling()

if __name__ == '__main__':
    main()
