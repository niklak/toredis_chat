import datetime
from tornado import websocket, escape
from channel_handlers import WaiterSet
from handlers import UserMixin, r, logger


class ChatSocketHandler(UserMixin, websocket.WebSocketHandler):

    waiters = WaiterSet()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self, *args, **kwargs):
        self.chnl = kwargs.get('channel', 'main')
        self.chnl_key = 'channels:{}:users'.format(self.chnl)

        count = int(r.zcount(self.chnl_key, 0, - 1))
        r.zadd(self.chnl_key, count+1, self.current_user)
        users = r.zrange(self.chnl_key, 0, -1)

        chat = self.perform_user_list(users)

        self.waiters[self.chnl].add(self)
        self.waiters.broadcast(self.chnl, chat)

        self.log('JOINED')

    def on_close(self):

        r.zrem(self.chnl_key, self.current_user)
        users = r.zrange(self.chnl_key, 0, -1)

        chat = self.perform_user_list(users)

        self.waiters[self.chnl].remove(self)
        self.waiters.broadcast(self.chnl, chat)

        self.log('LEFT')

    def on_message(self, message):
        parsed = escape.json_decode(message)
        chat = {
            'parent': 'inbox',
            'body': parsed['body'] if len(parsed['body']) <= 128 else 'D`oh.',
            'user': parsed['user'],
            'time': datetime.datetime.now().strftime('%H:%M:%S %Y-%m-%d')
            }
        self.update_channel_history(chat)
        chat['html'] = escape.to_basestring(
            self.render_string('include/message.html', message=chat)
        )
        self.waiters.broadcast(self.chnl, chat)

    def log(self, event):
        logger.info('USER {} {} CHANNEL {}'.format(self.current_user,
                                                    event, self.chnl))

    def perform_user_list(self, users):
        return {'parent': 'user_list',
                'html': escape.to_basestring(
                    self.render_string('include/user_list.html', users=users)
                )}

    def update_channel_history(self, chat):
        chnl = 'channels:{}'.format(self.chnl)
        r.rpush(chnl, escape.json_encode(chat))
        r.ltrim(chnl, -25, -1)

    def __del__(self):
        r.zrem(self.chnl_key, self.current_user)
        self.log('PUSHED OUT')
