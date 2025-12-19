from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)

# SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    note = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@app.route("/")
def dashboard():
    expenses = Expense.query.order_by(Expense.created_at.desc()).all()

    total_spent = sum(e.amount for e in expenses)

    category_totals = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total_spent=total_spent,
        category_totals=category_totals,
    )


@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        note = request.form.get("note", "").strip()

        # Basic validation
        try:
            amount = float(amount_raw)
        except ValueError:
            return render_template("add.html", error="Amount must be a number.")

        if amount <= 0:
            return render_template("add.html", error="Amount must be greater than 0.")

        if not category:
            return render_template("add.html", error="Category is required.")

        expense = Expense(
            amount=amount,
            category=category,
            note=note if note else None,
        )
        db.session.add(expense)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("add.html")


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
