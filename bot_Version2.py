import logging
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Leer el token desde un archivo externo
def get_token(filename="bot_token.txt"):
    with open(filename, "r") as f:
        return f.read().strip()

# Leer comandos permitidos desde un archivo externo
def get_allowed_commands(filename="allowed_commands.txt"):
    allowed = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key = line.split()[0]
            allowed[key] = line.split()
    return allowed

TOKEN = get_token()
ALLOWED_COMMANDS = get_allowed_commands()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu bot. Usa /run <comando> para ejecutar un comando permitido en el servidor.\n"
        "Comandos permitidos: " + ", ".join(ALLOWED_COMMANDS.keys())
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Uso: /run <comando>. Comandos permitidos: " + ", ".join(ALLOWED_COMMANDS.keys())
        )
        return

    cmd = context.args[0]
    if cmd not in ALLOWED_COMMANDS:
        await update.message.reply_text(f"Comando '{cmd}' no permitido.")
        return

    try:
        output = subprocess.check_output(ALLOWED_COMMANDS[cmd], stderr=subprocess.STDOUT, text=True)
        if len(output) > 4000:
            output = output[:3997] + "..."
        await update.message.reply_text(f"Salida de '{cmd}':\n{output}")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"Error ejecutando '{cmd}':\n{e.output}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("run", run_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()

if __name__ == '__main__':
    main()