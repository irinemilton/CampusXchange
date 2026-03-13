"""
Campus Circular Economy & Barter Exchange
==========================================
Main Flask Application — MySQL Backend
"""

from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Student, Category, Item, ExchangeTransaction, CreditLedger
from config import Config
from seed_data import seed_all

# ── App Factory ──────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))


# ── Initialize DB ───────────────────────────────────────────
with app.app_context():
    db.create_all()
    seed_all()


# ══════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════

# ── Landing Page ─────────────────────────────────────────────
@app.route('/')
def index():
    items = Item.query.filter_by(Status='Available').order_by(Item.ItemID.desc()).limit(8).all()
    categories = Category.query.all()
    stats = {
        'students': Student.query.count(),
        'items_count': Item.query.count(),
        'exchanges': ExchangeTransaction.query.filter_by(Status='Completed').count(),
        'categories': Category.query.count(),
    }
    return render_template('index.html', items=items, categories=categories, stats=stats)


# ── Auth Routes ──────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if not all([name, email, password, confirm]):
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        if Student.query.filter_by(Email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        student = Student(Name=name, Email=email, CreditBalance=100)
        student.set_password(password)
        db.session.add(student)
        db.session.commit()

        login_user(student)
        flash(f'Welcome to CampusXchange, {name}! You received 100 starter credits.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        student = Student.query.filter_by(Email=email).first()
        if student and student.check_password(password):
            login_user(student)
            flash(f'Welcome back, {student.Name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ── Dashboard ────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    my_items = Item.query.filter_by(Owner_StudentID=current_user.StudentID).all()
    pending_requests = ExchangeTransaction.query.filter(
        ExchangeTransaction.Giver_StudentID == current_user.StudentID,
        ExchangeTransaction.Status == 'Pending'
    ).all()
    my_requests = ExchangeTransaction.query.filter(
        ExchangeTransaction.Receiver_StudentID == current_user.StudentID,
        ExchangeTransaction.Status == 'Pending'
    ).all()
    recent_ledger = CreditLedger.query.filter_by(
        StudentID=current_user.StudentID
    ).order_by(CreditLedger.EntryDate.desc()).limit(10).all()

    return render_template('dashboard.html',
                           my_items=my_items,
                           pending_requests=pending_requests,
                           my_requests=my_requests,
                           recent_ledger=recent_ledger)


# ── Marketplace (Browse Items) ──────────────────────────────
@app.route('/marketplace')
def marketplace():
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')

    query = Item.query.filter_by(Status='Available')

    if category_id:
        query = query.filter_by(CategoryID=category_id)

    if search:
        query = query.filter(
            (Item.Title.ilike(f'%{search}%')) |
            (Item.Description.ilike(f'%{search}%'))
        )

    if sort == 'price_low':
        query = query.order_by(Item.CreditValue.asc())
    elif sort == 'price_high':
        query = query.order_by(Item.CreditValue.desc())
    elif sort == 'oldest':
        query = query.order_by(Item.ItemID.asc())
    else:
        query = query.order_by(Item.ItemID.desc())

    items = query.all()
    categories = Category.query.all()

    return render_template('marketplace.html',
                           items=items,
                           categories=categories,
                           selected_category=category_id,
                           search=search,
                           sort=sort)


# ── List New Item ────────────────────────────────────────────
@app.route('/items/new', methods=['GET', 'POST'])
@login_required
def new_item():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        credit_value = request.form.get('credit_value', type=int)
        category_id = request.form.get('category_id', type=int)

        if not all([title, credit_value, category_id]):
            flash('Title, credit value, and category are required.', 'error')
            return redirect(url_for('new_item'))

        item = Item(
            Title=title,
            Description=description,
            CreditValue=credit_value,
            CategoryID=category_id,
            Owner_StudentID=current_user.StudentID,
            Status='Available'
        )
        db.session.add(item)
        db.session.commit()

        flash(f'"{title}" listed successfully!', 'success')
        return redirect(url_for('dashboard'))

    categories = Category.query.all()
    return render_template('new_item.html', categories=categories)


# ── Item Detail ──────────────────────────────────────────────
@app.route('/items/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    related_items = Item.query.filter(
        Item.CategoryID == item.CategoryID,
        Item.ItemID != item.ItemID,
        Item.Status == 'Available'
    ).limit(4).all()
    return render_template('item_detail.html', item=item, related_items=related_items)


# ── Request Exchange ─────────────────────────────────────────
@app.route('/exchange/request/<int:item_id>', methods=['POST'])
@login_required
def request_exchange(item_id):
    item = Item.query.get_or_404(item_id)

    # Validations
    if item.Owner_StudentID == current_user.StudentID:
        flash('You cannot request your own item.', 'error')
        return redirect(url_for('item_detail', item_id=item_id))

    if item.Status != 'Available':
        flash('This item is no longer available.', 'error')
        return redirect(url_for('item_detail', item_id=item_id))

    if current_user.CreditBalance < item.CreditValue:
        flash(f'Insufficient credits. You need {item.CreditValue} but have {current_user.CreditBalance}.', 'error')
        return redirect(url_for('item_detail', item_id=item_id))

    # Check for existing pending request
    existing = ExchangeTransaction.query.filter(
        ExchangeTransaction.ItemID == item_id,
        ExchangeTransaction.Receiver_StudentID == current_user.StudentID,
        ExchangeTransaction.Status == 'Pending'
    ).first()

    if existing:
        flash('You already have a pending request for this item.', 'warning')
        return redirect(url_for('item_detail', item_id=item_id))

    # Create transaction
    transaction = ExchangeTransaction(
        ItemID=item_id,
        Giver_StudentID=item.Owner_StudentID,
        Receiver_StudentID=current_user.StudentID,
        Status='Pending'
    )

    # Update item status
    item.Status = 'Requested'

    db.session.add(transaction)
    db.session.commit()

    flash(f'Exchange request sent for "{item.Title}"!', 'success')
    return redirect(url_for('dashboard'))


# ── Accept/Reject Exchange ───────────────────────────────────
@app.route('/exchange/<int:transaction_id>/accept', methods=['POST'])
@login_required
def accept_exchange(transaction_id):
    transaction = ExchangeTransaction.query.get_or_404(transaction_id)

    if transaction.Giver_StudentID != current_user.StudentID:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('dashboard'))

    if transaction.Status != 'Pending':
        flash('This transaction is no longer pending.', 'error')
        return redirect(url_for('dashboard'))

    item = transaction.item
    receiver = transaction.receiver
    giver = transaction.giver

    # Credit balance check (atomicity)
    if receiver.CreditBalance < item.CreditValue:
        flash(f'{receiver.Name} no longer has sufficient credits.', 'error')
        transaction.Status = 'Cancelled'
        item.Status = 'Available'
        db.session.commit()
        return redirect(url_for('dashboard'))

    # ── Atomic Transaction ──
    # 1. Transfer credits
    receiver.CreditBalance -= item.CreditValue
    giver.CreditBalance += item.CreditValue

    # 2. Update transaction status
    transaction.Status = 'Completed'

    # 3. Update item status
    item.Status = 'Exchanged'

    # 4. Create ledger entries (double-entry bookkeeping)
    debit_entry = CreditLedger(
        TransactionType='Debit',
        Amount=item.CreditValue,
        StudentID=receiver.StudentID,
        TransactionID=transaction.TransactionID
    )

    credit_entry = CreditLedger(
        TransactionType='Credit',
        Amount=item.CreditValue,
        StudentID=giver.StudentID,
        TransactionID=transaction.TransactionID
    )

    db.session.add(debit_entry)
    db.session.add(credit_entry)
    db.session.commit()

    flash(f'Exchange completed! You received {item.CreditValue} credits for "{item.Title}".', 'success')
    return redirect(url_for('dashboard'))


@app.route('/exchange/<int:transaction_id>/reject', methods=['POST'])
@login_required
def reject_exchange(transaction_id):
    transaction = ExchangeTransaction.query.get_or_404(transaction_id)

    if transaction.Giver_StudentID != current_user.StudentID:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('dashboard'))

    if transaction.Status != 'Pending':
        flash('This transaction is no longer pending.', 'error')
        return redirect(url_for('dashboard'))

    transaction.Status = 'Cancelled'
    transaction.item.Status = 'Available'
    db.session.commit()

    flash('Exchange request declined.', 'info')
    return redirect(url_for('dashboard'))


# ── Cancel My Request ────────────────────────────────────────
@app.route('/exchange/<int:transaction_id>/cancel', methods=['POST'])
@login_required
def cancel_exchange(transaction_id):
    transaction = ExchangeTransaction.query.get_or_404(transaction_id)

    if transaction.Receiver_StudentID != current_user.StudentID:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('dashboard'))

    if transaction.Status != 'Pending':
        flash('This transaction is no longer pending.', 'error')
        return redirect(url_for('dashboard'))

    transaction.Status = 'Cancelled'
    transaction.item.Status = 'Available'
    db.session.commit()

    flash('Your exchange request has been cancelled.', 'info')
    return redirect(url_for('dashboard'))


