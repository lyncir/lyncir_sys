import os
import stat

import aiofiles
from sanic import Blueprint
from sanic import response
from sanic.exceptions import abort
from jinja2 import Environment, PackageLoader, select_autoescape

from .utils import creole_parser


bp = Blueprint('blog', url_prefix='/blog')

_basedir = os.path.abspath(os.path.dirname(__file__))
PAGES_DIR = os.path.join(_basedir, 'pages')
UPLOAD_FOLDER = os.path.join(PAGES_DIR, '{pagename}/attachments')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3'])
ALLOWED_HTML = set(['html', 'htm', 'xhtml'])


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


@bp.route('/')
async def index(request):
    pagename = 'FrontPage'
    creole_markup = await init_page(pagename, action='r')
    creole_html = creole_parser(creole_markup)

    rendered_template = await post_template.render_async(creole_html=creole_html, request=request)
    return response.html(rendered_template)


@bp.route('/<pagename>')
async def show_post(request, pagename):
    if os.path.exists(await init_page(pagename)):
        # 先读html 再读text
        html = await init_page(pagename, action='r', mime_type="html")
        if html:
            return response.html(html)

        creole_markup = await init_page(pagename, action='r')
        creole_html = creole_parser(creole_markup)

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
                filename = upload_file.name
                async with aiofiles.open(os.path.join(file_path, filename), 'wb') as f:
                    await f.write(upload_file.body)
                return response.html('upload success!')
            else:
                return response.html('upload failed!')

        rendered_template = await upload_template.render_async(request=request)
        return response.html(rendered_template)

    else:
        abort(404)


@bp.route('/<pagename>/upload_html', methods=['GET', 'POST'])
async def upload_html(request, pagename):
    if request['session'].get('username'):
        if request.method == 'POST':
            upload_file = request.files.get('file')
            if upload_file and allowed_html(upload_file.name):
                await init_page(pagename, action='w', html=upload_file.body, mime_type="html")
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


async def init_page(pagename, action='d', text='', html='', mime_type='text'):
    """ Init pages dir stracture

    pages
    └──PageName
        ├── attachments
        ├── text
        └── html

    :param pagename: also title name
    :param action: enums: i: initial r: read text w: write text d: retuen path
    """
    page_path = os.path.join(PAGES_DIR, pagename)
    # 初始化Page.主要包含attachments,text,html
    if action == 'i':
        if not os.path.exists(page_path):
            os.mkdir(page_path)
            os.mkdir(os.path.join(page_path, 'attachments'))

            async with aiofiles.open(os.path.join(page_path, 'text'), 'a') as f:
                await f.close()

            async with aiofiles.open(os.path.join(page_path, 'html'), 'a') as f:
                await f.close()

            return True

    # 返回Page路径
    if action == 'd':
        return page_path

    # 根据类型读取内容
    if action == 'r' and mime_type in ["text", "html"]:
        if mime_type == "text":
            async with aiofiles.open(os.path.join(page_path, 'text')) as f:
                return await f.read()

        if mime_type == "html":
            if os.path.exists(os.path.join(page_path, 'html')):
                async with aiofiles.open(os.path.join(page_path, 'html')) as f:
                    return await f.read()

    # write to text
    if action == 'w' and mime_type in ["text", "html"]:
        if mime_type == "text":
            async with aiofiles.open(os.path.join(page_path, 'text'), 'w') as f:
                await f.write(text)
                return True

        if mime_type == "html":
            async with aiofiles.open(os.path.join(page_path, 'html'), 'wb') as f:
                await f.write(html)
                return True


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def allowed_html(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_HTML
