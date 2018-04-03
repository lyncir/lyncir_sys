# -*- coding: utf8 -*-

from flask import Blueprint, session, render_template, redirect, url_for, abort, request

from app import app

blueprint = Blueprint('user', __name__)

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == app.config['PASSWORD'] and \
                request.form['username'] == app.config['USERNAME']:
            session['username'] = request.form['username']
            return redirect(url_for('blog.index'))
        else:
            abort(404)
    return render_template('login.html')


@blueprint.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('blog.index'))
