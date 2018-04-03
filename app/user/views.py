from sanic import Blueprint
from sanic import response
from sanic.exceptions import abort
from jinja2 import Environment, PackageLoader, select_autoescape


bp = Blueprint('user', url_prefix='/user')


# Load the template environment with async support
template_env = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html']),
    enable_async=True
)


# Load the template from file
login_template = template_env.get_template('login.html')


@bp.route('/login', methods=['GET', 'POST'])
async def login(request):
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if ((password == request.app.config['PASSWORD']) and
                (username == request.app.config['USERNAME'])):
            request['session']['username'] = username
            url = request.app.url_for('test')
            return response.redirect(url)
        else:
            abort(404)

    rendered_template = await login_template.render_async(request=request)
    return response.html(rendered_template)


@bp.route('/logout')
async def logout(request):
    request['session'].pop('username', None)
    url = request.app.url_for('test')
    return response.redirect(url)
