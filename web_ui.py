from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
import signal
import threading
import sys
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bean_genie_bot import process_command

app = Flask(__name__)
app.secret_key = os.urandom(24)

# In-memory user store for demo purposes
users = {}

# Database setup
DATABASE = 'chat_memory.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            sender TEXT NOT NULL,
            message_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('chat.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password"
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            error = "Username already exists"
            return render_template('register.html', error=error)
        users[username] = {
            'password': generate_password_hash(password)
        }
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

def save_message(username, sender, message_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO messages (username, sender, message_text, timestamp) VALUES (?, ?, ?, ?)',
        (username, sender, message_text, datetime.utcnow())
    )
    conn.commit()
    conn.close()

def get_recent_messages(username, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT sender, message_text FROM messages WHERE username = ? ORDER BY timestamp DESC LIMIT ?',
        (username, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    # Return messages in chronological order
    return rows[::-1]

@app.route('/api/message', methods=['POST'])
def message():
    if 'username' not in session:
        return jsonify({'reply': 'Please log in to chat.'})
    username = session['username']
    user_message = request.json.get('message', '')

    # Save user message
    save_message(username, 'user', user_message)

    # Retrieve recent conversation history
    history_rows = get_recent_messages(username)
    conversation_history = []
    for row in history_rows:
        conversation_history.append({'sender': row['sender'], 'message': row['message_text']})

    # Pass conversation history to process_command (assuming it can accept context)
    # For now, we will concatenate history as a string for context
    context_text = ''
    for msg in conversation_history:
        prefix = 'User: ' if msg['sender'] == 'user' else 'Bot: '
        context_text += prefix + msg['message'] + '\n'
    context_text += 'User: ' + user_message + '\n'

    # Pass conversation history to process_command to maintain context
    response = process_command(user_message, conversation_history=context_text)

    # Save bot response
    save_message(username, 'bot', response)

    try:
        response_data = json.loads(response)
        if 'response' in response_data:
            bot_reply = response_data['response']
        elif 'error' in response_data:
            bot_reply = f"Error: {response_data['error']}"
        else:
            bot_reply = response
    except Exception:
        bot_reply = response
    return jsonify({'reply': bot_reply})

def shutdown_server():
    """Function to shutdown the Flask server"""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/restart', methods=['POST'])
def restart():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    # Optionally, add more authorization checks here (e.g., admin user)
    def restart_server():
        shutdown_server()
        # Relaunch the server process - this requires the app to be run via a script that restarts on exit
        # Here we just exit; an external process manager should restart the app
        os._exit(0)
    threading.Thread(target=restart_server).start()
    return jsonify({'message': 'Server is restarting...'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
