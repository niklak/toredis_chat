import logging
import uuid
import redis
import ujson
import datetime
from tornado import web, websocket, escape

r = redis.StrictRedis(host='localhost', port=6379, db=0)
# r = redis.Redis(unix_socket_path='/var/run/redis/redis.sock')

# реализовать комнаты и приватные переписки


class BaseHandler(web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('user')

    def get(self):
        if not self.current_user:
            self.redirect('/login')
            return


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html', title='Authentication')

    def post(self):
        self.set_secure_cookie('user', self.get_argument('name'))
        self.redirect('/')
        

class IndexHandler(BaseHandler):
    def get(self):
        super().get()
        cache = r.lrange('messages', 0, -1)
        if len(cache) > 0:
            logging.info('got cache %r', cache)
            messages = (ujson.loads(x) for x in cache)
        else:
            messages = []
        self.render('index.html', messages=messages, title='Chat')


class ChatSocketHandler(websocket.WebSocketHandler):
    # redis.Redis(unix_socket_path='/tmp/redis.sock')
    waiters = set()
    cache = r.lrange('messages', 0, -1)

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        self.waiters.add(self)

    def on_close(self):
        self.waiters.remove(self)

    @classmethod
    def update_cache(cls, chat):
        r.rpush('messages', ujson.dumps(chat))
        r.ltrim('messages', 0, 10)

    @classmethod
    def send_updates(cls, chat):
        logging.info('sending message to %d waiters', len(cls.waiters))
        for waiter in cls.waiters:
            logging.info(waiter)
            try:
                waiter.write_message(chat)
            except:
                logging.error('Error sending message', exc_info=True)

    def on_message(self, message):
        logging.info('got message %r', message)
        parsed = escape.json_decode(message)
        chat = {
            'id': str(uuid.uuid4()),
            'body': parsed['body'],
            'user': parsed['user'],
            'time': datetime.datetime.now().strftime('%H:%M:%S %Y-%m-%d')
            }
        chat['html'] = escape.to_basestring(
            self.render_string('message.html', message=chat))

        #self.write_message(chat)    # for 1
        self.update_cache(chat)
        self.send_updates(chat)