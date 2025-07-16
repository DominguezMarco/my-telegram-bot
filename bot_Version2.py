import logging
import subprocess
import json
import hashlib
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_token(filename="bot_token.txt"):
    with open(filename, "r") as f:
        return f.read().strip()

def get_allowed_commands(filename="allowed_commands.json"):
    with open(filename, "r") as f:
        return json.load(f)

def get_hash(filename="auth_hash.txt"):
    with open(filename, "r") as f:
        return f.read().strip()

TOKEN = get_token()
ALLOWED_COMMANDS = get_allowed_commands()
PASSWORD_HASH = get_hash()

# Diccionario para guardar chats autenticados
authenticated_chats = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu bot seguro. Usa /auth <contraseña> para autenticarte antes de ejecutar comandos con /run."
    )

async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /auth <contraseña>")
        return
    password = " ".join(context.args)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash == PASSWORD_HASH:
        authenticated_chats.add(update.effective_chat.id)
        await update.message.reply_text("¡Autenticación exitosa! Ahora puedes usar /run.")
    else:
        await update.message.reply_text("Contraseña incorrecta.")

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in authenticated_chats:
        await update.message.reply_text("No estás autenticado. Usa /auth <contraseña> primero.")
        return

    if not context.args:
        await update.message.reply_text(
            "Uso: /run <alias>. Aliases permitidos: " + ", ".join(ALLOWED_COMMANDS.keys())
        )
        return

    alias = " ".join(context.args)
    if alias not in ALLOWED_COMMANDS:
        await update.message.reply_text(f"Alias '{alias}' no permitido.")
        return

    try:
        output = subprocess.check_output(ALLOWED_COMMANDS[alias], stderr=subprocess.STDOUT, text=True)
        if len(output) > 4000:
            output = output[:3997] + "..."
        await update.message.reply_text(f"Salida de '{alias}':\n{output}")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"Error ejecutando '{alias}':\n{e.output}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("auth", auth))
    app.add_handler(CommandHandler("run", run_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()

if __name__ == '__main__':
    main()