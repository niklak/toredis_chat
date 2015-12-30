from tornado import web, ioloop, locale
from conf import settings
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
    # single thread && single process
    app.listen(8888)
    ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
