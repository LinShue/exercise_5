import logging
import string
import traceback
import random
import sqlite3
from datetime import datetime
from flask import * # Flask, g, redirect, render_template, request, url_for
from functools import wraps

app = Flask(__name__)

# These should make it so your Flask app always returns the latest version of
# your HTML, CSS, and JS files. We would remove them from a production deploy,
# but don't change them here.
app.debug = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache"
    return response



def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect('db/watchparty.sqlite3')
        db.row_factory = sqlite3.Row
        setattr(g, '_database', db)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    print("query_db")
    print(cursor)
    rows = cursor.fetchall()
    print(rows)
    db.commit()
    cursor.close()
    if rows:
        if one: 
            return rows[0]
        return rows
    return None

def new_user():
    name = "Unnamed User #" + ''.join(random.choices(string.digits, k=6))
    password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    api_key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=40))
    u = query_db('insert into users (name, password, api_key) ' + 
        'values (?, ?, ?) returning id, name, password, api_key',
        (name, password, api_key),
        one=True)
    return u

def get_user_from_cookie(request):
    user_id = request.cookies.get('user_id')
    password = request.cookies.get('user_password')
    if user_id and password:
        return query_db('select * from users where id = ? and password = ?', [user_id, password], one=True)
    return None

def render_with_error_handling(template, **kwargs):
    try:
        return render_template(template, **kwargs)
    except:
        t = traceback.format_exc()
        return render_template('error.html', args={"trace": t}), 500

# ------------------------------ NORMAL PAGE ROUTES ----------------------------------

@app.route('/')
def index():
    print("index") # For debugging
    user = get_user_from_cookie(request)

    if user:
        rooms = query_db('select * from rooms')
        return render_with_error_handling('index.html', user=user, rooms=rooms)
    
    return render_with_error_handling('index.html', user=None, rooms=None)

@app.route('/rooms/new', methods=['GET', 'POST'])
def create_room():
    print("create room") # For debugging
    user = get_user_from_cookie(request)
    if user is None: return {}, 403

    if (request.method == 'POST'):
        name = "Unnamed Room " + ''.join(random.choices(string.digits, k=6))
        room = query_db('insert into rooms (name) values (?) returning id', [name], one=True)            
        return redirect(f'{room["id"]}')
    else:
        return app.send_static_file('create_room.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("signup")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/profile')
        # return render_with_error_handling('profile.html', user=user) # redirect('/')
    
    if request.method == 'POST':
        u = new_user()
        print(u)
        for key in u.keys():
            print(f'{key}: {u[key]}')

        resp = redirect('/profile')
        resp.set_cookie('user_id', str(u['id']))
        resp.set_cookie('user_password', u['password'])
        return resp
    
    return redirect('/login')

@app.route('/profile')
def profile():
    print("profile")
    user = get_user_from_cookie(request)
    if user:
        return render_with_error_handling('profile.html', user=user)
    redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("login")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/')
    
    if request.method == 'POST':
        name = request.form['username']
        password = request.form['password']
        u = query_db('select * from users where name = ? and password = ?', [name, password], one=True)
        if u:
            resp = make_response(redirect("/"))
            resp.set_cookie('user_id', str(u['id']))
            resp.set_cookie('user_password', u['password'])
            return resp

    return render_with_error_handling('login.html', failed=True)   

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('user_id', '')
    resp.set_cookie('user_password', '')
    return resp

@app.route('/rooms/<int:room_id>')
def room(room_id):
    user = get_user_from_cookie(request)
    if user is None: return redirect('/')
    room = query_db('select * from rooms where id = ?', [room_id], one=True)
    return render_with_error_handling('room.html',
            room=room, user=user)

# -------------------------------- API ROUTES ----------------------------------

# POST to change the user's name
@app.route('/api/user/name', methods=['POST'])
def update_username():
    api_key = request.headers.get('X-API-Key')
    user = query_db('select * from users where api_key = ?', [api_key], one=True)
    if not user:
        return jsonify({"error": "Invalid or missing API key"}), 403
    # print("request data: ", request.json)
    new_name = request.json.get('name')
    # print('new_name:', new_name)
    if not new_name:
        return jsonify({"error": "New name is required"}), 400
    # print("api_key: ", api_key)
    query_db('update users set name = ? where id = ?', [new_name, user['id']])
    return jsonify({"message": "Username updated successfully"}), 200

# POST to change the user's password
@app.route('/api/user/password', methods=['POST'])
def update_password():
    api_key = request.headers.get('X-API-Key')
    user = query_db('select * from users where api_key = ?', [api_key], one=True)
    if not user:
        return jsonify({"error": "Invalid or missing API key"}), 403
    # print("request data: ", request.json)
    new_password = request.json.get('password')
    query_db('update users set password = ? where id = ?', [new_password, user['id']])
    return jsonify({"message": "Password updated successfully"}), 200

# POST to change the name of a room
@app.route('/api/rooms/<int:room_id>/name', methods=['POST'])
def update_room_name(room_id):
    api_key = request.headers.get('X-API-Key')
    user = query_db('select * from users where api_key = ?', [api_key], one=True)
    if not user:
        return jsonify({"error": "Invalid or missing API key"}), 403
    # print("Request: ", request.json)
    new_name = request.json.get('name')
    # print("new_name",new_name)
    # print("room_id", room_id)
    query_db('update rooms set name = ? where id = ?', [new_name, room_id])
    return jsonify({"message": "Room name updated successfully"}), 200

# GET to get all the messages in a room
@app.route('/api/rooms/<int:room_id>/messages', methods=['GET'])
def get_messages(room_id):
    api_key = request.headers.get('X-API-Key')
    if not api_key or not query_db('select * from users where api_key = ?', [api_key], one=True):
        return jsonify({"error": "Invalid or missing API key"}), 403
    
    messages = query_db('select m.*, u.name as user_name from messages m join users u on m.user_id = u.id where m.room_id = ?', [room_id])
    return jsonify([{"id": msg["id"], "user_name": msg["user_name"], "body": msg["body"]} for msg in messages])

# POST to post a new message to a room
@app.route('/api/rooms/<int:room_id>/messages', methods=['POST'])
def post_message(room_id):
    api_key = request.headers.get('X-API-Key')
    user = query_db('select * from users where api_key = ?', [api_key], one=True)
    if not user:
        return jsonify({"error": "Invalid or missing API key"}), 403
    body = request.json.get('body')
    query_db('insert into messages (user_id, room_id, body) values (?, ?, ?)', [user['id'], room_id, body])
    return jsonify({"message": "Message posted successfully"}), 201

