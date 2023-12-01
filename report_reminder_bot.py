#! python3
# -*- coding: utf-8 -*-
try:
    from commands import *
except ImportError:
    print("Install dependency via 'pip install git+https://github.com/egigoka/commands'")
    from commands import *
try:
    import telebot
except ImportError:
    print("Install dependency via 'pip install pytelegrambotapi'")
    import telebot
import time
import os
import telegrame
from enum import Enum

__version__ = "0.1.4"

# Auth
my_chat_id = 5328715

with open("token.txt", "r") as f:
    telegram_token = f.read().strip()

telegram_api = telebot.TeleBot(telegram_token, threaded=False)

# default buttons
button_rows = [["Add to message"], ["Get message"]]

main_markup = telebot.types.ReplyKeyboardMarkup()
for button_row in button_rows:
    markup_row = main_markup.row(*[telebot.types.KeyboardButton(button) for button in button_row])


# messages
def add_message(message):
    with open("messages.txt", "a") as messages_file:
        time_now = Time.datetime()
        time_now = time_now.strftime("%d.%m.%Y %H:%M")
        messages_file.write(f"{time_now}: {message}\n")


def get_messages():
    with open("messages.txt", "r") as messages_file:
        messages = messages_file.read().strip()
    with open("messages.txt", "w") as messages_file:
        messages_file.write("")
    return messages


# state
class StateEnum(Enum):
    NONE = 0
    ADD = 1


class State:
    current = StateEnum.NONE
    previous_hour = None
    previous_new_report_message = None
    hello_said = os.path.exists(".hello_said")
    previous_write_message = None


# main logic
def _start_bot_receiver():
    @telegram_api.message_handler(content_types=["text", 'sticker'])
    def reply_all_messages(message):
        if message.chat.id == my_chat_id:
            if message.text:
                text = message.text
                if State.current == StateEnum.ADD:
                    if State.previous_write_message:
                        telegram_api.delete_message(my_chat_id, State.previous_write_message)
                    add_message(text)
                    telegrame.delete_message(telegram_api, my_chat_id, message.id)
                    State.current = StateEnum.NONE
                elif State.current == StateEnum.NONE:
                    if text == "Add to message":
                        reply = "Write message"
                        messages = telegrame.send_message(telegram_api, message.chat.id, reply)
                        if messages:
                            State.previous_write_message = messages[0].id
                        try:
                            telegram_api.delete_message(my_chat_id, message.id)
                        except Exception:
                            pass
                        State.current = StateEnum.ADD
                    elif text == "Get message":
                        reply = get_messages()
                        telegrame.send_message(telegram_api, message.chat.id, reply, disable_notification=True)
                        try:
                            telegram_api.delete_message(my_chat_id, message.id)
                        except Exception:
                            pass

            else:
                reply = "Stickers doesn't supported"
                telegrame.send_message(telegram_api, message.chat.id, reply, disable_notification=True)
                telegram_api.delete_message(my_chat_id, message.id)

        else:
            telegram_api.forward_message(my_chat_id, message.chat.id, message.message_id,
                                         disable_notification=True)
            Print.rewrite()

    telegram_api.polling(none_stop=True)


def _start_bot_sender():
    if not State.hello_said:
        telegrame.send_message(telegram_api, my_chat_id, "Hello!", reply_markup=main_markup)
        State.hello_said = True
        with open(".hello_said", "w") as hello_said_file:
            hello_said_file.write("")
    while True:
        current_hour = Time.datetime().hour
        if State.previous_hour != current_hour:
            if State.previous_new_report_message:
                telegrame.delete_message(telegram_api, my_chat_id, State.previous_new_report_message)
            State.previous_hour = current_hour
            messages = telegrame.send_message(telegram_api, my_chat_id, "New report is needed")
            if messages:
                State.previous_new_report_message = messages[0].id
            else:
                State.previous_new_report_message = None

        time.sleep(60)


# run bot
def safe_threads_run():
    # https://www.tutorialspoint.com/python/python_multithreading.htm  # you can expand current implementation

    print(f"Main thread v{__version__} started")

    threads = Threading()

    threads.add(telegrame.very_safe_start_bot, args=(_start_bot_receiver,), name="Receiver")
    threads.add(telegrame.very_safe_start_bot, args=(_start_bot_sender,), name="Sender")

    threads.start(wait_for_keyboard_interrupt=True)

    Print.rewrite()
    print("Main thread quited")


if __name__ == '__main__':
    safe_threads_run()
