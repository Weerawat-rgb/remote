from flask import Blueprint, request, jsonify
from flask_cors import CORS
import pyodbc

customer_search = Blueprint('customer_search', __name__)
CORS(customer_search)

# Database configuration
DB_CONFIG = {
    'server': '43.128.204.99,14369',
    'database': 'INFO_BKK',
    'username': 'infosqlserver',
    'password': '!nfo@sqlserver$#@!'
}

def get_db_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

@customer_search.route('/api/search', methods=['GET'])
def search():
    # Get parameters
    search_type = request.args.get('type')
    query = request.args.get('query')

    # Print parameters for debugging
    print(f"Received parameters - type: {search_type}, query: {query}")

    # Validate parameters
    if not search_type or not query:
        return jsonify({
            'status': 'error',
            'message': 'Missing required parameters. Both type and query are required.',
            'required_params': {
                'type': 'serial or name',
                'query': 'search term'
            }
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if search_type == 'serial':
            sql = """
                SELECT sp.SupplierName,i.ItemId,i.itemcode, si.ItemDesc, c.Acct, c.FirstName, CONVERT(date,si.InsertDate) as InsertDate 
                FROM SaleItem si
                INNER JOIN Sale s ON s.SaleId = si.SaleId
                INNER JOIN Customer c ON c.CustomerId = s.CustomerId
                INNER JOIN Items i ON i.ItemId = si.ItemId
				LEFT JOIN SupplierXRef sx on sx.ItemId = i.ItemId and sx.IsDefault = 1
				LEFT JOIN Supplier sp on sp.SupplierId = sx.SupplierId
                WHERE i.itemcode LIKE ? OR si.ItemDesc LIKE ?
            """
            search_param = f'%{query}%'
            cursor.execute(sql, (search_param, search_param))
        else:
            sql = """
                SELECT sp.SupplierName,i.ItemId,i.itemcode, si.ItemDesc, c.Acct, c.FirstName, CONVERT(date,si.InsertDate) as InsertDate 
                FROM SaleItem si
                INNER JOIN Sale s ON s.SaleId = si.SaleId
                INNER JOIN Customer c ON c.CustomerId = s.CustomerId
                INNER JOIN Items i ON i.ItemId = si.ItemId
				LEFT JOIN SupplierXRef sx on sx.ItemId = i.ItemId and sx.IsDefault = 1
				LEFT JOIN Supplier sp on sp.SupplierId = sx.SupplierId
                WHERE c.FirstName LIKE ? OR c.LastName LIKE ?
            """
            search_param = f'%{query}%'
            cursor.execute(sql, (search_param, search_param))
        
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        cursor.close()
        conn.close()

        return jsonify({
            'status': 'success',
            'data': results
        })

    except Exception as e:
        print(f"Database error: {str(e)}")  # For debugging
        return jsonify({
            'status': 'error',
            'message': 'Database error occurred',
            'error': str(e)
        }), 500