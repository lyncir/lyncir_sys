import asyncio_redis
from sanic import Sanic
from sanic import response
from sanic_session import RedisSessionInterface

app = Sanic(__name__)
app.config.from_pyfile('config.py')
app.config.from_pyfile('instance/config.py')


class Redis:
    """
    A simple wrapper class that allows you to share a connection
    pool across your application.
    """
    _pool = None

    async def get_redis_pool(self):
        if not self._pool:
            self._pool = await asyncio_redis.Pool.create(
                host=app.config['REDIS_HOST'],
                port=app.config['REDIS_PORT'],
                poolsize=app.config['REDIS_POOLSIZE']
            )
        return self._pool


redis = Redis()

# pass the getter method for the connection pool into the session
session_interface = RedisSessionInterface(redis.get_redis_pool)


@app.middleware('request')
async def add_session_to_request(request):
    # before each request initialize a session
    # using the client's request
    await session_interface.open(request)


@app.middleware('response')
async def save_session(request, response):
    # after each request save the session,
    # pass the response to set client cookies
    await session_interface.save(request, response)


@app.route('/')
async def index(request):
    url = request.app.url_for('blog.index')
    return response.redirect(url)


# register blueprint
from . import blog
from . import user
app.blueprint(blog.bp)
app.blueprint(user.bp)


app.static('/static', './app/static')
