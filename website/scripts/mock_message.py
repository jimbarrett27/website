import requests
from gcp_util.secrets import get_telegram_bot_key, get_telegram_user_id

def send_message(message: str):
    """
    When running locally, create an acceptable 
    post request to the telegram bot route to
    mock me sending a message
    """

    request_data = {
        'message': {
            'from': {
                'id': get_telegram_user_id()
            },
            'text': message
        }
    }

    url = f'http://localhost:8080/telegram_webhook/{get_telegram_bot_key()}'

    requests.post(url, json=request_data)


if __name__ == '__main__':
    message = 'echo hello world!'
    send_message(message)