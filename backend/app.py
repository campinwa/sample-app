from flask import Flask, request, jsonify

app = Flask(__name__)

# Store income and expenses
data = {
    'income': [],
    'expenses': []
}

@app.route('/add_income', methods=['POST'])
def add_income():
    amount = request.json.get('amount')
    data['income'].append(amount)
    return jsonify({'message': 'Income added successfully'}), 200

@app.route('/add_expense', methods=['POST'])
def add_expense():
    amount = request.json.get('amount')
    data['expenses'].append(amount)
    return jsonify({'message': 'Expense added successfully'}), 200

@app.route('/summary', methods=['GET'])
def summary():
    total_income = sum(data['income'])
    total_expense = sum(data['expenses'])
    balance = total_income - total_expense
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
