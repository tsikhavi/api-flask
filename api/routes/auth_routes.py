from flask import jsonify, make_response, request, current_app
from flask_restx import Namespace, Resource, fields
from flask_mail import Message
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import psycopg2
from utils import connect_db, check_password, hash_password
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os

auth_ns = Namespace('auth', description='Authentication related operations')

login_model = auth_ns.model('Login', {
    'emailOrPhone': fields.String(required=True, description='Email or phone number of the user'),
    'password': fields.String(required=True, description='Password of the user')
})

@auth_ns.route('/login')
class LoginUser(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        try:
            data = request.get_json()
            current_app.logger.debug(f"Login data received: {data}")
            email_or_phone = data['emailOrPhone']
            password = data['password']

            conn = connect_db()
            cur = conn.cursor()

            cur.execute("SELECT * FROM userinfo1 WHERE email = %s OR phone_number = %s", (email_or_phone, email_or_phone))
            user = cur.fetchone()
            current_app.logger.debug(f"User fetched from database: {user}")

            if not user:
                current_app.logger.warning("Invalid email/phone number")
                return make_response(jsonify({"error": "Invalid email/phone number"}), 401)

            if user[6] != '1':
                current_app.logger.warning("Account not verified")
                return make_response(jsonify({"error": "Account not verified. Please confirm your account using the instructions sent to your email."}), 403)

            current_app.logger.debug(f"Hashed password in DB: {user[4]}")
            if check_password(password, user[4]):
                current_app.logger.debug("Invalid password")
                return make_response(jsonify({"error": "Invalid password"}), 401)

            cur.close()
            conn.close()

            access_token = create_access_token(identity=user[0])
            current_app.logger.debug(f"Access token created: {access_token}")

            mail = current_app.extensions.get('mail')
            if mail:
                msg = Message(
                    subject='Login Confirmation',
                    recipients=[user[2]],
                    body='You have successfully logged in!'
                )
                mail.send(msg)
                current_app.logger.info("Login confirmation email sent successfully to: %s", user[2])
            else:
                current_app.logger.warning("Mail extension not found in app context")

            response_data = {"message": "Login successful", "access_token": access_token}
            resp = make_response(jsonify(response_data), 200)

            theme_cookie_value = 'light'
            expires_date = datetime.utcnow() + timedelta(days=365)
            resp.set_cookie('theme', value=theme_cookie_value, httponly=True, path='/', max_age=60*60*24*365, expires=expires_date)
            resp.set_cookie('session', value=access_token, httponly=True, path='/', max_age=60*60*24*365, expires=expires_date)

            current_app.logger.debug(f"Response prepared with cookies: {resp.headers.get('Set-Cookie')}")

            return resp

        except KeyError as key_error:
            current_app.logger.error(f"KeyError during login: {str(key_error)}")
            return make_response(jsonify({"error": "Invalid request format. Missing required field."}), 400)

        except Exception as error:
            current_app.logger.error(f"Error during login: {str(error)}")
            return make_response(jsonify({"error": "An internal error occurred. Please try again later."}), 500)

@auth_ns.route('/logout')
class LogoutUser(Resource):
    @jwt_required() 
    def post(self):
        try:
            cookies_to_clear = ['theme', 'session']
            resp = make_response(jsonify({"message": "Logout successful"}), 200)
            for cookie in cookies_to_clear:
                resp.set_cookie(cookie, '', expires=0)
            current_app.logger.debug(f"Cookies cleared: {cookies_to_clear}")
            return resp

        except Exception as error:
            current_app.logger.error(f"Error during logout: {str(error)}")
            return jsonify({"error": str(error)}), 500


password_change_model = auth_ns.model('PasswordChange', {
    'email': fields.String(required=True, description='The email of the user'),
    'current_password': fields.String(required=True, description='The current password of the user'),
    'new_password': fields.String(required=True, description='The new password of the user'),
})

@auth_ns.route('/passwordchange')
class PasswordChange(Resource):
    @auth_ns.expect(password_change_model)
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            email = data['email']
            current_password = data['current_password']
            new_password = data['new_password']
            current_app.logger.debug(f"Password change request received: {data}")

            user_id = get_jwt_identity()
            current_app.logger.debug(f"User ID from JWT: {user_id}")

            conn = connect_db()
            cur = conn.cursor()

            cur.execute("SELECT password FROM userinfo1 WHERE email = %s", (email,))
            user = cur.fetchone()
            current_app.logger.debug(f"User fetched from database for password change: {user}")

            if not user or not check_password(current_password, user[0]):
                current_app.logger.warning("Invalid current password")
                return jsonify({"error": "Invalid current password"}), 401

            new_password_hashed = hash_password(new_password)
            cur.execute("UPDATE userinfo1 SET password = %s WHERE email = %s", (new_password_hashed, email))

            conn.commit()
            cur.close()
            conn.close()

            current_app.logger.debug(f"Password changed successfully for email: {email}")
            return jsonify({"message": "Password changed successfully"}), 200

        except Exception as error:
            current_app.logger.error(f"Error during password change: {str(error)}")
            return jsonify({"error": str(error)}), 500

delete_model = auth_ns.model('DeleteUser', {
    'password': fields.String(required=True, description='Password of the user')
})

@auth_ns.route('/delete')
class DeleteAccount(Resource):
    @auth_ns.expect(delete_model)
    @jwt_required()
    def delete(self):
        try:
            data = request.get_json()
            user_id = get_jwt_identity()
            password = data.get('password')
            
            if not password:
                current_app.logger.warning(f"User {user_id} did not provide a password for deletion.")
                return make_response(jsonify({"error": "Password is required"}), 400)

            conn = connect_db()
            cur = conn.cursor()
            
            cur.execute("SELECT password FROM userinfo1 WHERE id = %s", (user_id,))
            user = cur.fetchone()
            
            if not user:
                current_app.logger.warning(f"User {user_id} not found in the database.")
                return make_response(jsonify({"error": "User not found"}), 404)

            if not check_password(password, user[0]):
                current_app.logger.warning(f"User {user_id} provided an invalid password.")
                return make_response(jsonify({"error": "Invalid password"}), 401)
            
            cur.execute("DELETE FROM userinfo1 WHERE id = %s", (user_id,))
            conn.commit()
            
            cur.close()
            conn.close()
            
            current_app.logger.info(f"User {user_id} deleted their account successfully.")
            return jsonify({"message": "Account deleted successfully"}), 200

        except psycopg2.Error as db_error:
            current_app.logger.error(f"Database error during account deletion for user {user_id}: {str(db_error)}")
            return make_response(jsonify({"error": "A database error occurred. Please try again later."}), 500)
        
        except Exception as error:
            current_app.logger.error(f"Error during account deletion for user {user_id}: {str(error)}")
            return make_response(jsonify({"error": "An internal error occurred. Please try again later."}), 500)

@auth_ns.route('/profile/upload')
class FileUpload(Resource):
    @jwt_required() 
    def post(self):
        print('Received file upload request')
        if 'file' not in request.files:
            print('No file part in request')
            return make_response(jsonify({"error": "No file part"}), 400)
        file = request.files['file']
        if file.filename == '':
            print('No selected file in request')
            return make_response(jsonify({"error": "No selected file"}), 400)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            print(f'File saved to {filepath}')

            conn = connect_db()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO files (filename, filepath) VALUES (%s, %s)", (filename, filepath))
                conn.commit()
                print('File details saved to database')
            finally:
                cur.close()
                conn.close()

            return make_response(jsonify({"message": "File uploaded successfully"}), 201)
