from flask_restx import Namespace, Resource
from utils import initialize_db
from flask import jsonify


home_ns = Namespace('home', description='Home related operations')

@home_ns.route('/home')
class HelloWorld(Resource):
    def get(self):
        return {'Hello': 'World'}

@home_ns.route('/db_data')
class DBData(Resource):
    def get(self):
        try:
            initialize_db()
            return "Database initialized and seeded successfully"
        except Exception as error:
            return {'error': str(error)}

@home_ns.route('/python')
class PythonVersion(Resource):
    def get(self):
        return {'Python': 'Flask'}

@home_ns.route('/data')
class Data(Resource):
    def get(self):
        data = {
            'Name': "sautis",
            "Age": "30",
            "programming": "python flask, react, typescript, nodejs, php, laravel"
        }
        return jsonify(data)