# ── Transaction History ──────────────────────────────────────
@app.route('/transactions')
@login_required
def transactions():
    all_transactions = ExchangeTransaction.query.filter(
        (ExchangeTransaction.Giver_StudentID == current_user.StudentID) |
        (ExchangeTransaction.Receiver_StudentID == current_user.StudentID)
    ).order_by(ExchangeTransaction.TransactionDate.desc()).all()

    ledger = CreditLedger.query.filter_by(
        StudentID=current_user.StudentID
    ).order_by(CreditLedger.EntryDate.desc()).all()

    return render_template('transactions.html',
                           transactions=all_transactions,
                           ledger=ledger)


# ── API Endpoints for AJAX ───────────────────────────────────
@app.route('/api/stats')
def api_stats():
    return jsonify({
        'students': Student.query.count(),
        'items': Item.query.filter_by(Status='Available').count(),
        'exchanges': ExchangeTransaction.query.filter_by(Status='Completed').count(),
        'total_credits': db.session.query(db.func.sum(Student.CreditBalance)).scalar() or 0,
    })


# ── Delete Item ──────────────────────────────────────────────
@app.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)

    if item.Owner_StudentID != current_user.StudentID:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('dashboard'))

    if item.Status == 'Requested':
        flash('Cannot delete an item with a pending request.', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(item)
    db.session.commit()
    flash(f'"{item.Title}" has been removed.', 'info')
    return redirect(url_for('dashboard'))


# ══════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, port=5000)
