import os
import re
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Retrieve tokens and model identifiers from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_KEY2 = os.getenv("OPENROUTER_API_KEY2")
MODEL = os.getenv("MODEL")
MODEL2 = os.getenv("MODEL2")

if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY or not OPENROUTER_API_KEY2:
    logger.error("Please set TELEGRAM_TOKEN, OPENROUTER_API_KEY and OPENROUTER_API_KEY2 environment variables")
    exit(1)

# Initialize the first OpenRouter API client for sentiment analysis
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Initialize the second OpenRouter API client for dating advice
client2 = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY2,
)

# Dictionary to track the last response time per chat (for 5s delay)
last_response_time = {}
# Dictionary to track chat modes per chat ("analysis" or "advice")
chat_modes = {}

def perform_analysis(sentence: str) -> str:
    """
    Calls the OpenRouter API to perform sentiment analysis on the provided sentence.
    Retries up to 3 times if a placeholder response is returned.
    """
    max_attempts = 3
    for attempt in range(max_attempts):
        print(f"\nAttempt {attempt+1} for input: {sentence}\n")
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
            if "<tool_response>" in analysis:
                logger.error("Attempt %d: Received placeholder response", attempt+1)
                continue
            return analysis
        except Exception as e:
            logger.error("Attempt %d: Error during perform_analysis: %s", attempt+1, e)
    return None

def perform_advice(question: str) -> str:
    """
    Calls the OpenRouter API to provide dating advice for the given question.
    Retries up to 3 times if a placeholder response is returned.
    """
    max_attempts = 3
    for attempt in range(max_attempts):
        print(f"\nAdvice Attempt {attempt+1} for input: {question}\n")
        try:
            response = client2.chat.completions.create(
                model=MODEL2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a knowledgeable and supportive dating coach. "
                            "Provide advice and answer questions related to dating, relationships, and personal development. "
                            "Keep your responses friendly, encouraging, and clear."
                        )
                    },
                    {"role": "user", "content": f"Question: {question}"}
                ]
            )
            print(response)
            advice = response.choices[0].message.content
            if "<tool_response>" in advice:
                logger.error("Advice Attempt %d: Received placeholder response", attempt+1)
                continue
            return advice
        except Exception as e:
            logger.error("Advice Attempt %d: Error during perform_advice: %s", attempt+1, e)
    return None

async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE, sentence: str) -> None:
    """
    Runs sentiment analysis in an executor and sends the result back to the user.
    """
    await update.message.reply_text("processing...")
    loop = asyncio.get_running_loop()
    analysis = await loop.run_in_executor(None, perform_analysis, sentence)
    if analysis is None:
        await update.message.reply_text("Sorry, an error occurred during sentiment analysis. Please try again later.")
    else:
        await update.message.reply_text(f"Sentiment Analysis:\n{analysis}")

async def advice_message(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str) -> None:
    """
    Runs the dating advice request in an executor and sends the result back to the user.
    """
    await update.message.reply_text("processing advice...")
    loop = asyncio.get_running_loop()
    advice = await loop.run_in_executor(None, perform_advice, question)
    if advice is None:
        await update.message.reply_text("Sorry, an error occurred while seeking dating advice. Please try again later.")
    else:
        await update.message.reply_text(f"Dating Advice:\n{advice}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Switches the chat to sentiment analysis mode and sends a welcome message.
    """
    chat_id = update.message.chat_id
    chat_modes[chat_id] = "analysis"
    last_response_time[chat_id] = time.time() - 5
    await update.message.reply_text(
        "Hi! Your messages will now be analyzed for sentiment. "
        "Send any text and I'll provide an analysis (with at least a 5-second interval between responses)."
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes the /analyze command, switching the chat to sentiment analysis mode.
    """
    chat_id = update.message.chat_id
    chat_modes[chat_id] = "analysis"
    last_response_time[chat_id] = time.time() - 5

    sentence = " ".join(context.args)
    if not sentence:
        await update.message.reply_text("Please provide a sentence after the /analyze command.")
        return
    await analyze_message(update, context, sentence)

async def advice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes the /advice command, switching the chat to dating advice mode.
    If a question is provided immediately, it will answer that. Otherwise, it stays in advice mode for subsequent messages.
    """
    chat_id = update.message.chat_id
    chat_modes[chat_id] = "advice"
    last_response_time[chat_id] = time.time() - 5

    question = " ".join(context.args)
    if question:
        await advice_message(update, context, question)
    else:
        await update.message.reply_text("Now in advice mode. Please send your dating questions or advice requests.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles all text messages for active chats according to the current mode,
    enforcing a 5-second delay between responses.
    """
    chat_id = update.message.chat_id
    if chat_id not in chat_modes:
        return

    current_time = time.time()
    last_time = last_response_time.get(chat_id, 0)
    if current_time - last_time < 5:
        await update.message.reply_text("Please wait 5 seconds between responses.")
        return

    last_response_time[chat_id] = current_time
    sentence = update.message.text
    mode = chat_modes.get(chat_id, "analysis")
    if mode == "advice":
        await advice_message(update, context, sentence)
    else:
        await analyze_message(update, context, sentence)

def main() -> None:
    """Start the bot."""
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("advice", advice_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
