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
# Dictionary to maintain conversation context for advice mode per chat
advice_context = {}

def convert_bold_markdown_to_html(text: str) -> str:
    """
    Converts markdown bold markers **text** in the input to HTML <b>text</b>.
    Only text between ** and ** is replaced.
    """
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

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

def perform_advice(chat_id: int, question: str) -> str:
    """
    Maintains conversation context for advice mode.
    Appends the new question to the chat's advice context and calls the OpenRouter API
    to get dating advice. Retries up to 3 times if a placeholder response is returned.
    """
    max_attempts = 3
    # Initialize conversation context for advice if not present
    if chat_id not in advice_context:
        advice_context[chat_id] = [
            {
                "role": "system",
                "content": (
                    "You are a knowledgeable and supportive dating coach. "
                    "Provide advice and answer questions related to dating, relationships, and personal development. "
                    "Keep your responses friendly, encouraging, and clear."
                )
            }
        ]
    # Append the user's new question to the conversation context
    advice_context[chat_id].append({"role": "user", "content": question})
    
    for attempt in range(max_attempts):
        print(f"\nAdvice Attempt {attempt+1} for chat {chat_id} with input: {question}\n")
        try:
            response = client2.chat.completions.create(
                model=MODEL2,
                messages=advice_context[chat_id]
            )
            print(response)
            advice = response.choices[0].message.content
            if "<tool_response>" in advice:
                logger.error("Advice Attempt %d: Received placeholder response", attempt+1)
                continue
            # Append the assistant's response to the conversation context
            advice_context[chat_id].append({"role": "assistant", "content": advice})
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
    Runs the dating advice request (with chat continuity) in an executor and sends the result back to the user.
    Converts any **text** markers to HTML bold so that only text between ** is bolded.
    """
    await update.message.reply_text("processing advice...", parse_mode="HTML")
    loop = asyncio.get_running_loop()
    chat_id = update.message.chat_id
    advice = await loop.run_in_executor(None, perform_advice, chat_id, question)
    if advice is None:
        await update.message.reply_text("Sorry, an error occurred while seeking dating advice. Please try again later.", parse_mode="HTML")
    else:
        # Convert only text between ** markers to HTML bold tags.
        formatted_advice = convert_bold_markdown_to_html(advice)
        await update.message.reply_text(formatted_advice, parse_mode="HTML")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Switches the chat to sentiment analysis mode, clears any advice context, and sends a welcome message.
    """
    chat_id = update.message.chat_id
    chat_modes[chat_id] = "analysis"
    if chat_id in advice_context:
        del advice_context[chat_id]
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
    if chat_id in advice_context:
        del advice_context[chat_id]
    last_response_time[chat_id] = time.time() - 5
    sentence = " ".join(context.args)
    if not sentence:
        await update.message.reply_text("Please provide a sentence after the /analyze command.")
        return
    await analyze_message(update, context, sentence)

async def advice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes the /advice command, switching the chat to dating advice mode.
    If a question is provided immediately, it will answer that; otherwise, the chat remains in advice mode.
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
