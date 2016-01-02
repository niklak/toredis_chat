import signal
from tornado import web, ioloop, locale
from tornado.httpserver import HTTPServer
from conf import settings
from server_handlers import shutdown
import handlers


class Application(web.Application):
    def __init__(self):
        h = [
            (r"/", handlers.ChannelHandler),
            (r"/channels/(?P<channel>\w+)/", handlers.ChannelHandler),
            (r"/login", handlers.LoginHandler),
            (r"/logout", handlers.LogoutHandler),
            (r"/chatsocket/(?P<channel>\w+)/", handlers.ChatSocketHandler),
        ]
        super(Application, self).__init__(handlers=h, **settings)


def main():

    locale.load_gettext_translations('locale', 'messages')
    app = Application()
    server = HTTPServer(app)
    # single thread && single process
    server.listen(8888)

    loop = ioloop.IOLoop.current()

    def sig_shutdown_handler(sig, frame):
        loop.add_callback_from_signal(shutdown, loop=loop, server=server)

    signal.signal(signal.SIGTERM, sig_shutdown_handler)
    signal.signal(signal.SIGINT, sig_shutdown_handler)

    loop.start()


if __name__ == "__main__":
    main()
