from tornado import web, ioloop, options
import conf
from handlers import ChannelHandler, LoginHandler, LogoutHandler, \
    ChatSocketHandler


options.define("port", default=8888, help="run on the given port", type=int)


class Application(web.Application):
    def __init__(self):
        handlers = [
            (r"/", ChannelHandler),
            (r"/channels/(?P<channel>\w+)/", ChannelHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/chatsocket/", ChatSocketHandler),
            (r"/chatsocket/(?P<channel>\w+)/", ChatSocketHandler),
        ]
        super(Application, self).__init__(handlers=handlers, **conf.settings)


def main():
    options.parse_command_line()
    app = Application()
    app.listen(options.options.port)
    ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
