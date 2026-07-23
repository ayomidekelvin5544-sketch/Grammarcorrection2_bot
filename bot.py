import os
import logging
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN set in environment variables")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Simple Grammar Checker (No heavy downloads) ---
class SimpleGrammarChecker:
    def __init__(self):
        # Common grammar mistakes and corrections
        self.common_mistakes = {
            r'\b(a|\b)(?=\s*[aeiou])': 'an',  # 'a apple' -> 'an apple'
            r'\b(an)(?=\s*[^aeiou])': 'a',    # 'an cat' -> 'a cat'
            r'\b(their|there)\b': 'their',    # Basic suggestions
            r'\b(your|you\'re)\b': 'your',
            r'\b(its|it\'s)\b': 'its',
            r'\b(where|were|we\'re)\b': 'where',
        }
        
        # Common misspellings (simple dictionary)
        self.spelling_corrections = {
            'teh': 'the',
            'adn': 'and',
            'thier': 'their',
            'recieve': 'receive',
            'belive': 'believe',
            'acheive': 'achieve',
            'definately': 'definitely',
            'seperate': 'separate',
            'occured': 'occurred',
            'occuring': 'occurring',
            'writting': 'writing',
            'untill': 'until',
            'alot': 'a lot',
            'infomation': 'information',
            'accomodate': 'accommodate',
            'embarass': 'embarrass',
            'neccessary': 'necessary',
            'priviledge': 'privilege',
            'pubic': 'public',
            'suprise': 'surprise',
            'truely': 'truly',
            'untill': 'until',
            'usally': 'usually',
        }
        
        # Common punctuation fixes
        self.punctuation_patterns = [
            (r'\s+\.', '.'),  # Remove space before period
            (r'\s+,', ','),   # Remove space before comma
            (r'\s+\?', '?'),  # Remove space before question mark
            (r'\s+\!', '!'),  # Remove space before exclamation
            (r'\s+\:', ':'),  # Remove space before colon
            (r'\s+\;', ';'),  # Remove space before semicolon
        ]
        
        # Contractions expansion
        self.contractions = {
            "don't": "do not",
            "can't": "cannot",
            "won't": "will not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "couldn't": "could not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "doesn't": "does not",
            "didn't": "did not",
            "i'm": "i am",
            "you're": "you are",
            "he's": "he is",
            "she's": "she is",
            "it's": "it is",
            "we're": "we are",
            "they're": "they are",
            "i've": "i have",
            "you've": "you have",
            "we've": "we have",
            "they've": "they have",
            "i'll": "i will",
            "you'll": "you will",
            "he'll": "he will",
            "she'll": "she will",
            "we'll": "we will",
            "they'll": "they will",
            "i'd": "i would",
            "you'd": "you would",
            "he'd": "he would",
            "she'd": "she would",
            "we'd": "we would",
            "they'd": "they would",
        }
    
    def correct_text(self, text):
        """Correct grammar and spelling in the given text"""
        if not text:
            return text
        
        original = text
        corrected = text.lower()
        
        # 1. Fix common spelling mistakes
        for wrong, correct in self.spelling_corrections.items():
            # Word boundary matching
            pattern = r'\b' + wrong + r'\b'
            corrected = re.sub(pattern, correct, corrected, flags=re.IGNORECASE)
        
        # 2. Fix article usage (a/an)
        for pattern, replacement in self.common_mistakes.items():
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        # 3. Fix punctuation spacing
        for pattern, replacement in self.punctuation_patterns:
            corrected = re.sub(pattern, replacement, corrected)
        
        # 4. Expand common contractions (optional - makes text more formal)
        for contraction, expansion in self.contractions.items():
            corrected = corrected.replace(contraction, expansion)
        
        # 5. Capitalize first letter of sentences
        sentences = re.split(r'([.!?])\s*', corrected)
        corrected = ''
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sent = sentences[i]
                if sent:
                    sent = sent.capitalize()
                    corrected += sent
                if i + 1 < len(sentences):
                    corrected += sentences[i + 1] + ' '
        
        # 6. Clean up extra spaces
        corrected = re.sub(r'\s+', ' ', corrected).strip()
        
        # If no changes were made, return original
        if corrected == original.lower():
            return None
        
        return corrected

# Initialize the checker
checker = SimpleGrammarChecker()

# --- Bot Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_message = (
        f"👋 Hello {user.first_name}!\n\n"
        "I'm a Grammar Correction Bot. Send me any text, and I'll try to correct its grammar and spelling.\n\n"
        "📝 I can fix:\n"
        "• Spelling mistakes\n"
        "• Grammar errors\n"
        "• Punctuation\n"
        "• Article usage (a/an)\n\n"
        "🔧 Use the buttons below for quick actions:"
    )
    keyboard = [
        [KeyboardButton("📝 Correct my last message"), KeyboardButton("ℹ️ Help")],
        [KeyboardButton("🔄 Reset")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🤖 *Grammar Correction Bot Help*\n\n"
        "• Simply type or paste any text and I'll correct it.\n"
        "• I can fix:\n"
        "  - Common spelling mistakes\n"
        "  - Grammar errors (a/an, contractions, etc.)\n"
        "  - Punctuation issues\n"
        "  - Sentence capitalization\n\n"
        "• Use the buttons below:\n"
        "  - '📝 Correct my last message' → Correct your previous text\n"
        "  - 'ℹ️ Help' → Show this help\n"
        "  - '🔄 Reset' → Clear conversation\n\n"
        "Send /start to see the menu again."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text("🔄 Conversation reset. You can start over!")

async def correct_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    
    if user_message.startswith('/'):
        return
    
    await update.message.chat.send_action(action="typing")
    
    try:
        corrected = checker.correct_text(user_message)
        
        if corrected:
            response = f"✍️ *Corrected version:*\n\n{corrected}"
        else:
            response = "✅ Your text looks great! No corrections needed."
        
        await update.message.reply_text(response, parse_mode="Markdown")
        context.user_data['last_message'] = user_message
        context.user_data['last_correction'] = corrected

    except Exception as e:
        logger.error(f"Error during correction: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def handle_last_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = context.user_data.get('last_message')
    if not last_message:
        await update.message.reply_text("🤔 I don't have a previous message. Send me a text first!")
        return
    
    update.message.text = last_message
    await correct_text(update, context)

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.Text("📝 Correct my last message"), handle_last_message))
    application.add_handler(MessageHandler(filters.Text("ℹ️ Help"), help_command))
    application.add_handler(MessageHandler(filters.Text("🔄 Reset"), reset))
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.Text(["📝 Correct my last message", "ℹ️ Help", "🔄 Reset"]),
            correct_text
        )
    )
    
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
