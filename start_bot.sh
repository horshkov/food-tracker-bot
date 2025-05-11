#!/bin/bash

# Change to the bot directory
cd /Users/DimaH/food_tracker_bot

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export TELEGRAM_BOT_TOKEN="7612267395:AAEl7pqSXjZWrt1SdFxhCjmz5Q1VDmK1PXQ"
export ANTHROPIC_API_KEY="REMOVED"

# Run the bot
python bot.py 