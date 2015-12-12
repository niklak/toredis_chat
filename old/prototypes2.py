class ChatChannelsSocketHandler(UserMixin, websocket.WebSocketHandler):
    waiters = set()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self, *args, **kwargs):
        self.chnl = kwargs.get('channel', 'main')
        logging.info('USER {} JOINED CHANNEL {}'.format(self.current_user, self.chnl))
        self.waiters.add((self.chnl, self))

    def on_close(self):
        logging.info('USER {} LEFT CHANNEL {}'.format(self.current_user, self.chnl))
        self.waiters.remove((self.chnl, self))

    def update_cache(self, chat):
        chnl = 'channels:{}'.format(self.chnl)
        r.rpush(chnl, ujson.dumps(chat))
        r.ltrim(chnl, 0, 10)   # fix

    def send_updates(self, chat):
        logging.info('sending message to %d waiters', len(self.waiters))
        logging.info('Total: %d waiters', len(self.waiters))
        chnl_waiters = tuple(filter(lambda x: x[0] == self.chnl, self.waiters))
        logging.info('Sending to %d waiters', len(chnl_waiters))
        for chnl, waiter in chnl_waiters:
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
            self.render_string('include/message.html', message=chat)
        )
        #self.write_message(chat)    # for 1
        self.update_cache(chat)
        self.send_updates(chat)


class ChatUserListHandler(UserMixin, websocket.WebSocketHandler):
    waiters = set()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self, *args, **kwargs):
        self.chnl = kwargs.get('channel', 'main')

        self.waiters.add((self.chnl, self))

        logging.info('USER {} ADDED TO THE {} CHANNEL LIST'.format(self.current_user, self.chnl))

        self.chnl_key = 'channels:{}:users'.format(self.chnl)
        count = int(r.zcount(self.chnl_key, 0, - 1))
        r.zadd(self.chnl_key, count+1, self.current_user)

        users = r.zrange(self.chnl_key, 0, -1)
        chat = self.perform_user_list_message(users)
        self.send_updates(chat)

    def on_close(self, *args, **kwargs):
        r.zrem(self.chnl_key, self.current_user)
        users = r.zrange(self.chnl_key, 0, -1)

        self.waiters.remove((self.chnl, self))
        logging.info('USER {} HAS BEEN REMOVED FROM THE {} CHANNEL LIST'.format(self.current_user, self.chnl))

        chat = self.perform_user_list_message(users)
        self.send_updates(chat)

    def send_updates(self, chat):
        logging.info('Total: %d waiters', len(self.waiters))
        chnl_waiters = tuple(filter(lambda x: x[0] == self.chnl, self.waiters))
        logging.info('Sending to %d waiters', len(chnl_waiters))

        for channel, waiter in chnl_waiters:
            try:
                logging.info(chat)
                waiter.write_message(chat)
            except:
                logging.error('Error sending message', exc_info=True)

    def perform_user_list_message(self, users):
        return {'id': str(uuid.uuid4()),
                'html': escape.to_basestring(
                    self.render_string('include/user_list.html', users=users)
                )}