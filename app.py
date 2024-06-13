from flask import Flask, request, jsonify, render_template
app = Flask(__name__)

# Assuming you are storing these in-memory for simplicity
total_income = 0
total_expense = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_income', methods=['POST'])
def add_income():
    global total_income
    data = request.get_json()
    amount = data['amount']
    total_income += amount
    return jsonify({"message": "Income added", "total_income": total_income})

@app.route('/add_expense', methods=['POST'])
def add_expense():
    global total_expense
    data = request.get_json()
    amount = data['amount']
    total_expense += amount
    return jsonify({"message": "Expense added", "total_expense": total_expense})

@app.route('/summary', methods=['GET'])
def summary():
    balance = total_income - total_expense
    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
