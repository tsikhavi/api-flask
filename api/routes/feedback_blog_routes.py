from flask import jsonify, request, current_app
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import connect_db

feedback_ns = Namespace('feedback', description='Feedback related operations')

feedback_model = feedback_ns.model('Feedback', {
    'blog_id': fields.String(required=True, description='ID of the blog post'),
    'like': fields.Boolean(required=False, description='Whether the user liked the post'),
    'dislike': fields.Boolean(required=False, description='Whether the user disliked the post'),
    'error': fields.Boolean(required=False, description='Whether the user found an error in the post'),
    'comment': fields.String(required=False, description='User comment on the post')
})

@feedback_ns.route('/feedback-blog')
class FeedbackBlog(Resource):
    @feedback_ns.expect(feedback_model)
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            blog_id = data['blog_id']
            like = data.get('like', False)
            dislike = data.get('dislike', False)
            error = data.get('error', False)
            comment = data.get('comment', None)
            user_id = get_jwt_identity()

            conn = connect_db()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO feedback_blog (blog_id, user_id, like, dislike, error, comment)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (blog_id, user_id, like, dislike, error, comment))

            feedback_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"message": "Feedback submitted successfully", "feedback_id": feedback_id}), 200

        except Exception as e:
            current_app.logger.error("Error submitting feedback: %s", str(e))
            return jsonify({"error": "An unexpected error occurred"}), 500


