import logging
import json
import threading
from datetime import datetime, timedelta
from ast import literal_eval

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest

try:
    with open('messages_to_delete') as f:
        messages_to_delete = literal_eval(f.read().strip())
except SyntaxError:
    messages_to_delete = {}

logging.basicConfig(
    format='%(levelname)s - %(message)s',
    level=logging.INFO
)

RUNNING = True

with open('config.json') as f:
    CONFIG = json.loads(f.read().strip())

GROUP_ID = CONFIG['CHAT_ID']

TWO_WEEK_DELTA = timedelta(weeks=2)

updater = Updater(CONFIG['API_TOKEN'])

def handle_new_message(bot, update):
    # Enqueue mesage
    logging.info(
        'Queueing message with ID {}'.format(update.message['message_id'])
    )
    messages_to_delete[update.message['message_id']] = update.message['date'].timestamp()
    logging.info(messages_to_delete)

    # Alive checking
    if update.message.text == '/oi':
        update.message.reply_text('I\'m alive')

    # Delete all queued messages
    if update.message.text == '/nuke':
        logging.info('Nuking...')

        for message_id in messages_to_delete.copy():
            try:
                if updater.bot.delete_message(GROUP_ID, message_id):
                    logging.info('Deleted message with ID {}'.format(message_id))
                    # Remove message from dict, has been deleted
                    delete_id_from_dict(message_id)
                else:
                    logging.warning('Failed to delete message with ID {}'.format(message_id))
            except BadRequest:
                logging.warning('Message with ID {} was already deleted'.format(message_id))
                delete_id_from_dict(message_id)

def delete_messages():
    while RUNNING:
        for id_and_timestamp in messages_to_delete.copy().items():
            # Split up tuple into sending time of message and message id
            message_id, timestamp  = id_and_timestamp

            # Calculate when the message expires
            message_expiry = datetime.fromtimestamp(timestamp) + TWO_WEEK_DELTA

            # Check if message is past expiry date
            if message_expiry < datetime.now():
                try:
                    if updater.bot.delete_message(GROUP_ID, message_id):
                        logging.info('Deleted message with ID {}'.format(message_id))
                        # Remove message from dict, has been deleted
                        delete_id_from_dict(message_id)
                    else:
                        logging.warning('Failed to delete message with ID {}'.format(message_id))

                except BadRequest:
                    logging.warning('Message with ID {} was already deleted'.format(message_id))
                    delete_id_from_dict(message_id)

def delete_id_from_dict(message_id):
    try:
        del messages_to_delete[message_id]
    except KeyError:
        logging.warning('ID {} wasn\'t in dict'.format(message_id))

# Start message deletion thread
message_deletion_thread = threading.Thread(target=delete_messages)
message_deletion_thread.start()

# Add message handler
updater.dispatcher.add_handler(
   MessageHandler(Filters.chat(chat_id=GROUP_ID), handle_new_message)
)

# Setup and run
updater.start_polling()
updater.idle()

# Kill infinite loop in the other thread
RUNNING = False

# Save message queue to file
with open('messages_to_delete', 'w') as f:
    f.write(repr(messages_to_delete))