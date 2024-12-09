import logging
import requests

from config import BOT_TOKEN


def send_to_telegram(name,lastname, phone, date, guests, chat_id):
    bot_token = BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    print("chaaat",chat_id)

    escaped_message = (
        f"🔔 Новая заявка на бронирование столика:\n\n"
        f"👤 Имя: {name}\n"
        f"👤 Фамилия: {lastname}\n"
        f"📞 Телефон: {phone}\n"
        f"📅 Дата: {date}\n"
        f"👥 Количество гостей: {guests}"
    )

    payload = {
        'chat_id': chat_id,
        'text': escaped_message,
        'parse_mode': 'Markdown'
    }
    try:

        response = requests.post(url, data=payload)
        if response.status_code == 200:
           logging.info("Message sent to Telegram successfully.")
        else:
            logging.error(f"Failed to send message: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"Error sending message to Telegram: {e}")

