# test-your-language-bot
Example - [@test_your_language_bot](https://t.me/test_your_language_bot)

## Usage

Clone this repo:

    $ mkdir language_bot && cd language_bot
    $ git clone https://github.com/azhvanko/test-your-language-bot.git

Add admins id in `core/config.py`  
Set ENV in Dockerfile. 
Build and start the Docker image:

    $ docker build -t language_bot .
    $ docker run --name tgbot -v language_bot_db:/home/bot/db -d language_bot
