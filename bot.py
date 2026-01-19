import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import json
from datetime import datetime

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
BOT_TOKEN = "8541538951:AAHv51hiPSNxL3qV3RkwoxhxZVhXDRcmD-4"  # Replace with your bot token from BotFather
ADMIN_USER_ID = 5672588037  # Replace with your Telegram User ID (just the number, no quotes)
# =========================

# Conversation states
NAME, EMAIL, PHONE, DOB, OCCUPATION, MARITAL, LOCATION, MESSAGE = range(8)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask for name."""
    user = update.effective_user
    
    welcome_message = (
        f"👋 Hello {user.first_name}!\n\n"
        "Welcome to our lead collection service. I'll help you get started by gathering some information.\n\n"
        "This will only take a few moments. Let's begin!\n\n"
        "📝 *What's your full name?*"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store name and ask for email."""
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        "Great! 📧 *What's your email address?*",
        parse_mode='Markdown'
    )
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store email and ask for phone."""
    context.user_data['email'] = update.message.text
    
    # Create keyboard with phone share button
    keyboard = [[KeyboardButton("📱 Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Perfect! 📱 *What's your phone number?*\n\n"
        "You can type it or use the button below to share it automatically.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store phone and ask for date of birth."""
    if update.message.contact:
        context.user_data['phone'] = update.message.contact.phone_number
    else:
        context.user_data['phone'] = update.message.text
    
    await update.message.reply_text(
        "Got it! 🎂 *What's your date of birth?*\n\n"
        "Please use format: DD/MM/YYYY (e.g., 15/03/1990)",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    return DOB

async def dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store DOB and ask for occupation."""
    context.user_data['dob'] = update.message.text
    await update.message.reply_text(
        "Thanks! 💼 *What's your occupation/profession?*",
        parse_mode='Markdown'
    )
    return OCCUPATION

async def occupation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store occupation and ask for marital status."""
    context.user_data['occupation'] = update.message.text
    
    keyboard = [['Single', 'Married'], ['Divorced', 'Widowed'], ['Prefer not to say']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Almost there! 💑 *What's your marital status?*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MARITAL

async def marital(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store marital status and ask for location."""
    context.user_data['marital_status'] = update.message.text
    
    keyboard = [[KeyboardButton("📍 Share My Location", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Great! 📍 *Please share your location*\n\n"
        "Click the button below to share your current location.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store location and ask for optional message."""
    if update.message.location:
        loc = update.message.location
        context.user_data['location'] = f"Lat: {loc.latitude}, Long: {loc.longitude}"
        context.user_data['location_link'] = f"https://www.google.com/maps?q={loc.latitude},{loc.longitude}"
    else:
        context.user_data['location'] = "Not shared"
        context.user_data['location_link'] = "N/A"
    
    await update.message.reply_text(
        "Perfect! 💬 *Do you have any questions or messages for us?*\n\n"
        "Type your message, or send /skip if you don't have any.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    return MESSAGE

async def message_inquiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store message and finish."""
    context.user_data['message'] = update.message.text
    return await finish_collection(update, context)

async def skip_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip message and finish."""
    context.user_data['message'] = "No message provided"
    return await finish_collection(update, context)

async def finish_collection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect additional info and send lead to admin."""
    user = update.effective_user
    
    # Get user's group count (common groups with bot)
    try:
        common_chats = await context.bot.get_user_profile_photos(user.id)
        # Note: Telegram API doesn't directly provide group count for privacy
        # We can only get limited info about the user
        group_info = "Privacy protected - Not accessible via bot"
    except:
        group_info = "Unable to retrieve"
    
    # Prepare lead data
    lead_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'telegram_info': {
            'user_id': user.id,
            'username': user.username or 'Not set',
            'first_name': user.first_name,
            'last_name': user.last_name or 'Not provided'
        },
        'lead_info': {
            'name': context.user_data.get('name'),
            'email': context.user_data.get('email'),
            'phone': context.user_data.get('phone'),
            'dob': context.user_data.get('dob'),
            'occupation': context.user_data.get('occupation'),
            'marital_status': context.user_data.get('marital_status'),
            'location': context.user_data.get('location'),
            'location_link': context.user_data.get('location_link'),
            'message': context.user_data.get('message')
        },
        'telegram_groups': group_info
    }
    
    # Save to file (optional backup)
    try:
        with open('leads.json', 'a') as f:
            json.dump(lead_data, f)
            f.write('\n')
    except Exception as e:
        logger.error(f"Error saving lead: {e}")
    
    # Send to admin
    admin_message = (
        "🎯 *NEW LEAD COLLECTED!*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 *Date:* {lead_data['timestamp']}\n\n"
        "*👤 PERSONAL INFORMATION:*\n"
        f"• Name: {lead_data['lead_info']['name']}\n"
        f"• Email: {lead_data['lead_info']['email']}\n"
        f"• Phone: {lead_data['lead_info']['phone']}\n"
        f"• DOB: {lead_data['lead_info']['dob']}\n"
        f"• Occupation: {lead_data['lead_info']['occupation']}\n"
        f"• Marital Status: {lead_data['lead_info']['marital_status']}\n\n"
        f"*📍 LOCATION:*\n"
        f"• {lead_data['lead_info']['location']}\n"
        f"• Map: {lead_data['lead_info']['location_link']}\n\n"
        f"*💬 MESSAGE:*\n"
        f"{lead_data['lead_info']['message']}\n\n"
        f"*📱 TELEGRAM INFO:*\n"
        f"• User ID: `{lead_data['telegram_info']['user_id']}`\n"
        f"• Username: @{lead_data['telegram_info']['username']}\n"
        f"• Name: {lead_data['telegram_info']['first_name']} {lead_data['telegram_info']['last_name']}\n"
        f"• Groups: {lead_data['telegram_groups']}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=admin_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending to admin: {e}")
    
    # Thank the user
    await update.message.reply_text(
        "✅ *Thank you!*\n\n"
        "Your information has been submitted successfully. "
        "We'll get back to you soon!\n\n"
        "Type /start if you need to submit again.",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        'Operation cancelled. Type /start to begin again.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PHONE: [
                MessageHandler(filters.CONTACT, phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone)
            ],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, dob)],
            OCCUPATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, occupation)],
            MARITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, marital)],
            LOCATION: [MessageHandler(filters.LOCATION | filters.TEXT, location)],
            MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_inquiry),
                CommandHandler('skip', skip_message)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Start bot
    print("🤖 Bot is running... Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()