# routes/chat_routes.py
import os
import uuid
import datetime
from flask import Blueprint, request, jsonify, current_app, make_response
from werkzeug.utils import secure_filename
from utils import connect_db
from flask_restx import Namespace, Resource


chat_ns = Namespace('chat', description='Chat operations')

@chat_ns.route('/chat/upload')
class FileUpload(Resource):
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
