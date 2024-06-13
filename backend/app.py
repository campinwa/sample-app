from flask import Flask, request, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'  # or the IP address of your local machine
app.config['MYSQL_USER'] = 'root'  # default MySQL username in XAMPP
app.config['MYSQL_PASSWORD'] = ''  # default password is usually empty in XAMPP
app.config['MYSQL_DB'] = 'income_expense_db'  # the name of your database

mysql = MySQL(app)

# Initialize MySQL
def init_mysql():
    cur = mysql.connection.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            amount FLOAT,
            type VARCHAR(10) -- 'income' or 'expense'
        )
    ''')
    mysql.connection.commit()
    cur.close()

# Store income and expenses in-memory (for demonstration purposes)
data = {
    'income': [],
    'expenses': []
}

@app.route('/')
def index():
    return "Income and Expense Counter"

@app.route('/data')
def fetch_data():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM transactions''')
    rv = cur.fetchall()
    cur.close()
    return jsonify(rv)

@app.route('/add_income', methods=['POST'])
def add_income():
    amount = request.json.get('amount')
    cur = mysql.connection.cursor()
    cur.execute('''INSERT INTO transactions (amount, type) VALUES (%s, %s)''', (amount, 'income'))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Income added successfully'}), 200

@app.route('/add_expense', methods=['POST'])
def add_expense():
    amount = request.json.get('amount')
    cur = mysql.connection.cursor()
    cur.execute('''INSERT INTO transactions (amount, type) VALUES (%s, %s)''', (amount, 'expense'))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Expense added successfully'}), 200

@app.route('/summary', methods=['GET'])
def summary():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS total_income,
                          SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS total_expense
                   FROM transactions''')
    result = cur.fetchone()
    cur.close()
    total_income = result['total_income'] if result['total_income'] else 0
    total_expense = result['total_expense'] if result['total_expense'] else 0
    balance = total_income - total_expense
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance
    }), 200

if __name__ == '__main__':
    init_mysql()  # Initialize MySQL tables on startup
    app.run(debug=True)
