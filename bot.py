import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_services import AIService
from database import Database
import re

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Initialize services
ai_service = AIService()
db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_message = (
        f"👋 Hi {user.first_name}!\n\n"
        "I'm your Food Tracker Bot. I can help you analyze your food and track your nutrition.\n\n"
        "Here's what I can do:\n"
        "📸 Send me a photo of your food for analysis\n"
        "📝 Type a description of your food\n"
        "📊 Use /stats to see your nutrition statistics\n"
        "📜 Use /history to see your recent food entries\n"
        "❓ Use /help for more information"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 Food Tracker Bot Help\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/stats - Show your nutrition statistics\n"
        "/history - Show your recent food entries\n"
        "/delete - Delete a food entry\n\n"
        "Features:\n"
        "• Send photos of food for analysis\n"
        "• Type food descriptions for analysis\n"
        "• Track your nutrition history\n"
        "• View your nutrition statistics"
    )
    await update.message.reply_text(help_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's nutrition statistics."""
    user_id = update.effective_user.id
    stats = db.get_user_stats(user_id)
    
    if stats['total_entries'] == 0:
        await update.message.reply_text("You haven't tracked any food yet. Send me a photo or description to get started!")
        return
    
    stats_message = (
        "📊 Your Nutrition Statistics\n\n"
        f"Total Entries: {stats['total_entries']}\n\n"
        "📈 Totals:\n"
        f"Calories: {stats['total_calories']} kcal\n"
        f"Protein: {stats['total_protein']}g\n"
        f"Carbs: {stats['total_carbs']}g\n"
        f"Fats: {stats['total_fats']}g\n\n"
        "📊 Averages (per entry):\n"
        f"Calories: {stats['avg_calories']} kcal\n"
        f"Protein: {stats['avg_protein']}g\n"
        f"Carbs: {stats['avg_carbs']}g\n"
        f"Fats: {stats['avg_fats']}g"
    )
    await update.message.reply_text(stats_message)

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's recent food history."""
    user_id = update.effective_user.id
    history = db.get_user_history(user_id)
    
    if not history:
        await update.message.reply_text("You haven't tracked any food yet. Send me a photo or description to get started!")
        return
    
    history_message = "📜 Your Recent Food History\n\n"
    for entry in history:
        history_message += (
            f"ID: {entry['id']}\n"
            f"🍽 {entry['description']}\n"
            f"Calories: {entry['calories']} kcal\n"
            f"Protein: {entry['protein']}g | Carbs: {entry['carbs']}g | Fats: {entry['fats']}g\n"
            f"Date: {entry['created_at']}\n\n"
        )
    
    history_message += "\nTo delete an entry, use /delete <ID>"
    await update.message.reply_text(history_message)

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a food entry."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Please provide an entry ID to delete.\n"
            "Example: /delete 123\n\n"
            "Use /history to see your entries with their IDs."
        )
        return
    
    try:
        entry_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a valid entry ID (a number).")
        return
    
    # Get the entry first to show what's being deleted
    entry = db.get_entry(user_id, entry_id)
    if not entry:
        await update.message.reply_text("Entry not found. Please check the ID and try again.")
        return
    
    # Delete the entry
    if db.delete_entry(user_id, entry_id):
        await update.message.reply_text(
            f"✅ Entry deleted successfully:\n\n"
            f"ID: {entry['id']}\n"
            f"🍽 {entry['description']}\n"
            f"Calories: {entry['calories']} kcal\n"
            f"Protein: {entry['protein']}g | Carbs: {entry['carbs']}g | Fats: {entry['fats']}g\n"
            f"Date: {entry['created_at']}"
        )
    else:
        await update.message.reply_text("❌ Failed to delete the entry. Please try again.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle food photos."""
    user_id = update.effective_user.id
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    photo = update.message.photo[-1]  # Get the largest photo
    
    # Download the photo
    photo_file = await context.bot.get_file(photo.file_id)
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Analyze the photo
    result = await ai_service.get_image_analysis(photo_bytes)
    
    if "error" in result:
        await update.message.reply_text(f"❌ Sorry, I couldn't analyze your food photo. {result['error']}")
        return
    
    # Save to database
    db.add_food_entry(user_id, result)
    
    # Format the response
    response = (
        f"🍽 {result['description']}\n\n"
        f"📊 Nutrition Facts:\n"
        f"Calories: {result['calories']} kcal\n"
        f"Protein: {result['protein']}g\n"
        f"Carbs: {result['carbs']}g\n"
        f"Fats: {result['fats']}g\n\n"
        f"💡 Analysis:\n{result['analysis']}"
    )
    
    await update.message.reply_text(response)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    user_id = update.effective_user.id
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    text = update.message.text

    # Prompt length check
    if len(text) > 1000:
        await update.message.reply_text("⚠️ Your message is quite long and may not be processed correctly. Please try to shorten it or split it into multiple messages.")
        return

    # Preprocess text: flatten multiple line breaks, standardize bullet points, remove excessive whitespace
    text = re.sub(r'\n+', '\n', text)  # Replace multiple line breaks with one
    text = re.sub(r'^\s*-\s*', '', text, flags=re.MULTILINE)  # Remove leading dashes/bullets
    text = re.sub(r'\s+', ' ', text)  # Collapse excessive whitespace
    text = text.strip()

    # Analyze the text
    result = await ai_service.get_combined_analysis(text)
    
    if "error" in result:
        error_msg = result["error"]
        raw_response = result.get("raw_response")
        if raw_response:
            await update.message.reply_text(f"❌ Sorry, I couldn't analyze your food description. {error_msg}\n\nClaude raw response:\n{raw_response}")
        else:
            await update.message.reply_text(f"❌ Sorry, I couldn't analyze your food description. {error_msg}")
        return
    
    # Save to database
    db.add_food_entry(user_id, result)
    
    # Format the response
    response = (
        f"🍽 {text}\n\n"
        f"📊 Nutrition Facts:\n"
        f"Calories: {result['calories']} kcal\n"
        f"Protein: {result['protein']}g\n"
        f"Carbs: {result['carbs']}g\n"
        f"Fats: {result['fats']}g\n\n"
        f"💡 Analysis:\n{result['analysis']}"
    )
    
    await update.message.reply_text(response)

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main() 