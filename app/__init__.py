from sanic import Sanic
from sanic.response import json

app = Sanic(__name__)
app.config.from_pyfile('config.py')
app.config.from_pyfile('instance/config.py')


@app.route('/')
async def test(request):
    return json({'hello': 'world'})


# register blueprint
from . import blog
app.blueprint(blog.bp)
