import os
import logging
import language_tool_python
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration & Setup ---
# Load the bot token from environment variable (crucial for Railway)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN set in environment variables")

# Set up logging to see what's happening
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize the grammar correction tool (using LanguageTool)
# It downloads the required language model on the first run
logger.info("Initializing LanguageTool...")
try:
    # 'en-US' for American English. You can change to 'en-GB', etc.
    tool = language_tool_python.LanguageTool('en-US')
    logger.info("LanguageTool initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize LanguageTool: {e}")
    tool = None

# --- Helper Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and a custom keyboard when the /start command is issued."""
    user = update.effective_user
    welcome_message = (
        f"👋 Hello {user.first_name}!\n\n"
        "I'm a Grammar Correction Bot. Send me any text, and I'll try to correct its grammar and spelling.\n\n"
        "🔧 You can also use the buttons below:"
    )
    # Create a persistent reply keyboard with helpful buttons
    keyboard = [
        [KeyboardButton("📝 Correct my last message"), KeyboardButton("ℹ️ Help")],
        [KeyboardButton("🔄 Reset")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    help_text = (
        "🤖 *Grammar Correction Bot Help*\n\n"
        "• Simply type or paste any text and I'll correct it.\n"
        "• Use the buttons below for quick actions:\n"
        "  - '📝 Correct my last message' → I'll correct the last text you sent.\n"
        "  - 'ℹ️ Help' → Show this help message.\n"
        "  - '🔄 Reset' → Clears the current conversation context.\n\n"
        "Send /start to see the menu again."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset conversation context and clear any stored data."""
    context.user_data.clear()  # Clear any stored data for this user
    await update.message.reply_text("🔄 Conversation reset. You can start over!")

async def correct_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Core function: correct the grammar and spelling of the user's message."""
    if tool is None:
        await update.message.reply_text("⚠️ Sorry, the grammar correction service is currently unavailable.")
        return

    user_message = update.message.text

    # Check if the message is a command or from the custom keyboard
    # We handle these in their specific handlers, but we add a safety check here.
    if user_message.startswith('/'):
        return

    # Wait for the correction
    await update.message.chat.send_action(action="typing")
    
    try:
        # The magic happens here! LanguageTool corrects the text.
        matches = tool.check(user_message)
        corrected_text = language_tool_python.utils.correct(user_message, matches)
        
        if corrected_text == user_message:
            response = "✅ Your text looks great! No corrections needed."
        else:
            response = f"✍️ *Corrected version:*\n\n{corrected_text}"
        
        # Send the response
        await update.message.reply_text(response, parse_mode="Markdown")
        # Store the user's original message in context for potential later use
        context.user_data['last_message'] = user_message
        context.user_data['last_correction'] = corrected_text

    except Exception as e:
        logger.error(f"Error during correction: {e}")
        await update.message.reply_text("❌ An error occurred while correcting your text. Please try again.")

async def handle_last_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Correct my last message' button."""
    last_message = context.user_data.get('last_message')
    if not last_message:
        await update.message.reply_text("🤔 I don't have a previous message from you to correct. Please send me a text first!")
        return
    
    # We'll reuse the correct_text logic by simulating a text message
    update.message.text = last_message
    await correct_text(update, context)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any other text messages not caught by other handlers."""
    # This is a catch-all; we can also just ignore it, but we'll redirect to the main correct_text
    # To avoid recursion, we check if the message is already handled by a command.
    if not update.message.text.startswith('/'):
        await correct_text(update, context)

def main() -> None:
    """Start and run the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset))
    
    # Register message handlers
    # 1. For the 'Correct my last message' button using a filter on the text
    application.add_handler(MessageHandler(filters.Text("📝 Correct my last message"), handle_last_message))
    # 2. For the 'Help' button
    application.add_handler(MessageHandler(filters.Text("ℹ️ Help"), help_command))
    # 3. For the 'Reset' button
    application.add_handler(MessageHandler(filters.Text("🔄 Reset"), reset))
    
    # 4. For all other text messages (the main grammar correction logic)
    # Exclude commands and our specific button texts so they don't get caught twice.
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.Text(["📝 Correct my last message", "ℹ️ Help", "🔄 Reset"]),
            correct_text
        )
    )
    
    # Start the Bot (using long polling, which is ideal for Railway)
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
