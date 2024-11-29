import logging
import requests


def send_to_telegram(name, phone, date, time, guests, chat_id):
    bot_token = '7451477534:AAFYTKDG-rHyl20pShvIhIPaeGhh75NzIS0'
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    escaped_message = (
        f"🔔 Новая заявка на бронирование столика:\n\n"
        f"👤 Имя: {name}\n"
        f"📞 Телефон: {phone}\n"
        f"📅 Дата: {date}\n"
        f"🕒 Время: {time}\n"
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
