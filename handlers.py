import logging
import datetime
from redis import StrictRedis
from tornado import web, websocket, escape
# In this case we use 1 redis connection(client) for all queries
r = StrictRedis(db=1)

logger = logging.getLogger('info-log')
# logger.disabled = True

# It is not a publish / subscribe example


class UserMixin:
    def get_current_user(self):
        user = self.get_secure_cookie('user')
        return escape.xhtml_escape(user) if user else None


class LoginHandler(web.RequestHandler):
    def get(self):
        _ = self.locale.translate
        title = _('Authentication')
        self.render('login.html', title=title)

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
        messages = (escape.json_decode(x) for x in cache) if cache else []
        user_cache = r.zrange('channels:{}:users'.format(title), 0, -1)
        users = user_cache if user_cache else ['Nobody here']
        channels = ('ORANGERY', 'ISOLATOR', 'WHATEVER', 'MILKY WAY', 'COOKIES')
        self.render('index.html', title=title, messages=messages,
                    users=users, channels=channels)


class ChatSocketHandler(UserMixin, websocket.WebSocketHandler):
    # Waiters set can contain objects, tuples, instances of the named_tuple
    # or some other construction containing waiter objects
    # (instance of this class) and its identifier.
    waiters = set()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self, *args, **kwargs):
        self.chnl = kwargs.get('channel', 'main')
        self.waiters.add((self.chnl, self))

        self.chnl_key = 'channels:{}:users'.format(self.chnl)
        count = int(r.zcount(self.chnl_key, 0, - 1))
        r.zadd(self.chnl_key, count+1, self.current_user)
        users = r.zrange(self.chnl_key, 0, -1)

        chat = self.perform_user_list(users)
        self.send_updates(chat)

        self.log('JOINED')

    def on_close(self):

        r.zrem(self.chnl_key, self.current_user)
        users = r.zrange(self.chnl_key, 0, -1)

        self.waiters.remove((self.chnl, self))

        chat = self.perform_user_list(users)
        self.send_updates(chat)

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
        self.send_updates(chat)

    def log(self, event):
        logger.info('USER {} {} CHANNEL {}'.format(self.current_user,
                                                    event, self.chnl))

    def perform_user_list(self, users):
        return {'parent': 'user_list',
                'html': escape.to_basestring(
                    self.render_string('include/user_list.html', users=users)
                )}

    def send_updates(self, chat):
        chnl_waiters = tuple(w for c, w in self.waiters if c == self.chnl)
        logger.info('Sending message to %d waiters', len(chnl_waiters))
        for waiter in chnl_waiters:
            try:
                waiter.write_message(chat)
            except:
                logger.error('Error sending message', exc_info=True)

    def update_channel_history(self, chat):
        chnl = 'channels:{}'.format(self.chnl)
        r.rpush(chnl, escape.json_encode(chat))
        r.ltrim(chnl, -25, -1)

    def __del__(self):
        r.zrem(self.chnl_key, self.current_user)
        self.log('PUSHED OUT')
