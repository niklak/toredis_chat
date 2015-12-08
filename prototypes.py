class MultiChatSocketHandler(websocket.WebSocketHandler):
    waiters = set()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self, *args, **kwargs):
        setattr(self, 'channel', kwargs.get('channel', 'main'))
        self.waiters.add((self.channel, self))

    def on_close(self):
        self.waiters.remove((self.channel, self))

    @classmethod
    def update_cache(cls, chat, channel):
        u_channel = 'channels:{}'.format(channel)
        r.rpush(u_channel, ujson.dumps(chat))
        r.ltrim(u_channel, 0, 10)

    @classmethod
    def send_updates(cls, chat, channel):
        logging.info('sending message to %d waiters', len(cls.waiters))
        for channel, waiter in cls.waiters:
            if channel == channel:
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
        self.update_cache(chat, self.channel)
        self.send_updates(chat, self.channel)


class MonoChatSocketHandler(websocket.WebSocketHandler):
    waiters = set()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self, *args, **kwargs):
        setattr(self, 'channel', kwargs.get('channel', 'main'))
        self.waiters.add((self.channel, self))

    def on_close(self):
        self.waiters.remove(self)

    @classmethod
    def update_cache(cls, chat):
        r.rpush('channels', ujson.dumps(chat))
        r.ltrim('channels', 0, 10)

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