import datetime
import uuid
from typing import Any, Dict, Union
from flask import jsonify, request, current_app, Response
from flask_restx import Namespace, Resource, fields
from flask_mail import Message
from utils import connect_db  # Adjust imports based on your project structure

contact_ns: Namespace = Namespace('contactus', description='Contact form submission operations')

contact_model = contact_ns.model('Contact', {
    'name': fields.String(required=True, description='The name of the person submitting the form'),
    'email': fields.String(required=True, description='The email address of the person submitting the form'),
    'message': fields.String(required=True, description='The message content from the person submitting the form'),
})

def get_current_utc_time() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

@contact_ns.route('/contact')
class ContactSubmit(Resource):
    @contact_ns.marshal_list_with(contact_model)
    def post(self) -> Union[Response, Any]:
        try:
            data: Dict[str, str] = request.get_json() if request.is_json else request.form.to_dict()

            name: str = data.get('name', '')
            email: str = data.get('email', '')
            message: str = data.get('message', '')

            if not name or not email or not message:
                raise ValueError("Name, Email, or Message is missing")

            conn = connect_db()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO contact (email, message, uuid, contact_timestamp)
                VALUES (%s, %s, %s, %s)
            """, (email, message, str(uuid.uuid4()), get_current_utc_time()))

            conn.commit()
            cur.close()
            conn.close()

            mail = current_app.extensions.get('mail')
            if not mail:
                raise Exception("Mail extension is not initialized")

            contact_email = current_app.config.get('MAIL_DEFAULT_SENDER')
            if not contact_email:
                raise ValueError("MAIL_DEFAULT_SENDER is not set in configuration")

            # Send email to the configured contact email
            msg = Message(
                subject='Your Message has been received, we will get back to you in a moment',
                recipients=[contact_email],
                body=f'Name: {name}\nEmail: {email}\nMessage:\n{message}'
            )
            mail.send(msg)

            # Send confirmation email to the submitter
            confirm_msg = Message(
                subject='Thank you for your message',
                recipients=[email],
                body=f'Thank you {name},\n\nWe have received your message and will get back to you shortly.\n\nYour message:\n{message}'
            )
            mail.send(confirm_msg)

            current_app.logger.info("Contact form submitted successfully by: %s", email)

            response = jsonify({"message": "Contact form submitted successfully"})
            response.status_code = 201
            return response

        except ValueError as ve:
            current_app.logger.error("ValueError: %s", str(ve))
            response = jsonify({"error": str(ve)})
            response.status_code = 400
            return response
        except Exception as e:
            current_app.logger.exception("An error occurred during contact form submission processing")
            response = jsonify({"error": "An unexpected error occurred"})
            response.status_code = 500
            return response

@contact_ns.route('/messages')
class GetMessages(Resource):
    def get(self):
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT uuid, email, message, contact_timestamp FROM contact ORDER BY contact_timestamp DESC")
            messages = cur.fetchall()
            cur.close()
            conn.close()

            result = [
                {
                    "uuid": str(row[0]),
                    "email": row[1],
                    "message": row[2],
                    "contact_timestamp": row[3].isoformat()
                } for row in messages
            ]
            return jsonify(result)
        except Exception as e:
            current_app.logger.exception("Failed to fetch messages")
            return jsonify({"error": "Failed to fetch messages"}), 500

@contact_ns.route('/message/<string:message_id>')
class DeleteMessage(Resource):
    def delete(self, message_id):
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM contact WHERE uuid = %s", (message_id,))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"message": "Message deleted successfully"})
        except Exception as e:
            current_app.logger.exception("Failed to delete message")
            return jsonify({"error": "Failed to delete message"}), 500
