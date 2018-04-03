import os
import stat

import aiofiles
from sanic import Blueprint
from sanic import response
from sanic.exceptions import abort
from jinja2 import Environment, PackageLoader, select_autoescape
from werkzeug import secure_filename


bp = Blueprint('blog', url_prefix='/blog')

_basedir = os.path.abspath(os.path.dirname(__file__))
PAGES_DIR = os.path.join(_basedir, 'pages')
UPLOAD_FOLDER = os.path.join(PAGES_DIR, '{pagename}/attachments')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3'])


# Load the template environment with async support
template_env = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html']),
    enable_async=True
)


# Load the template from file
post_template = template_env.get_template('post.html')
edit_post_template = template_env.get_template('editpost.html')
upload_template = template_env.get_template('upload.html')


@bp.route('/<pagename>')
async def show_post(request, pagename):
    if os.path.exists(await init_page(pagename)):
        creole_html = await init_page(pagename, action='r')

        rendered_template = await post_template.render_async(creole_html=creole_html, request=request)
        return response.html(rendered_template)

    # page not found
    else:
        abort(404)


@bp.route('/<pagename>/edit', methods=['GET', 'POST'])
async def edit_post(request, pagename):
    if request['session'].get('username'):
        if request.method == 'POST':
            text = request.form.get('savetext')
            await init_page(pagename, action='w', text=text)
            url = request.app.url_for('blog.show_post', pagename=pagename)
            return response.redirect(url)

        if not os.path.exists(await init_page(pagename)):
            await init_page(pagename, action='i')
        text = await init_page(pagename, action='r')

        rendered_template = await edit_post_template.render_async(text=text, request=request)
        return response.html(rendered_template)

    else:
        abort(404)


@bp.route('/<pagename>/upload', methods=['GET', 'POST'])
async def upload_file(request, pagename):
    if request['session'].get('username'):
        file_path = UPLOAD_FOLDER.format(pagename=pagename)
        if request.method == 'POST':
            upload_file = request.files.get('file')
            if upload_file and allowed_file(upload_file.name):
                filename = secure_filename(upload_file.name)
                async with aiofiles.open(os.path.join(file_path, filename), 'wb') as f:
                    await f.write(upload_file.body)
                return response.html('upload success!')
            else:
                return response.html('upload failed!')

        rendered_template = await upload_template.render_async(request=request)
        return response.html(rendered_template)

    else:
        abort(404)


@bp.route('/<pagename>/uploads/<filename>')
async def uploaded_file(request, pagename, filename):
    file_path = UPLOAD_FOLDER.format(pagename=pagename)
    return await response.file_stream(os.path.join(file_path, filename))


async def init_page(pagename, action='d', text=''):
    """ Init pages dir stracture

    pages
    └──PageName
        ├── attachments
        └── text

    :param pagename: also title name
    :param action: enums: i: initial r: read text w: write text d: retuen path
    """
    page_path = os.path.join(PAGES_DIR, pagename)
    # initial pages, include text, and uploads dir attachments
    if action == 'i':
        if not os.path.exists(page_path):
            os.mkdir(page_path)
            async with aiofiles.open(os.path.join(page_path, 'text'), 'a') as f:
                await f.close()
            os.mkdir(os.path.join(page_path, 'attachments'))
            return True

    # return page path
    if action == 'd':
        return page_path

    # read from text
    if action == 'r':
        async with aiofiles.open(os.path.join(page_path, 'text')) as f:
            return await f.read()

    # write to text
    if action == 'w':
        async with aiofiles.open(os.path.join(page_path, 'text'), 'w') as f:
            await f.write(text)
            return True


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
