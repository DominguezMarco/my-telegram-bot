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

def get_allowed_telegram_user(filename="allowed_telegram_user.txt"):
    with open(filename, "r") as f:
        return int(f.read().strip())

def get_active_users_list(filename="active_users.txt"):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

TOKEN = get_token()
ALLOWED_COMMANDS = get_allowed_commands()
PASSWORD_HASH = get_hash()
ALLOWED_TELEGRAM_USER = get_allowed_telegram_user()
authenticated_chats = set()

def is_authorized(user_id):
    return user_id == ALLOWED_TELEGRAM_USER

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("No estás autorizado para usar este bot.")
        return
    help_cmds = [k for k in ALLOWED_COMMANDS.keys() if k not in ["restartService", "anyCommand", "getTelegramUser", "isUserActive"]]
    help_cmds.append("isUserActive")
    await update.message.reply_text(
        "¡Hola! Soy tu bot seguro. Usa /auth <contraseña> para autenticarte antes de ejecutar comandos con /run.\n"
        "Comandos disponibles: " + ", ".join(help_cmds) +
        "\nComando especial: /run restartService <servicio> (requiere autenticación y configuración de sudo)\n"
        "Comando especial: /run isUserActive (verifica usuarios gráficos activos definidos en active_users.txt)"
    )

async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("No estás autorizado para usar este bot.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /auth <contraseña>")
        return
    password = " ".join(context.args)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash == PASSWORD_HASH:
        authenticated_chats.add(update.effective_chat.id)
        await update.message.reply_text("¡Autenticación exitosa! Ahora puedes usar /run y comandos especiales.")
    else:
        await update.message.reply_text("Contraseña incorrecta.")

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("No estás autorizado para usar este bot.")
        return
    if update.effective_chat.id not in authenticated_chats:
        await update.message.reply_text("No estás autenticado. Usa /auth <contraseña> primero.")
        return
    if not context.args:
        allowed = [k for k in ALLOWED_COMMANDS.keys() if k not in ["restartService", "anyCommand", "getTelegramUser", "isUserActive"]]
        allowed.append("isUserActive")
        await update.message.reply_text(
            "Uso: /run <alias>. Aliases permitidos: " + ", ".join(allowed)
        )
        return

    alias = context.args[0]
    # Comando seguro desde JSON (excepto isUserActive)
    if alias in ALLOWED_COMMANDS and alias != "isUserActive":
        try:
            output = subprocess.check_output(ALLOWED_COMMANDS[alias], stderr=subprocess.STDOUT, text=True)
            if len(output) > 4000:
                output = output[:3997] + "..."
            await update.message.reply_text(f"Salida de '{alias}':\n{output}")
        except Exception as e:
            await update.message.reply_text(f"Error ejecutando '{alias}':\n{e}")
        return

    # isUserActive - verifica usuarios definidos en active_users.txt
    if alias == "isUserActive":
        try:
            who_output = subprocess.check_output(["who"], text=True)
            active_users = get_active_users_list()
            found = []
            for user in active_users:
                # Busca líneas que contengan el usuario y :0 (sesión gráfica típica)
                if any(user in line and ":0" in line for line in who_output.splitlines()):
                    found.append(user)
            if found:
                await update.message.reply_text(f"Usuarios activos en sesión gráfica: {', '.join(found)}")
            else:
                await update.message.reply_text("Ningún usuario monitoreado está activo en la sesión gráfica.")
        except Exception as e:
            await update.message.reply_text(f"Error comprobando usuarios gráficos:\n{e}")
        return

    # restartService [service]
    if alias == "restartService":
        if len(context.args) < 2:
            await update.message.reply_text("Uso: /run restartService <servicio>")
            return
        service = context.args[1]
        try:
            cmd = ["sudo", "systemctl", "restart", service]
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            await update.message.reply_text(f"Servicio '{service}' reiniciado correctamente.")
        except subprocess.CalledProcessError as e:
            await update.message.reply_text(f"Error reiniciando '{service}':\n{e.output}")
        return

    # anyCommand [cualquier comando]
    if alias == "anyCommand":
        if len(context.args) < 2:
            await update.message.reply_text("Uso: /run anyCommand <comando con parámetros>")
            return
        custom_cmd = context.args[1:]
        try:
            cmd = ["sudo"] + custom_cmd
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            if len(output) > 4000:
                output = output[:3997] + "..."
            await update.message.reply_text(f"Salida:\n{output}")
        except subprocess.CalledProcessError as e:
            await update.message.reply_text(f"Error ejecutando el comando:\n{e.output}")
        return

    # getTelegramUser
    if alias == "getTelegramUser":
        user = update.effective_user
        info = (
            f"ID de Telegram: {user.id}\n"
            f"Nombre: {user.first_name} {user.last_name or ''}\n"
            f"Username: @{user.username if user.username else ''}"
        )
        await update.message.reply_text(info)
        return

    await update.message.reply_text(f"Alias '{alias}' no permitido.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_authorized(update.effective_user.id):
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