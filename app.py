from tornado import web, ioloop, options
import conf
from handlers import IndexHandler, ChannelHandler, LoginHandler, \
    ChatSocketHandler, ChatChannelsSocketHandler


options.define("port", default=8888, help="run on the given port", type=int)


class Application(web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/channels/(?P<channel>\w+)/", ChannelHandler),
            (r"/login", LoginHandler),
            (r"/chatsocket/", ChatSocketHandler),
            (r"/chatsocket/(?P<channel>\w+)/", ChatChannelsSocketHandler),
        ]
        super(Application, self).__init__(handlers=handlers, **conf.settings)


def main():
    options.parse_command_line()
    app = Application()
    app.listen(options.options.port)
    ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
