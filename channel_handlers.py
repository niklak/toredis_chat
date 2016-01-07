from collections import defaultdict
import logging


class WaiterSet(defaultdict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_factory = set

    def broadcast(self, key, message):
        logging.info('Sending message to %d waiters', len(self[key]))
        for waiter in self[key]:
            try:
                waiter.write_message(message)
            except Exception:
                logging.error('Error sending message', exc_info=True)
