import os
import uuid
from flask import request, current_app, jsonify
from flask_restx import Namespace, Resource, fields
from flask_mail import Message
from typing import Dict, Any
from utils import connect_db, user_exists, phone_exists, create_user, hash_password, generate_magic_link, update_user_registration_status

registration_ns = Namespace('registration', description='User registration operations')

# Define the user model for registration
user_model = registration_ns.model('User', {
    'name': fields.String(required=True, description='User name'),
    'email': fields.String(required=True, description='User email address'),
    'phone_number': fields.String(required=True, description='User phone number'),
    'password': fields.String(required=True, description='User password'),
})

@registration_ns.route('/register')
class RegisterUser(Resource):
    @registration_ns.expect(user_model, validate=True)
    def post(self) -> Dict[str, Any]:
        try:
            data = request.get_json()
            name = data['name']
            email = data['email']
            phone_number = data['phone_number']
            password = data['password']

            # Validate password (example: minimum length)
            if len(password) < 8:
                return {"error": "Password must be at least 8 characters long"}, 400

            conn = connect_db()
            cur = conn.cursor()

            if user_exists(cur, email):
                return {"error": "User with this email already exists"}, 400

            if phone_exists(cur, phone_number):
                return {"error": "User with this phone number already exists"}, 400

            token = str(uuid.uuid4())  # Generate a unique token
            hashed_password = hash_password(password)
            create_user(cur, name, email, phone_number, hashed_password, token)  # Pass token to create_user

            conn.commit()
            cur.close()
            conn.close()

            # Generate and send magic link via email
            magic_link = generate_magic_link(token)

            # Fetch frontend base URL from environment variable
            frontend_base_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')

            # Construct the confirmation URL
            confirmation_url = f'{frontend_base_url}/confirm/{token}'

            app = current_app._get_current_object()  # Access Flask app instance
            mail = registration_ns.context['mail']  # Access mail instance
            msg = Message(
                subject='Confirm Registration',
                recipients=[email],
                body=f'Click the following link to confirm your registration: {confirmation_url}'
            )
            mail.send(msg)
            app.logger.info("Magic link sent successfully to: %s", email)

            return {"message": "User registered successfully. Check your email for confirmation instructions."}, 201

        except KeyError as e:
            return {"error": f"Missing key in request data: {str(e)}"}, 400

        except Exception as e:
            current_app.logger.error("Error during registration: %s", str(e))
            return {"error": str(e)}, 500

@registration_ns.route('/confirm/<token>')
class ConfirmRegistration(Resource):
    def get(self, token: str) -> Dict[str, Any]:
        try:
            if update_user_registration_status(token):
                return {"message": "Registration confirmed successfully!"}, 200
            else:
                return {"error": "Error confirming registration. Please try again later."}, 500

        except Exception as e:
            current_app.logger.error("Error confirming registration: %s", str(e))
            return {"error": f"Error confirming registration: {str(e)}"}, 500

@registration_ns.route('/resend/<token>', methods=['POST'])
class ResendConfirmationEmail(Resource):
    def post(self, token: str) -> Dict[str, Any]:
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT email FROM userinfo1 WHERE token = %s", (token,))
            user = cur.fetchone()

            if not user:
                return {"error": "Invalid token"}, 400

            frontend_base_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')

            email = user[0]
            confirmation_url = f'{frontend_base_url}/confirm/{token}'
            mail = registration_ns.context['mail']  # Access mail instance
            msg = Message(
                subject='Confirm Registration',
                recipients=[email],
                body=f'Click the following link to confirm your registration: {confirmation_url}'
            )
            mail.send(msg)
            return {"message": "Confirmation email resent successfully!"}, 200

        except Exception as e:
            current_app.logger.error("Error resending confirmation email: %s", str(e))
            return {"error": f"Error resending confirmation email: {str(e)}"}, 500
