#!/bin/bash

# Check if the tmux session exists
if ! tmux has-session -t foodbot 2>/dev/null; then
    # Create a new session named 'foodbot'
    tmux new-session -d -s foodbot
    
    # Send the commands to the session
    tmux send-keys -t foodbot "cd /Users/DimaH/food_tracker_bot" C-m
    tmux send-keys -t foodbot "source venv/bin/activate" C-m
    tmux send-keys -t foodbot "export TELEGRAM_BOT_TOKEN='7612267395:AAEl7pqSXjZWrt1SdFxhCjmz5Q1VDmK1PXQ'" C-m
    tmux send-keys -t foodbot "export ANTHROPIC_API_KEY='REMOVED'" C-m
    tmux send-keys -t foodbot "python bot.py" C-m
fi

echo "Bot is running in tmux session 'foodbot'"
echo "To view the bot's output, run: tmux attach -t foodbot"
echo "To detach from the session (leave it running), press Ctrl+B then D" 