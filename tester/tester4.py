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

# Initialize the second OpenRouter API client for advice and rizz modes
client2 = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY2,
)

# Dictionary to track chat modes per chat ("analysis", "advice", or "rizz")
chat_modes = {}
# Dictionary to maintain conversation context for advice mode per chat
advice_context = {}
# Dictionary to maintain conversation context for rizz mode per chat
rizz_context = {}

def convert_bold_markdown_to_html(text: str) -> str:
    """
    Converts markdown bold markers **text** in the input to HTML <b>text</b>.
    Only text between ** and ** is replaced.
    """
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

async def send_html_message(update: Update, text: str) -> None:
    """
    Converts text from markdown bold to HTML bold and sends the reply with HTML parse mode.
    """
    formatted_text = convert_bold_markdown_to_html(text)
    print(formatted_text)
    await update.message.reply_text(formatted_text, parse_mode="HTML")

async def send_normal_message(update: Update, text: str) -> None:
    """
    Converts text from markdown bold to HTML bold and sends the reply with HTML parse mode.
    """
    # formatted_text = convert_bold_markdown_to_html(text)
    # print(formatted_text)
    await update.message.reply_text(text)

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
            advice_context[chat_id].append({"role": "assistant", "content": advice})
            return advice
        except Exception as e:
            logger.error("Advice Attempt %d: Error during perform_advice: %s", attempt+1, e)
    return None

def perform_rizz(chat_id: int, message: str) -> str:
    """
    Maintains conversation context for rizz mode.
    Appends the new message to the chat's rizz context and calls the OpenRouter API
    to get a flirtatious reply.
    The system prompt is adjusted so that replies are genuine, short, and like texting a real person.
    Retries up to 3 times if a placeholder response is returned.
    """
    max_attempts = 3
    if chat_id not in rizz_context:
        rizz_context[chat_id] = [
            {
                "role": "system",
                "content": (
                    "You are a smooth, charismatic, and genuine conversationalist. "
                    "Reply as if you're texting a real person: short, natural, and flirtatious. "
                    "Keep your responses friendly and believable, without overdoing it."
                    "You can also respond with smooth and casual jokes or pick-up lines."
                    "Sound more flirtatious if possible, with a slight hint of innuendous"
                    "Example responses to 'hey baby i am bored' can be 'Whats up babygirl?'' or 'U alone tonight?'"
                    "responses to 'hello' can be similar to 'hey bby whatsup <3' or 'hi angel' or 'did u fall from heaven?'"
                    "what is most important is conversation resumption, phrase the message in a way that allows the user to easier reply to the sent message"
                    "always include things like 'how about you?' or 'what was it?' in order to allow user to reply"
                    "Keep responses short and concise, include things like shorthand acronyms and emojis"
                     "ILY / ILU - I Love You"
                    "ILYSM - I Love You So Much"
                    "XOXO - Hugs and Kisses"
                    "WYD - What Are You Doing?"
                    "LMIRL - Let's Meet In Real Life"
                    "TTYL - Talk To You Later"
                    "CU - See You (or CU later)"
                    "DM - Direct Message (often used as 'slide into my DMs')"
                    #"emoji replacements include:"
                    "<3"    # Heart
                    ":*"    # Kiss
                    "xoxo"  # Hugs and kisses
                    ";)"    # Wink
                    ":-P"   # Playful tongue out
                    "^^"    # Happy eyes/smile
                    "<33"    # Extra love
                    "never use emojis at the start of a message"

                )
            }
        ]
    rizz_context[chat_id].append({"role": "user", "content": message})
    
    for attempt in range(max_attempts):
        print(f"\nRizz Attempt {attempt+1} for chat {chat_id} with input: {message}\n")
        try:
            response = client2.chat.completions.create(
                model=MODEL2,
                messages=rizz_context[chat_id]
            )
            # print(response)
            rizz_reply = response.choices[0].message.content
            print(rizz_reply)
            if "<tool_response>" in rizz_reply:
                logger.error("Rizz Attempt %d: Received placeholder response", attempt+1)
                continue
            rizz_context[chat_id].append({"role": "assistant", "content": rizz_reply})
            return rizz_reply
        except Exception as e:
            logger.error("Rizz Attempt %d: Error during perform_rizz: %s", attempt+1, e)
    return None

