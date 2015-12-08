import logging
import uuid
import redis
import ujson
import datetime
from tornado import web, websocket, escape

# Для одного клиента!
r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
# r = redis.Redis(unix_socket_path='/var/run/redis/redis.sock')

# реализовать комнаты и приватные переписки
# реализовать создание комнат
# сделать аккуратно!

# Попробовать сделать pubsub НЕТ, не в этот раз
# Сделать один обработчик вместо двух!


class UserMixin:
    def get_current_user(self):
        user = self.get_secure_cookie('user')
        return escape.xhtml_escape(user) if user else None


class LoginHandler(web.RequestHandler):
    def get(self):
        self.render('login.html', title='Authentication')

    def post(self):
        self.set_secure_cookie('user', self.get_argument('name'))
        self.redirect('/')


class LogoutHandler(web.RequestHandler):
    @web.authenticated
    def get(self):
        self.clear_cookie('user')
        self.redirect('/')


class ChannelHandler(UserMixin, web.RequestHandler):
    @web.authenticated
    def get(self, *args, **kwargs):
        title = kwargs.get('channel', 'main')
        cache = r.lrange('channels:{}'.format(title), 0, -1)
        messages = (ujson.loads(x) for x in cache) if len(cache) > 0 else []
        u_cache = r.zrange('channels:{}:users'.format(title), 0, -1)
        users = u_cache if u_cache else ['Nobody here']
        channels = ('ORANGERY', 'ISOLATOR', 'WHATEVER', 'MILKY WAY', 'COOKIES')
        self.render('index.html', messages=messages, title=title, users=users, channels=channels)


class ChatSocketHandler(UserMixin, websocket.WebSocketHandler):

    waiters = set()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self, *args, **kwargs):
        self.chnl = kwargs.get('channel', 'main')
        logging.info('USER {} JOINED CHANNEL {}'.format(self.current_user, self.chnl))
        self.waiters.add((self.chnl, self))

        self.chnl_key = 'channels:{}:users'.format(self.chnl)
        count = int(r.zcount(self.chnl_key, 0, - 1))
        r.zadd(self.chnl_key, count+1, self.current_user)

        users = r.zrange(self.chnl_key, 0, -1)
        chat = self.perform_user_list(users)
        self.send_updates(chat)

    def perform_user_list(self, users):
        return {'parent': 'user_list',
                'html': escape.to_basestring(
                    self.render_string('include/user_list.html', users=users)
                )}

    def send_updates(self, chat):
        logging.info('Total: %d waiters', len(self.waiters))
        chnl_waiters = tuple(filter(lambda x: x[0] == self.chnl, self.waiters))
        logging.info('Sending to %d waiters', len(chnl_waiters))
        logging.info(chat)
        for _, waiter in chnl_waiters:
            try:
                waiter.write_message(chat)
            except:
                logging.error('Error sending message', exc_info=True)

    def on_close(self):

        r.zrem(self.chnl_key, self.current_user)
        users = r.zrange(self.chnl_key, 0, -1)

        self.waiters.remove((self.chnl, self))
        logging.info('USER {} LEFT CHANNEL {}'.format(self.current_user, self.chnl))

        chat = self.perform_user_list(users)
        self.send_updates(chat)

    def update_channel_history(self, chat):
        chnl = 'channels:{}'.format(self.chnl)
        r.rpush(chnl, escape.json_encode(chat))
        r.ltrim(chnl, -25, -1)

    def on_message(self, message):
        logging.info('got message %r', message)
        parsed = escape.json_decode(message)
        chat = {
            'parent': 'inbox',
            'body': parsed['body'],
            'user': parsed['user'],
            'time': datetime.datetime.now().strftime('%H:%M:%S %Y-%m-%d')
            }
        self.update_channel_history(chat)
        chat['html'] = escape.to_basestring(
            self.render_string('include/message.html', message=chat)
        )
        self.send_updates(chat)
