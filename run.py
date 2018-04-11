import os
import signal
import argparse
import multiprocessing
import gunicorn.app.base
from gunicorn.six import iteritems


def get_pid(pidfile):
    if os.path.exists(pidfile):
        with open(pidfile, 'r') as f:
            return int(f.read())
    else:
        print('[Error]: pid file not exists!')
        return None


def rm_pidfile(pidfile):
    if os.path.exists(pidfile):
        print('[Remove File]: {}'.format(pidfile))
        os.remove(pidfile)


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


class Application(gunicorn.app.base.Application):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(Application, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():

    # 参数解析
    parser = argparse.ArgumentParser(description='Game Server Starter')
    parser.add_argument('--webport', help='Listen Http Port', type=int, default=8000)
    parser.add_argument('--start', help="Start gameservice", action="store_true")
    parser.add_argument('--stop', help='Stop gameservice', action="store_true")
    parser.add_argument('--reload', help='Reload gameservice', action="store_true")

    args = parser.parse_args()

    # gunicorn 参数
    options = {
        'bind': '%s:%s' % ('0.0.0.0', args.webport),
        'workers': number_of_workers(),
        'daemon': True,
        'pidfile': 'app.pid',
        'worker_class': 'sanic.worker.GunicornWorker',
        'graceful_timeout': 10,
        'capture_output': True,
        'errorlog': 'last_runlog.log',
    }

    if args.start:
        if os.path.exists(options['pidfile']):
            pid = get_pid(options['pidfile'])
            print('<< Server already started! >>')
        else:
            print('>>> Starting server ......')
            from app import app
            Application(app, options).run()

    elif args.stop:
        pid = get_pid(options['pidfile'])
        if pid:
            print('>>> Stoping ......')
            try:
                os.kill(pid, signal.SIGTERM)
                print('[Successed]: ok!')
            except OSError:
                print('[Failed]: <pid: {}> has gone!'.format(pid))
            finally:
                rm_pidfile(options['pidfile'])

    elif args.reload:
        pid = get_pid(options['pidfile'])
        if pid:
            print('>>> Reloading ......')
            try:
                os.kill(pid, signal.SIGHUP)
            except OSError:
                print('[Failed]: Server haven\'t start yet!')


if __name__ == "__main__":
    main()
