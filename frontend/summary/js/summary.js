fetch('/summary')
    .then(response => response.json())
    .then(data => {
        document.getElementById('totalIncome').textContent = data.total_income;
        document.getElementById('totalExpense').textContent = data.total_expense;
        document.getElementById('balance').textContent = data.balance;
    })
    .catch(error => {
        console.error('Error fetching summary:', error);
    });
