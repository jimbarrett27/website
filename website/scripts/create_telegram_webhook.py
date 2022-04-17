from bots.secrets import get_telegram_bot_key
import requests

def main():

    webhook_url = f'https://www.jimbarrett.co.uk/telegram_webhook/{get_telegram_bot_key()}'

    request_data = {
        'url': webhook_url
    }

    telegram_url = f'https://api.telegram.org/bot{get_telegram_bot_key()}/setWebhook'

    response = requests.post(telegram_url, json=request_data)

    print(response.content)

if __name__ == '__main__':
    main()