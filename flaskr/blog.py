from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, tag, location, time, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tag = request.form['tag']
        location = request.form['location']
        time = request.form['time']
        # joins = request.form['joins']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, tag, location, time, author_id)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (title, body, tag, location, time, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id):
    post = get_db().execute(
        'SELECT p.id, title, body, tag, location, time, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id, check_author=True):
    post = get_post(id)
    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tag = request.form['tag']
        location = request.form['location']
        time = request.form['time']
        # joins = request.form['joins']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, tag = ?,location = ?, time = ?'
                ' WHERE id = ?',
                (title, body, tag, location, time, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/post', methods=('GET', 'POST'))
def post_page(id):
    post = get_post(id)
    return render_template('blog/post.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))
