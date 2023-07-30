import os
import sqlite3
from collections import namedtuple
from datetime import datetime

from PIL import Image
from flask import Flask, render_template, request, g, redirect, url_for
from werkzeug.utils import secure_filename

from datetime import datetime, timedelta

date_string = "1987-08-13 00:00:00"
date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

# Добавляем 0 часов
new_date = date_object + timedelta(hours=3)

formatted_date = new_date.strftime("%H:%M:%S %d-%m-%Y")
print(formatted_date)



# # Присвоение значения переменной 'date'
# date_string = "2022-01-01 10:30:00"
# date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
#
# formatted_date = date_object.strftime("%H:%M:%S %d-%m-%Y")
# print(formatted_date)


app = Flask(__name__)
app.config['DATABASE'] = 'database.db'

Message = namedtuple('Message', 'id text photo user date')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db


def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.teardown_appcontext
def teardown_appcontext(e):
    close_db()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


init_db()


@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        text = request.form['text']
        photo = request.files['photo']
        user = "username"
        date = datetime.now()

        new_date = date + timedelta(
            hours=30)  # Прибавляем 3 часа к текущей дате и времени

        if photo.filename != '':
            filename = secure_filename(photo.filename)
            max_width = 1000
            image = Image.open(photo)
            image.thumbnail((max_width, max_width))
            image.save(os.path.join(app.static_folder, 'photos', filename))
        else:
            filename = None

        db = get_db()
        db.execute(
            'INSERT INTO messages (text, photo, user, date) VALUES (?, ?, ?, ?)',
            (
            text, filename, user, new_date))  # Используем new_date вместо date
        db.commit()

    db = get_db()

    messages = db.execute('SELECT * FROM messages').fetchall()
    messages = [
        Message(row['id'], row['text'], row['photo'], row['user'],
                (datetime.strptime(row['date'],
                                   "%Y-%m-%d %H:%M:%S.%f") + timedelta(
                    hours=3)).strftime("%H:%M:%S %d-%m-%Y"))
        for row in messages
    ]

    return render_template('main.html', messages=messages)


@app.route('/add_message', methods=['GET', 'POST'])
def add_message():
    if request.method == 'POST':
        text = request.form.get('text')
        user = "Опубликовано"
        date = datetime.now()

        db = get_db()
        photo = request.files.get('photo')
        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            max_width = 1000
            image = Image.open(photo)
            image.thumbnail((max_width, max_width))
            image.save(os.path.join(app.static_folder, 'photos', filename))
        else:
            filename = None

        db.execute(
            'INSERT INTO messages (text, photo, user, date) VALUES (?, ?, ?, ?)',
            (text, filename, user, date))

        db.commit()
        return redirect(url_for('home'))

    return render_template('add_message.html')


@app.route('/edit_message/<int:message_id>', methods=['GET', 'POST'])
def edit_message(message_id):
    if request.method == 'POST':
        text = request.form.get('text')
        user = "Отредактировано"
        date = datetime.now()

        db = get_db()
        message = db.execute(
            'SELECT * FROM messages WHERE id=?', (message_id,)
        ).fetchone()
        filename = message['photo']

        new_photo = request.files.get('photo')
        if new_photo and new_photo.filename != '':
            filename = secure_filename(new_photo.filename)
            max_width = 1000
            image = Image.open(new_photo)
            image.thumbnail((max_width, max_width))
            image.save(os.path.join(app.static_folder, 'photos', filename))

        db.execute(
            'UPDATE messages SET text=?, photo=?, user=?, date=? WHERE id=?',
            (text, filename, user, date, message_id))

        db.commit()
        return redirect(url_for('home'))

    db = get_db()
    message = db.execute(
        'SELECT * FROM messages WHERE id=?', (message_id,)
    ).fetchone()

    date = datetime.now()  # добавляем определение переменной date здесь

    message = Message(message['id'], message['text'], message['photo'],
                      message['user'], date.strftime("%Y-%m-%d %H:%M:%S"))

    return render_template('edit_message.html', message=message)


@app.route('/delete_message/<int:message_id>', methods=['GET', 'POST'])
def delete_message(message_id):
    db = get_db()
    db.execute('DELETE FROM messages WHERE id=?', (message_id,))
    db.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(port=5656, debug=True)
