from flask import current_app, jsonify, request
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import connect_db

user_ns = Namespace('user', description='User related operations')

@user_ns.route('/userinfo')
class UserInfo(Resource):
    @jwt_required()
    def get(self):
        try:
            user_id = get_jwt_identity()
            current_app.logger.info(f"Fetching info for user_id: {user_id}")

            conn = connect_db()
            cur = conn.cursor()

            cur.execute("SELECT id, name, email, phone_number, token, verified FROM userinfo1 WHERE id = %s", (user_id,))
            user = cur.fetchone()

            cur.close()
            conn.close()

            if user:
                user_id, name, email, phone_number, token, verified = user
                current_app.logger.info(f"User found: {user}")
                return jsonify({
                    "user_id": user_id,
                    "name": name,
                    "email": email,
                    "phone_number": phone_number,
                    "token": token,
                    "verified": verified
                })
            else:
                current_app.logger.warning(f"User not found for user_id: {user_id}")
                return jsonify({"error": "User not found"}), 404

        except Exception as e:
            current_app.logger.error(f"Error fetching user info: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500




@user_ns.route('/get_token_by_email')
class GetTokenByEmail(Resource):
    def post(self):
        try:
            data = request.get_json()
            email = data.get('email')

            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT token FROM userinfo1 WHERE email = %s", (email,))
            token = cur.fetchone()

            cur.close()
            conn.close()

            if token:
                return jsonify({"token": token[0]})
            else:
                return jsonify({"error": "User not found"}), 404

        except Exception as e:
            current_app.logger.error("Error fetching token by email: %s", str(e))
            return jsonify({"error": "An unexpected error occurred"}), 500