async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE, sentence: str) -> None:
    """
    Runs sentiment analysis in an executor and sends the result back to the user.
    """
    await send_html_message(update, "processing...")
    loop = asyncio.get_running_loop()
    analysis = await loop.run_in_executor(None, perform_analysis, sentence)
    if analysis is None:
        await send_html_message(update, "Sorry, an error occurred during sentiment analysis. Please try again later.")
    else:
        await send_html_message(update, f"Sentiment Analysis:\n{analysis}")

async def advice_message(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str) -> None:
    """
    Runs the dating advice request (with conversation continuity) in an executor and sends the result back to the user.
    """
    await send_html_message(update, "processing advice...")
    loop = asyncio.get_running_loop()
    chat_id = update.message.chat_id
    advice = await loop.run_in_executor(None, perform_advice, chat_id, question)
    if advice is None:
        await send_html_message(update, "Sorry, an error occurred while seeking dating advice. Please try again later.")
    else:
        await send_html_message(update, advice)

async def rizz_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
    """
    Runs the flirtatious (rizz mode) reply in an executor and sends the result back to the user.
    """
    loop = asyncio.get_running_loop()
    chat_id = update.message.chat_id
    rizz_reply = await loop.run_in_executor(None, perform_rizz, chat_id, message)
    if rizz_reply is None:
        await send_normal_message(update, "Sorry, an error occurred while processing your rizz. Please try again later.")
    else:
        await send_normal_message(update, rizz_reply)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Switches the chat to advice mode, clears any advice or rizz context, and sends a welcome message.
    """
    chat_id = update.message.chat_id
    chat_modes[chat_id] = "advice"
    if chat_id in advice_context:
        del advice_context[chat_id]
    if chat_id in rizz_context:
        del rizz_context[chat_id]
    await send_html_message(update, 
        "Welcome..."
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes the /sentiment command, switching the chat to sentiment analysis mode.
    """
    chat_id = update.message.chat_id
    chat_modes[chat_id] = "analysis"
    if chat_id in advice_context:
        del advice_context[chat_id]
    if chat_id in rizz_context:
        del rizz_context[chat_id]
    sentence = " ".join(context.args)
    if not sentence:
        await send_html_message(update, "Please provide a message after the /sentiment command")
        return
    await analyze_message(update, context, sentence)

async def advice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes the /advice command, switching the chat to dating advice mode.
    If a question is provided immediately, it will answer that; otherwise, the chat remains in advice mode.
    """
    chat_id = update.message.chat_id
    chat_modes[chat_id] = "advice"
    if chat_id in rizz_context:
        del rizz_context[chat_id]
    question = " ".join(context.args)
    if question:
        await advice_message(update, context, question)
    else:
        await send_html_message(update, "Now in advice mode. Please send your dating questions or advice requests.")

async def rizz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes the /rizz command, switching the chat to rizz mode.
    If a message is provided immediately, it will reply flirtatiously; otherwise, the chat remains in rizz mode.
    """
    chat_id = update.message.chat_id
    chat_modes[chat_id] = "rizz"
    if chat_id in advice_context:
        del advice_context[chat_id]
    if chat_id in rizz_context:
        del rizz_context[chat_id]
    message = " ".join(context.args)
    if message:
        await rizz_message(update, context, message)
    else:
        await send_html_message(update, "Now in rizz mode. Please send your messages for flirtatious replies.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles all text messages for active chats according to the current mode.
    """
    chat_id = update.message.chat_id
    if chat_id not in chat_modes:
        return
    sentence = update.message.text
    mode = chat_modes.get(chat_id, "analysis")
    if mode == "advice":
        await advice_message(update, context, sentence)
    elif mode == "rizz":
        await rizz_message(update, context, sentence)
    else:
        await analyze_message(update, context, sentence)

def main() -> None:
    """Start the bot."""
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sentiment", analyze_command))
    app.add_handler(CommandHandler("advice", advice_command))
    app.add_handler(CommandHandler("rizz", rizz_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
