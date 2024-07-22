from flask import jsonify, request, current_app
from flask_restx import Namespace, Resource
from flask_mail import Message
from utils import connect_db, subscribe_user, unsubscribe_user
import re
import nh3

subscription_ns = Namespace('subscription', description='Subscription related operations')

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def sanitize_feedback(feedback):
    return nh3.clean(
        feedback,
        tags=set(),  # No tags allowed
        attributes={},  # No attributes allowed
        strip_comments=True,  # Strip comments
        link_rel='noopener noreferrer'  # Add security features to links
    )


@subscription_ns.route('/subscribe')
class Subscribe(Resource):
    def post(self):
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()

            email = data.get('email')
            if not email or not validate_email(email):
                raise ValueError("Email address is missing or invalid")

            conn = connect_db()
            cur = conn.cursor()

            subscribe_user(cur, email)
            conn.commit()
            cur.close()
            conn.close()

            mail = current_app.extensions.get('mail')
            if not mail:
                raise Exception("Mail extension is not initialized")

            unsubscribe_link = f'http://localhost:3000/unsubscribe?email={email}'
            msg = Message(
                subject='Subscription Confirmation',
                recipients=[email],
                body=f'Thank you for subscribing. If you wish to unsubscribe, click here: {unsubscribe_link}'
            )
            mail.send(msg)
            current_app.logger.info("Email sent successfully to: %s", email)

            response = jsonify({"message": "Subscribed successfully"})
            response.status_code = 201
            return response

        except ValueError as ve:
            response = jsonify({"error": str(ve)})
            response.status_code = 400
            return response
        except Exception as e:
            current_app.logger.exception("An error occurred during subscription processing")
            response = jsonify({"error": "An unexpected error occurred"})
            response.status_code = 500
            return response

@subscription_ns.route('/unsubscribe')
class Unsubscribe(Resource):
    def post(self):
        try:
            data = request.get_json()
            email = data.get('email')
            feedback = data.get('feedback', '')

            if not email or not validate_email(email):
                raise ValueError("Email address is missing or invalid")

            feedback = sanitize_feedback(feedback)

            conn = connect_db()
            cur = conn.cursor()

            # Check if the email is in the subscriptions table
            cur.execute("SELECT 1 FROM subscriptions WHERE email = %s", (email,))
            if not cur.fetchone():
                response = jsonify({"error": "Email address is not subscribed"})
                response.status_code = 400
                return response

            # Unsubscribe the user
            unsubscribe_user(cur, email)
            conn.commit()
            cur.close()
            conn.close()

            if feedback:
                conn = connect_db()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO feedback (email, feedback) VALUES (%s, %s)",
                    (email, feedback)
                )
                conn.commit()
                cur.close()
                conn.close()

            current_app.logger.info("Unsubscribed successfully: %s", email)

            response = jsonify({"message": "Unsubscribed successfully"})
            response.status_code = 200
            return response

        except ValueError as ve:
            response = jsonify({"error": str(ve)})
            response.status_code = 400
            return response
        except Exception as e:
            current_app.logger.exception("An error occurred during unsubscription processing")
            response = jsonify({"error": "An unexpected error occurred"})
            response.status_code = 500
            return response
