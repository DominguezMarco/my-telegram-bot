import logging
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Define a whitelist of allowed commands
ALLOWED_COMMANDS = {
    "date": ["date"],
    "uptime": ["uptime"],
    "df": ["df", "-h"],
    # Add more allowed commands here
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm your bot. Send me a message and I'll echo it back! Use /run <command> to run a server command.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /run <command>. Allowed commands: " + ", ".join(ALLOWED_COMMANDS.keys()))
        return

    cmd = context.args[0]
    if cmd not in ALLOWED_COMMANDS:
        await update.message.reply_text(f"Command '{cmd}' not allowed.")
        return

    try:
        output = subprocess.check_output(ALLOWED_COMMANDS[cmd], stderr=subprocess.STDOUT, text=True)
        # Telegram messages have a length limit
        if len(output) > 4000:
            output = output[:3997] + "..."
        await update.message.reply_text(f"Output of '{cmd}':\n{output}")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"Error running '{cmd}':\n{e.output}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("run", run_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()

if __name__ == '__main__':
    main()