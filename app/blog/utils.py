import genshi
from creole import creole2html
from pygments import highlight
from pygments.lexers import get_lexer_by_name, ClassNotFound
from pygments.formatters import HtmlFormatter


default_lexer = get_lexer_by_name('text')


def macro_code(lang, text):
    """
    """
    try:
        lexer = get_lexer_by_name(lang, stripall=True)
    except ClassNotFound:
        lexer = default_lexer

    formatter = HtmlFormatter()
    return genshi.Markup(highlight(text, lexer, formatter))


def creole_parser(creole_markup):
    return creole2html(creole_markup, macros={'code': macro_code})
