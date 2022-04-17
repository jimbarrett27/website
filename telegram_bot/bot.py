import requests
from gcp_util.secrets import get_telegram_bot_key, get_telegram_user_id
from gcp_util.blob_storage import update_stored_json, get_stored_json
from datetime import datetime


def handle_bot_request(message: str):
    """
    Given a message sent to the telegram bot,
    parse it, and perform the appropriate action
    """

    split_message = message.split(" ")
    command = split_message[0]
    body = " ".join(split_message[1:])

    if command == 'echo':
        send_message_to_bot(body)
    elif command == 'weighin':
        record_weight(body)
    else:
        send_message_to_bot(f"'{command}' is an unknown command. Try again 😇")

    

def send_message_to_bot(message: str):
    
    response_data = {"chat_id": get_telegram_user_id(), "text": message}

    requests.post(
        f"https://api.telegram.org/bot{get_telegram_bot_key()}/sendMessage",
        json=response_data,
    )

def record_weight(body: str) -> None:

    try:
        weight = float(body)
    except:
        send_message_to_bot(f"'{body}' couldn't be interpreted as a float. Weight not recorded")
        return

    new_measurement = {
        'date': datetime.now().isoformat(),
        'weight': weight
    }

    if update_stored_json('weight.json', update_dict=new_measurement):
        send_message_to_bot(f"successfully recored weight as {weight}")
    else:
        send_message_to_bot("Something went wrong storing the weight. Debug time 🤓")