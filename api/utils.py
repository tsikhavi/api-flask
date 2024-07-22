import datetime
import os
import bcrypt
from flask_socketio import emit
import psycopg2
import uuid
from flask import Config, current_app
import logging
from logging.handlers import RotatingFileHandler
from config import Config



def setup_logging(app):
    if not app.debug:
        log_dir = os.path.join(app.config['logs'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = RotatingFileHandler(os.path.join(log_dir, 'sautis.log'), maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('Sautis startup')


def register_socketio_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('message', {'data': 'Connected'})

    @socketio.on('message')
    def handle_message(data):
        print('Received message:', data)
        email = data.get('email')
        message = data.get('message')
        if email and message:
            message_id = str(uuid.uuid4())
            timestamp = datetime.datetime.utcnow()

            conn = connect_db()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO messages (uuid, email, content, timestamp) VALUES (%s, %s, %s, %s)",
                            (message_id, email, message, timestamp))
                conn.commit()
                print('Message saved to database')
            finally:
                cur.close()
                conn.close()

            emit('message', {'email': email, 'message': message}, broadcast=True)
        else:
            print('Invalid message format')
            emit('message_error', {'error': 'Invalid message format'}, broadcast=True)

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def check_password(password: str, hashed: str) -> bool:
    password = password.strip()
    logging.debug(f"Checking password: {password} against hashed: {hashed}")
    try:
        result = bcrypt.checkpw(password.encode(), hashed.encode())
        logging.debug(f"Password match result: {result}")
        return result
    except Exception as error:
        logging.error(f"Error in check_password: {error}")
        raise

def connect_db():
    print(f"Connecting to database {Config.DB_NAME} on {Config.DB_HOST}:{Config.DB_PORT} as user {Config.DB_USER}")
    try:
        conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
        print("Successfully connected to the database")
        return conn
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        raise

def user_exists(cur, email):
    cur.execute("SELECT EXISTS(SELECT 1 FROM userinfo1 WHERE email = %s)", (email,))
    return cur.fetchone()[0]

def phone_exists(cur, phone_number):
    cur.execute("SELECT 1 FROM userinfo1 WHERE phone_number = %s", (phone_number,))
    return cur.fetchone() is not None

def create_user(cur, name, email, phone_number, password, token):
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(password)
    cur.execute("""
        INSERT INTO userinfo1 (id, name, email, phone_number, password, token)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, name, email, phone_number, hashed_password, token))


def initialize_db():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS userinfo1 (
            id UUID PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            phone_number VARCHAR(15),
            password VARCHAR(60),
            token VARCHAR(100),
            verified VARCHAR(1) DEFAULT '0' NOT NULL CHECK (verified IN ('0', '1')),
            profile_image TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blacklist_tokens (
            id SERIAL PRIMARY KEY,
            token TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id UUID PRIMARY KEY,
            email VARCHAR(100) UNIQUE,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    users = [
        ("John Doe", "john@example.com", "1234567890", hash_password("password123")),
        ("Jane Smith", "jane@example.com", "9876543210", hash_password("password456")),
        ("Jane Smith", "janes@example.com", "9876548900", hash_password("password789"))
    ]
    for name, email, phone_number, password in users:
        if not user_exists(cur, email):
            create_user(cur, name, email, phone_number, password, token=str(uuid.uuid4()))
    conn.commit()
    cur.close()
    conn.close()

def subscribe_user(cur, email):
    subscription_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO subscriptions (id, email)
        VALUES (%s, %s)
    """, (subscription_id, email))

def unsubscribe_user(cur, email):
    cur.execute("DELETE FROM subscriptions WHERE email = %s", (email,))

def set_cookies(resp, cookies):
    for key, value in cookies.items():
        current_app.logger.debug(f"Setting cookie: {key} = {value}")
        resp.headers.add('Set-Cookie', f"{key}={value}")

    return resp


def generate_magic_link(token):
    magic_link = f"http://localhost:3000/confirm/{token}"
    return magic_link

def update_user_registration_status(token):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE userinfo1 SET verified = '1' WHERE token = %s", (token,))
        conn.commit()
        cur.close()
        conn.close()
        current_app.logger.info("User registration status updated successfully for token: %s", token)
        return True
    except Exception as e:
        current_app.logger.error("Error updating user registration status: %s", str(e))
        return False

def add_to_blacklist(token):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO blacklist_tokens (token) VALUES (%s)", (token,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        current_app.logger.error("Error adding token to blacklist: %s", str(e))
