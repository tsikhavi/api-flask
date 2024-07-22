import datetime
from flask import jsonify, request
from flask_restx import Namespace, Resource, fields
from utils import connect_db

blog_ns = Namespace('blog', description='Blog operations')

# Define the model for the Blog
blog_model = blog_ns.model('Blog', {
    'title': fields.String(required=True, description='The title of the blog post'),
    'image': fields.String(required=True, description='The URL link to the blog post image'),
    'author': fields.String(required=True, description='The author of the blog post'),
    'date': fields.String(required=True, description='The publication date of the blog post'),
    'intro': fields.String(required=True, description='The introduction of the blog post'),
    'content_section': fields.String(required=True, description='The content section of the blog post'),
    'list': fields.List(fields.String, description='A list of additional content for the blog post'),
    'conclusion': fields.String(required=True, description='The conclusion of the blog post'),
    'views': fields.Integer(description='The number of views of the blog post')
})

@blog_ns.route('/blog')
class BlogList(Resource):
    @blog_ns.marshal_list_with(blog_model)
    def get(self):
        try:
            query = request.args.get('query', '')
            conn = connect_db()
            cur = conn.cursor()
            if query:
                cur.execute("""
                    SELECT title, image, author, date, intro, content_section, list, conclusion, views 
                    FROM blog 
                    WHERE title ILIKE %s 
                    OR author ILIKE %s 
                    OR intro ILIKE %s
                """, (f'%{query}%', f'%{query}%', f'%{query}%'))
            else:
                cur.execute("SELECT title, image, author, date, intro, content_section, list, conclusion, views FROM blog")

            blogs = cur.fetchall()
            cur.close()
            conn.close()

            blog_list = [
                {
                    "title": blog[0],
                    "image": blog[1],
                    "author": blog[2],
                    "date": blog[3].strftime('%Y-%m-%d'),
                    "intro": blog[4],
                    "content_section": blog[5],
                    "list": blog[6],
                    "conclusion": blog[7],
                    "views": blog[8]
                }
                for blog in blogs
            ]

            return blog_list

        except Exception as e:
            return {"error": "An unexpected error occurred"}, 500

    @blog_ns.expect(blog_model)
    @blog_ns.marshal_with(blog_model)
    def post(self):
        try:
            data = request.json
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO blog (title, image, author, date, intro, content_section, list, conclusion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING title, image, author, date, intro, content_section, list, conclusion, views
            """, (
                data['title'], data['image'], data['author'], datetime.datetime.now(), 
                data['intro'], data['content_section'], data['list'], data['conclusion']
            ))
            new_blog = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            if new_blog:
                return {
                    "title": new_blog[0],
                    "image": new_blog[1],
                    "author": new_blog[2],
                    "date": new_blog[3].strftime('%Y-%m-%d'),
                    "intro": new_blog[4],
                    "content_section": new_blog[5],
                    "list": new_blog[6],
                    "conclusion": new_blog[7],
                    "views": new_blog[8]
                }, 201
            else:
                return {"error": "Failed to create blog post"}, 500

        except Exception as e:
            return {"error": "An unexpected error occurred"}, 500

@blog_ns.route('/blog/<string:title>')
class BlogUpdate(Resource):
    @blog_ns.expect(blog_model)
    @blog_ns.marshal_with(blog_model)
    def put(self, title):
        try:
            data = request.json
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE blog 
                SET image = %s, author = %s, date = %s, intro = %s, content_section = %s, list = %s, conclusion = %s
                WHERE title = %s
                RETURNING title, image, author, date, intro, content_section, list, conclusion, views
            """, (
                data['image'], data['author'], datetime.datetime.now(), 
                data['intro'], data['content_section'], data['list'], data['conclusion'], title
            ))
            updated_blog = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            if updated_blog:
                return {
                    "title": updated_blog[0],
                    "image": updated_blog[1],
                    "author": updated_blog[2],
                    "date": updated_blog[3].strftime('%Y-%m-%d'),
                    "intro": updated_blog[4],
                    "content_section": updated_blog[5],
                    "list": updated_blog[6],
                    "conclusion": updated_blog[7],
                    "views": updated_blog[8]
                }
            else:
                return {"error": "Blog post not found"}, 404

        except Exception as e:
            return {"error": "An unexpected error occurred"}, 500

    def delete(self, title):
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM blog WHERE title = %s", (title,))
            conn.commit()
            cur.close()
            conn.close()
            return {"message": f"Blog post '{title}' deleted successfully"}, 200
        except Exception as e:
            return {"error": "An unexpected error occurred"}, 500

@blog_ns.route('/blog/views/<string:title>')
class BlogViews(Resource):
    def put(self, title):
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE blog 
                SET views = views + 1 
                WHERE title = %s
                RETURNING views
            """, (title,))
            updated_views = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            if updated_views:
                return {"views": updated_views[0]}, 200
            else:
                return {"error": "Blog post not found"}, 404

        except Exception as e:
            return {"error": "An unexpected error occurred"}, 500
