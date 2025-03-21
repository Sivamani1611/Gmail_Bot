# Telegram Bot with Gemini API & OAuth Authentication

This repository contains a Telegram bot that integrates with the Gemini API and uses OAuth authentication for secure access. The bot allows users to interact with the Gemini AI model through Telegram while ensuring secure API calls.

## Features
- Secure OAuth authentication to access Gemini API.
- Telegram bot for user interaction.
- Handles API requests efficiently with proper error handling.

## Repository Structure
```
📂 Telegram-Gemini-Bot
├── main.py  # Main Telegram bot script
├── config.py  # Configuration file with API keys
├── requirements.txt  # Python dependencies
├── README.md  # Documentation
└── .env  # Environment variables (not included in repo)
```

## Prerequisites
Ensure you have the following before proceeding:
- A **Google Cloud Project** with OAuth credentials.
- A **Gemini API key**.
- A **Telegram bot** created via BotFather.

## Setup Instructions

### 1. Setting Up OAuth Credentials
To create OAuth credentials in Google Cloud:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Navigate to **APIs & Services** > **Credentials**.
4. Click **Create Credentials** > **OAuth Client ID**.
5. Choose **Web Application** and configure the redirect URIs.
6. Download the credentials JSON file and store it securely.
7. Update the `config.py` file with OAuth details.

### 2. Obtaining the Gemini API Key
1. Sign up at the [Gemini AI Developer Portal](https://geminiapi.com/).
2. Generate an API key.
3. Add the key to your `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   ```

### 3. Creating a Telegram Bot
1. Open Telegram and search for **BotFather**.
2. Send `/newbot` and follow the instructions.
3. Copy the **bot token** provided by BotFather.
4. Add the token to your `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token
   ```

### 4. Installing Dependencies
Install required dependencies using:
```bash
pip install -r requirements.txt
```

### 5. Running the Bot
Start the bot with:
```bash
python main.py
```

## Usage
- Send a message to your Telegram bot.
- The bot processes the request and fetches responses from Gemini API.
- Secure OAuth ensures authenticated API calls.

## Contributing
Contributions are welcome! Feel free to fork, enhance, and submit pull requests.
