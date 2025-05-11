# Food Tracker Bot

A Telegram bot that helps track food intake and provides nutritional analysis using AI.

## Features

- Food image analysis
- Nutritional information tracking
- Daily and weekly statistics
- AI-powered food recognition

## Deployment on Render

1. Fork this repository to your GitHub account
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Add the following environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
5. Deploy!

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your environment variables
5. Run the bot:
   ```bash
   python bot.py
   ```

## Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from @BotFather
- `ANTHROPIC_API_KEY`: Your Anthropic API key

## License

MIT 