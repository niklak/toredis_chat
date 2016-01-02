import time
import logging

BEFORE_SHUTDOWN = 3


def shutdown(loop, server):
    logging.warning('Stopping http server')
    server.stop()

    logging.warning('Will shutdown in %s seconds ...', BEFORE_SHUTDOWN)

    deadline = time.time() + BEFORE_SHUTDOWN

    def stop_loop():
        now = time.time()
        if now < deadline and (loop._callbacks or loop._timeouts):
            loop.add_timeout(now + 1, stop_loop)
        else:
            loop.stop()
            logging.warning('Shutdown')
    stop_loop()
