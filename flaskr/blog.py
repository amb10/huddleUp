from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Markup
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, tag, location, time, date, joins, joined_id, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/<int:id>/profile', methods=('GET', 'POST'))
def profile(id):
    user = get_user(id)
    return render_template('blog/profile.html', user=user)


@bp.route('/<int:id>/p_update', methods=('GET', 'POST'))
@login_required
def p_update(id, check_author=True):
    user = get_user(id)
    if check_author and user['id'] != g.user['id']:
        abort(403)

    if request.method == 'POST':
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_num = request.form['phone_num']
        email = request.form['email']
        error = None

        if not password:
            error = 'Password is required.'
        elif not first_name:
            error = 'First name is required.'
        elif not last_name:
            error = 'Last name is required.'
        elif not phone_num:
            error = 'Phone number is required.'
        elif not email:
            error = 'Email is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE user SET password = ?, first_name = ?, last_name = ?, phone_num = ?, email = ?'
                ' WHERE id = ?',
                (generate_password_hash(password), first_name,
                 last_name, phone_num, email, id)
            )

            db.commit()
            return redirect(url_for('blog.profile', id=id))

    return render_template('blog/p_update.html', user=user)


@bp.route('/<string:filter_name>', methods=('GET', 'POST'))
def filter_post(filter_name):
    filtered_posts = []
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, tag, location, time, date, joins, joined_id, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    filter_index = 6
    match filter_name:
        case "#Social":
            filter_index = 1
        case "#Sports":
            filter_index = 2
        case "#Academic":
            filter_index = 3
        case "#Food":
            filter_index = 4
        case "#Club":
            filter_index = 5
        case "#Other":
            filter_index = 6

    for post in posts:
        if has_filter(post, filter_index, filter_name):
            filtered_posts.append(post)

    return render_template('blog/filter.html', posts=filtered_posts)


def has_filter(post, filter_index, filter_name):
    tags = post['tag'].split()
    if len(tags) < filter_index:
        filter_index = len(tags)

    for i in range(filter_index):
        if tags[i] == filter_name:
            return True
    return False


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tag_list = request.form.getlist('tag')
        tag = ""
        for x in tag_list:
            tag = tag + " #" + x
        location = request.form['location']
        time = request.form['time']
        date = request.form['date']
        joins = request.form['joins']
        joined_id = str(g.user['id'])
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, tag, location, time, date, joins, joined_id, author_id)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (title, body, tag, location, time, date,
                 joins, joined_id, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id):
    post = get_db().execute(
        'SELECT p.id, title, body, tag, location, time, date, joins, joined_id, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    return post


def get_user(id):
    user = get_db().execute(
        'SELECT u.id, username, password, first_name, last_name, phone_num, email'
        ' FROM user u'
        ' WHERE u.id = ?',
        (id,)
    ).fetchone()

    if user is None:
        return 'none'

    return user


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id, check_author=True):
    post = get_post(id)
    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tag_list = request.form.getlist('tag')
        tag = ""
        for x in tag_list:
            tag = tag + " #" + x
        location = request.form['location']
        time = request.form['time']
        date = request.form['date']
        joins = request.form['joins']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, tag = ?, joins = ?, location = ?, time = ?, date = ?'
                ' WHERE id = ?',
                (title, body, tag, joins, location, time, date, id)
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


@bp.route('/<int:id>/join_post', methods=('POST',))
@login_required
def join_post(id):
    post = get_post(id)

    joins = post['joins']
    joined_id = post['joined_id']
    error = None

    if post['author_id'] == g.user['id']:
        error = "You created this event!"

    # if statement here for user who already joined
    list_of_joined = joined_id.split(" ")
    for x in list_of_joined:
        x.strip()
        if str(g.user[id]) == x:
            error = "You already joined this event!"

    if joins == 0:
        error = "No slots left!"

    if error is not None:
        flash(error)
    else:
        flash("Successfully joined event!")
        joins -= 1
        joined_id = joined_id + " " + str(g.user['id'])
        db = get_db()
        db.execute(
            'UPDATE post SET joins = ?, joined_id = ?'
            ' WHERE id = ?',
            (joins, joined_id, id)
        )
        db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/view_joined', methods=('POST',))
@login_required
def view_joined(id):
    post = get_post(id)
    joined_id = post['joined_id']
    display_list = ""
    error = None

    list_of_joined = joined_id.split(" ")
    for x in list_of_joined:
        x.strip()
        x = int(x)
        if (get_user(x) == 'none'):
            display_list = display_list + "NULL USER\n"
        else:
            display_list = display_list + "<a href=" + \
                str(x) + "/profile>" + str(get_user(x)['username']) + "</a>\n"
    flash(Markup(display_list))
    return redirect(url_for('blog.index'))
