# DateAI - Telegram Sentiment Analysis & Dating Assistant Bot 🤖💝

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-green.svg)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A sophisticated Telegram bot that combines AI-powered sentiment analysis with dating advice and flirtatious conversation capabilities. Built as part of the CC0002 project by Team 2.

**🔗 Try it now: [@DateAnalysisBot](https://t.me/DateAnalysisBot)**

## 📋 Table of Contents

- [Features](#-features)
- [Demo](#-demo)
- [Technologies Used](#-technologies-used)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Integration](#-api-integration)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

## ✨ Features

### 🎯 **Sentiment Analysis Mode**
- Real-time sentiment analysis of text messages
- Sentiment scoring from -10 (very negative) to +10 (very positive)
- Detailed emotional insights and recommendations

### 💬 **Dating Advice Mode**
- AI-powered dating coach with contextual conversation memory
- Personalized relationship advice and tips
- Continuous conversation flow with context retention

### 😏 **Rizz Mode**
- Flirtatious conversation assistant
- Natural, text-like responses with modern slang and emojis
- Engaging conversation starters and smooth replies

### 🎛️ **Interactive Interface**
- Inline keyboard menu for easy mode switching
- Command-based navigation
- Clean HTML-formatted responses

## 🎬 Demo

```
👤 User: /start
🤖 Bot: Welcome to DateAI! Choose your mode:
       [Advice] [Sentiment] [Rizz]

👤 User: How do I start a conversation with someone I like?
🤖 Bot: Great question! Start with something genuine and specific...

👤 User: /sentiment I'm feeling amazing today!
🤖 Bot: **Sentiment Analysis:**
       Positive sentiment detected! Score: 8/10
       This message radiates joy and enthusiasm...
```

## 🛠️ Technologies Used

- **Python 3.12** - Core programming language
- **python-telegram-bot** - Telegram Bot API wrapper
- **OpenAI API** - AI language model integration via OpenRouter
- **asyncio** - Asynchronous programming for concurrent operations
- **Logging** - Comprehensive error tracking and debugging

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram      │    │   DateAI Bot     │    │   OpenRouter    │
│   User Input    │───▶│   (Python)       │───▶│   API           │
│                 │    │                  │    │   (3 Models)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Context        │
                       │   Management     │
                       │   (Per Chat)     │
                       └──────────────────┘
```

### Key Components:

1. **Multi-Client Architecture**: Three separate OpenAI clients for different functionalities
2. **Context Management**: Per-chat conversation history for advice and rizz modes
3. **Async Processing**: Non-blocking message handling with executor patterns
4. **Error Handling**: Robust retry mechanisms and graceful error recovery

## 🚀 Installation

### Prerequisites
- Python 3.12 or higher
- Telegram Bot Token
- OpenRouter API Keys

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/SentimentBot.git
   cd SentimentBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API keys**
   ```bash
   # Create config.py with your API credentials
   # (This file is gitignored for security)
   touch config.py
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

⚠️ **Security Note**: The `config.py` file is gitignored to protect sensitive API keys.

Create a `config.py` file with your API credentials:

```python
# Telegram Bot Configuration
TELEGRAM_TOKEN = "your_telegram_bot_token"

# OpenRouter API Keys (3 different keys for load balancing)
OPENROUTER_API_KEY = "your_openrouter_api_key_1"
OPENROUTER_API_KEY2 = "your_openrouter_api_key_2" 
OPENROUTER_API_KEY3 = "your_openrouter_api_key_3"

# AI Models
MODEL = "deepseek/deepseek-chat-v3-0324:free"
MODEL2 = "meta-llama/llama-3.2-3b-instruct:free"
```

### Getting API Keys:

1. **Telegram Bot Token**: 
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot with `/newbot`

2. **OpenRouter API Keys**:
   - Sign up at [OpenRouter](https://openrouter.ai)
   - Generate API keys in your dashboard

## 📱 Usage

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and show welcome menu |
| `/menu` | Display inline keyboard menu |
| `/sentiment [text]` | Switch to sentiment analysis mode |
| `/advice [question]` | Switch to dating advice mode |
| `/rizz [message]` | Switch to flirtatious chat mode |

### Mode Switching

The bot operates in three distinct modes:

1. **Sentiment Mode**: Analyze emotional tone of messages
2. **Advice Mode**: Get dating and relationship guidance
3. **Rizz Mode**: Engage in flirtatious conversation

Simply send a message after selecting a mode, and the bot will respond accordingly!

## 🔗 API Integration

### OpenRouter Implementation

The bot uses OpenRouter to access multiple AI models:

- **Sentiment Analysis**: DeepSeek Chat v3 for detailed emotional analysis
- **Advice & Rizz**: Llama 3.2 3B for conversational responses

### Error Handling

- **Retry Logic**: Up to 3 attempts for failed API calls
- **Fallback Responses**: Graceful degradation when APIs are unavailable
- **Logging**: Comprehensive error tracking for debugging

## 📁 Project Structure

```
SentimentBot/
├── main.py              # Main bot application
├── config.py            # Configuration and API keys (gitignored)
├── requirements.txt     # Python dependencies
├── README.md           # Project documentation
├── .gitignore          # Git ignore file for security
├── tester/             # Test files and utilities
│   ├── first.py
│   ├── main2.py
│   ├── main3.py
│   ├── main4.py
│   ├── tester.py
│   ├── tester2.py
│   ├── tester3.py
│   └── tester4.py
└── __pycache__/        # Python cache files
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings for new functions
- Include error handling for API calls
- Test thoroughly before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Contact

**Developer**: Kang Yi, Zen -Year 1 Computer Science Student  
**Project**: CC0002 Team 2 Date AI
**Bot**: [@DateAnalysisBot](https://t.me/DateAnalysisBot)
