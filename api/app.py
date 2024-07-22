import os
from flask import Flask
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_restx import Api
from flask_socketio import SocketIO
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_cors import CORS
from config import Config
from models import db  # Assuming you have a models module where your SQLAlchemy db instance is defined
from routes import initialize_routes
from utils import register_socketio_events, setup_logging
#from OpenSSL import SSL

load_dotenv()  # Load environment variables from .env file

mail = Mail()
jwt = JWTManager()
api = Api(version='1.0', title='Python backend API', description='Sautis API for frontend React')
socketio = SocketIO(cors_allowed_origins="*")
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'UPLOAD_FOLDER')
    app.config['logs'] = os.path.join(os.path.dirname(__file__), 'logs')
    app.config['DEBUG'] = False  # Enable debug mode
    app.config['SECRET_KEY'] = '825-647-297'
    #app.config['SSL'] = True  # Flag to enable SSL/TLS

    # SSL context configuration using pyOpenSSL
    #context = SSL.Context(SSL.SSLv23_METHOD)
    #context.use_privatekey_file(os.path.join(os.path.dirname(__file__), 'ssl', 'key.pem'))
    #context.use_certificate_file(os.path.join(os.path.dirname(__file__), 'ssl', 'cert.pem'))

    # Attach SSL context to the app
    #app.ssl_context = context

    CORS(app)  # Enable CORS for all routes

    mail.init_app(app)
    jwt.init_app(app)
    api.init_app(app)
    socketio.init_app(app, ssl_context='adhoc')  # Use 'adhoc' for development, replace with app.ssl_context for production
    db.init_app(app)
    migrate.init_app(app, db)

    # Pass app and mail to initialize_routes
    initialize_routes(api, app, mail)
    register_socketio_events(socketio)

    # Set up logging
    setup_logging(app)

    return app

# Ensure the app is created
app = create_app()

# Run the Flask application
if __name__ == '__main__':
    socketio.run(app, debug=False)
