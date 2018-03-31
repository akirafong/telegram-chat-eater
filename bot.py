import logging
import json
import threading
import datetime

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

message_deletion_queue = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

with open('config.json') as f:
    CONFIG = json.loads(f.read().strip())

GROUP_ID = CONFIG['CHAT_ID']

TWO_WEEK_DELTA = datetime.timedelta(weeks=2)

updater = Updater(CONFIG['API_TOKEN'])

def equeue_new_message(bot, update):
    print('Queueing message with ID {}'.format(
        update.message['message_id'])
    )
    message_deletion_queue[update.message['message_id']] = datetime.datetime.now()

def message_deleter():
    while True:
        for time_id_tuple in message_deletion_queue.copy().items():
            # Split up tuple into sending time of message and message id
            message_id, time_sent  = time_id_tuple

            # Calculate when the message expires
            message_expiry = time_sent + TWO_WEEK_DELTA

            # Check if message is past expiry date
            delete_message = message_expiry < datetime.datetime.now()

            if delete_message:
                if updater.bot.delete_message(GROUP_ID, message_id):
                    print("Deleted message with ID {}".format(message_id))
                    # Remove message from dict, has been deleted
                    message_deletion_queue.pop(message_id)
                else:
                    print("Did not deleted message with ID {}".format(message_id))

message_deletion_thread = threading.Thread(target=message_deleter)
message_deletion_thread.start()

updater.dispatcher.add_handler(
   MessageHandler(
       Filters.chat(chat_id=GROUP_ID),
       equeue_new_message
   )
)
updater.start_polling()
updater.idle()