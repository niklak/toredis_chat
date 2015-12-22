from tornado import web, ioloop, options
import conf
import handlers

options.define("port", default=8888, help="run on the given port", type=int)


class Application(web.Application):
    def __init__(self):
        h = [
            (r"/", handlers.ChannelHandler),
            (r"/channels/(?P<channel>\w+)/", handlers.ChannelHandler),
            (r"/login", handlers.LoginHandler),
            (r"/logout", handlers.LogoutHandler),
            (r"/chatsocket/(?P<channel>\w+)/", handlers.ChatSocketHandler),
        ]
        super(Application, self).__init__(handlers=h, **conf.settings)


def main():
    options.parse_command_line()
    app = Application()
    # single thread && single process
    app.listen(options.options.port)
    ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
