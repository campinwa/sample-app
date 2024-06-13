from flask import Flask, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'user'
app.config['MYSQL_PASSWORD'] = 'user_password'
app.config['MYSQL_DB'] = 'income_expense_db'

mysql = MySQL(app)

@app.route('/')
def index():
    return "Income and Expense Counter"

@app.route('/data')
def data():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM your_table''')
    rv = cur.fetchall()
    return jsonify(rv)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
