<div align="center">

# Lora Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**Enterprise-grade AI-powered Telegram bot built with Lora Technologies API**

[Features](#features) • [Installation](#installation) • [Configuration](#configuration) • [Documentation](#documentation)

</div>

---

## Overview

Lora Telegram Bot is a production-ready, scalable Telegram bot that leverages the power of Lora Technologies API to deliver intelligent conversational AI capabilities. Built with enterprise requirements in mind, it features comprehensive rate limiting, user management, structured logging, and real-time web search integration.

## Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Mention Trigger** | Responds when mentioned with `@botusername` |
| **Reply Trigger** | Continues conversation when users reply to bot messages |
| **Web Search** | Real-time DuckDuckGo search integration with source citations |
| **Conversation Memory** | Per-user, per-chat conversation history with configurable context window |

### Security & Rate Limiting

| Feature | Description |
|---------|-------------|
| **User Rate Limiting** | Configurable per-user request limits |
| **Group Rate Limiting** | Separate rate limits for group chats |
| **Cooldown System** | Automatic cooldown for spam prevention |
| **User Management** | Ban/unban functionality with admin controls |

### Monitoring & Analytics

| Feature | Description |
|---------|-------------|
| **Structured Logging** | JSON-formatted logs for easy parsing and analysis |
| **Usage Analytics** | Track messages, tokens, and search queries per user |
| **Health Checks** | System health monitoring endpoint |
| **Admin Dashboard** | Global statistics and system overview |

## Installation

### Prerequisites

- Python 3.11 or higher
- Telegram Bot Token ([Create via BotFather](https://t.me/botfather))
- Lora Technologies API Key ([Get API Key](https://loratech.dev))

### Quick Start

```bash
git clone https://github.com/your-org/lora-telegram-bot.git
cd lora-telegram-bot

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
```

### Environment Configuration

Edit the `.env` file with your credentials:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
LORA_API_KEY=your_lora_api_key
ADMIN_USER_IDS=123456789,987654321
BOT_USERNAME=your_bot_username
```

### Launch

```bash
python bot.py
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | Telegram Bot API token (required) |
| `LORA_API_KEY` | - | Lora Technologies API key (required) |
| `BOT_USERNAME` | - | Bot username without @ (required) |
| `ADMIN_USER_IDS` | - | Comma-separated admin Telegram user IDs |
| `RATE_LIMIT_USER` | `10` | Maximum requests per user per window |
| `RATE_LIMIT_GROUP` | `30` | Maximum requests per group per window |
| `RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |
| `CONTEXT_WINDOW_SIZE` | `20` | Number of messages to retain in memory |
| `MAX_TOKENS` | `4096` | Maximum tokens per AI response |
| `MODEL` | `gemini-2.5-pro` | AI model identifier |
| `LOG_LEVEL` | `INFO` | Logging verbosity level |

## Documentation

### User Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and display welcome message |
| `/help` | Show help menu with available commands |
| `/search <query>` | Perform web search and return results |
| `/clear` | Clear conversation history for current chat |
| `/stats` | Display personal usage statistics |

### Admin Commands

| Command | Description |
|---------|-------------|
| `/ban <user>` | Ban user by username or ID |
| `/unban <user>` | Remove ban from user |
| `/adminstats` | View global system statistics |
| `/health` | Check system health status |

## Architecture

```
lora-telegram-bot/
├── bot.py                      # Application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
│
├── data/                       # Runtime data (auto-generated)
│   └── bot.db                  # SQLite database
│
└── src/
    ├── database/               # Data persistence layer
    │   ├── db.py               # Database operations
    │   └── models.py           # Data models
    │
    ├── handlers/               # Request handlers
    │   ├── admin.py            # Admin command handlers
    │   ├── commands.py         # User command handlers
    │   └── message.py          # Message processing
    │
    ├── services/               # Business logic
    │   ├── ai.py               # AI/LLM integration
    │   └── search.py           # Search service
    │
    └── utils/                  # Utilities
        ├── helpers.py          # Helper functions
        ├── logger.py           # Logging configuration
        └── rate_limiter.py     # Rate limiting logic
```

## API Integration

This bot integrates with the Lora Technologies API, which is fully OpenAI-compatible.

| Property | Value |
|----------|-------|
| **Base URL** | `https://api.loratech.dev/v1` |
| **Default Model** | `gemini-2.5-pro` |
| **Protocol** | OpenAI Chat Completions API |

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ by Lora Technologies**

[Website](https://loratech.dev) • [API Documentation](https://loratech.dev/docs) • [Support](https://loratech.dev/support)

</div>
