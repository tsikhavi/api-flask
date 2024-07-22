from flask import Blueprint, request, jsonify
from flask_restx import Namespace, Resource, fields
from utils import connect_db

invoice_ns = Namespace('invoices', description='Invoice operations')

invoice_model = invoice_ns.model('Invoice', {
    'id': fields.Integer(description='ID of the invoice'),
    'name': fields.String(required=True, description='Name of the invoice'),
    'amount': fields.Float(required=True, description='Amount of the invoice'),
    'due_date': fields.String(required=True, description='Due date of the invoice'),
    'status': fields.String(description='Status of the invoice')
})

@invoice_ns.route('/list_invoices')
class InvoiceList(Resource):
    def get(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, amount, due_date, status FROM invoices")
        rows = cur.fetchall()
        invoices = [
            {
                'id': row[0],
                'name': row[1],
                'amount': row[2],
                'due_date': row[3],
                'status': row[4]
            }
            for row in rows
        ]
        cur.close()
        conn.close()
        return jsonify(invoices)

    @invoice_ns.expect(invoice_model)
    def post(self):
        data = request.json
        name = data['name']
        amount = data['amount']
        due_date = data['due_date']
        status = data.get('status', 'pending')

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO invoices (name, amount, due_date, status) VALUES (%s, %s, %s, %s)",
                    (name, amount, due_date, status))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Invoice created successfully'}), 201

@invoice_ns.route('/get_invoice/<int:id>')
class Invoice(Resource):
    def get(self, id):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, amount, due_date, status FROM invoices WHERE id = %s", (id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            invoice = {
                'id': row[0],
                'name': row[1],
                'amount': row[2],
                'due_date': row[3],
                'status': row[4]
            }
            return jsonify(invoice)
        return jsonify({'message': 'Invoice not found'}), 404

    def delete(self, id):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM invoices WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Invoice deleted successfully'}), 200

    @invoice_ns.expect(invoice_model)
    def put(self, id):
        data = request.json
        name = data['name']
        amount = data['amount']
        due_date = data['due_date']
        status = data['status']

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE invoices SET name = %s, amount = %s, due_date = %s, status = %s WHERE id = %s",
                    (name, amount, due_date, status, id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Invoice updated successfully'}), 200
