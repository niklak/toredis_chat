from tornado import web, ioloop, options
import conf
from handlers import IndexHandler, LoginHandler, ChatSocketHandler


options.define("port", default=8888, help="run on the given port", type=int)


class Application(web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/login", LoginHandler),
            (r"/chatsocket", ChatSocketHandler),
        ]
        super(Application, self).__init__(handlers=handlers, **conf.settings)


def main():
    options.parse_command_line()
    app = Application()
    app.listen(options.options.port)
    ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
