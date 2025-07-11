Step 1: Create a Bot with BotFather
Open Telegram and search for @BotFather.
Start a chat and send the command: /newbot
Follow the instructions to set a name and username for your bot.
After creation, BotFather will give you a token (a long string). Save this, you’ll need it later.
Step 2: Set Up Your Linux Server
Connect to your server (via SSH or directly).
Make sure Python 3.7+ is installed:
sh
python3 --version
If not, install Python 3:
sh
sudo apt update
sudo apt install python3 python3-pip
Step 3: Install the Required Library
You’ll use the python-telegram-bot library (version 20+ recommended):

sh
pip3 install python-telegram-bot --upgrade
Step 4: Write the Bot Code
Create a new file, e.g., bot.py:

sh
nano bot.py
Paste the following code (replace YOUR_TELEGRAM_BOT_TOKEN with your token):