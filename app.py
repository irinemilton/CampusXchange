"""
Campus Circular Economy & Barter Exchange
==========================================
Main Flask Application — MySQL Backend
"""

from datetime import datetime, timedelta
import random
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from models import db, Student, Category, Item, ExchangeTransaction, CreditLedger
from config import Config
from seed_data import seed_all
import re

ITEMS_PER_PAGE = 12

# ── App Factory ──────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
csrf = CSRFProtect(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Student, int(user_id))


# ── Health Check ─────────────────────────────────────────────
@app.route('/health')
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


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

        if not re.search(r'\.edu(\.|$)', email.lower().split('@')[-1]):
            flash('Only university .edu email addresses are allowed (e.g. you@college.edu.in).', 'error')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('register'))

        if Student.query.filter_by(Email=email.lower()).first():
            flash('This email is already registered. Please login or use a different email.', 'error')
            return redirect(url_for('register'))

        try:
            # Always store emails in lowercase for consistent lookup
            student = Student(Name=name, Email=email.lower(), CreditBalance=100)
            student.set_password(password)
            db.session.add(student)
            db.session.commit()
            
            login_user(student, remember=True)
            flash(f'Welcome to CampusXchange, {name}! You received 100 starter credits.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        # Lookup is now case-insensitive
        student = Student.query.filter_by(Email=email).first()
        
        if student:
            # Check if account is blocked (for demonstration, we only lock locally)
            if student.FailedLoginAttempts >= 5:
                flash('Account locked due to too many failed attempts. Contact admin.', 'error')
                return redirect(url_for('login'))

            if student.check_password(password):
                # SUCCESS
                student.FailedLoginAttempts = 0
                db.session.commit()
                
                login_user(student, remember=remember)
                flash(f'Welcome back, {student.Name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                # FAILURE
                student.FailedLoginAttempts += 1
                db.session.commit()
                flash('Invalid email or password.', 'error')
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ── Forgot Password ────────────────────────────────────────────────────────
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        student = Student.query.filter_by(Email=email).first()

        # Always show the same message to avoid leaking registered emails
        flash('If that email is registered, a password reset link has been sent.', 'info')

        if student:
            # Generate a secure random token
            token = secrets.token_urlsafe(32)
            student.PasswordResetToken = token
            student.PasswordResetExpiry = datetime.utcnow() + timedelta(seconds=app.config['PASSWORD_RESET_EXPIRY'])
            db.session.commit()

            # Build the reset URL
            reset_url = url_for('reset_password', token=token, _external=True)

            # Send email
            try:
                msg = Message(
                    subject='CampusXchange — Password Reset Request',
                    recipients=[student.Email]
                )
                msg.html = f"""
                <div style="font-family:sans-serif;max-width:520px;margin:auto;background:#0f172a;color:#e2e8f0;padding:32px;border-radius:16px;">
                    <div style="text-align:center;margin-bottom:24px;">
                        <span style="font-size:40px;">&#9851;</span>
                        <h1 style="color:#818cf8;font-size:22px;margin:8px 0 4px;">CampusXchange</h1>
                        <p style="color:#94a3b8;font-size:13px;margin:0;">Campus Circular Economy Platform</p>
                    </div>
                    <h2 style="font-size:18px;margin-bottom:8px;">Hi {student.Name},</h2>
                    <p style="color:#94a3b8;font-size:14px;line-height:1.6;">
                        We received a request to reset the password for your account.
                        Click the button below to set a new password. This link will expire in <strong style="color:#e2e8f0;">30 minutes</strong>.
                    </p>
                    <div style="text-align:center;margin:28px 0;">
                        <a href="{reset_url}"
                           style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;padding:14px 32px;
                                  border-radius:12px;text-decoration:none;font-weight:600;font-size:15px;">
                            Reset My Password
                        </a>
                    </div>
                    <p style="color:#64748b;font-size:12px;text-align:center;">
                        If you didn't request this, you can safely ignore this email.<br>
                        Your password won't change until you click the link above.
                    </p>
                    <hr style="border-color:#1e293b;margin:24px 0;">
                    <p style="color:#475569;font-size:11px;text-align:center;">CampusXchange &mdash; Built for students, by students.</p>
                </div>
                """
                mail.send(msg)
            except Exception:
                app.logger.error(f'Failed to send password reset email to {student.Email}', exc_info=True)

        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')


# ── Reset Password (via token link) ───────────────────────────────────────
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    student = Student.query.filter_by(PasswordResetToken=token).first()

    # Validate token existence and expiry
    if not student or student.PasswordResetExpiry is None or student.PasswordResetExpiry < datetime.utcnow():
        flash('This password reset link is invalid or has expired. Please request a new one.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('reset_password', token=token))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('reset_password', token=token))

        # Update password and clear the reset token
        student.set_password(password)
        student.PasswordResetToken = None
        student.PasswordResetExpiry = None
        student.FailedLoginAttempts = 0  # Unlock account if it was locked
        db.session.commit()

        flash('Your password has been reset successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


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
    condition = request.args.get('condition', '')
    page = request.args.get('page', 1, type=int)

    query = Item.query.filter_by(Status='Available')

    if category_id:
        query = query.filter_by(CategoryID=category_id)

    if search:
        query = query.filter(
            (Item.Title.ilike(f'%{search}%')) |
            (Item.Description.ilike(f'%{search}%'))
        )

    if condition in ('New', 'Like New', 'Good', 'Fair'):
        query = query.filter_by(Condition=condition)

    if sort == 'price_low':
        query = query.order_by(Item.CreditValue.asc())
    elif sort == 'price_high':
        query = query.order_by(Item.CreditValue.desc())
    elif sort == 'oldest':
        query = query.order_by(Item.ItemID.asc())
    else:
        query = query.order_by(Item.ItemID.desc())

    pagination = query.paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)
    items = pagination.items
    categories = Category.query.all()

    return render_template('marketplace.html',
                           items=items,
                           pagination=pagination,
                           categories=categories,
                           selected_category=category_id,
                           selected_condition=condition,
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
        condition = request.form.get('condition', 'Good')

        if not all([title, credit_value, category_id]):
            flash('Title, credit value, and category are required.', 'error')
            return redirect(url_for('new_item'))

        if len(title) > 100:
            flash('Title is too long (max 100 chars).', 'error')
            return redirect(url_for('new_item'))

        if credit_value < 1:
            flash('Credit value must be at least 1.', 'error')
            return redirect(url_for('new_item'))

        item = Item(
            Title=title,
            Description=description,
            CreditValue=credit_value,
            CategoryID=category_id,
            Owner_StudentID=current_user.StudentID,
            Status='Available',
            Condition=condition
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
    
    # Increment view count
    item.ViewCount = (item.ViewCount or 0) + 1
    db.session.commit()

    # Get similar items (same category, different item, available)
    similar_items = Item.query.filter(
        Item.CategoryID == item.CategoryID,
        Item.ItemID != item.ItemID,
        Item.Status == 'Available'
    ).limit(3).all()
    
    return render_template('item_detail.html', item=item, similar_items=similar_items)


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
    try:
        transaction = ExchangeTransaction(
            ItemID=item_id,
            Giver_StudentID=item.Owner_StudentID,
            Receiver_StudentID=current_user.StudentID,
            Status='Pending'
        )
        item.Status = 'Requested'
        db.session.add(transaction)
        db.session.commit()
        flash('Exchange request sent successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to send request. Please try again.', 'error')
    
    return redirect(url_for('item_detail', item_id=item_id))


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
    try:
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
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while processing the exchange. Please try again.', 'error')
        return redirect(url_for('dashboard'))

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


# ── Context Processor: Notification Badge ────────────────────
@app.context_processor
def inject_pending_count():
    if current_user.is_authenticated:
        count = ExchangeTransaction.query.filter_by(
            Receiver_StudentID=current_user.StudentID,
            Status='Pending'
        ).count()
        return {'pending_count': count}
    return {'pending_count': 0}


# ── Leaderboard ───────────────────────────────────────────────
@app.route('/leaderboard')
def leaderboard():
    top_earners = db.session.query(
        Student,
        db.func.coalesce(db.func.sum(CreditLedger.Amount), 0).label('total_earned'),
        db.func.count(ExchangeTransaction.TransactionID).label('exchange_count')
    ).outerjoin(
        CreditLedger,
        (CreditLedger.StudentID == Student.StudentID) & (CreditLedger.TransactionType == 'Credit')
    ).outerjoin(
        ExchangeTransaction,
        (ExchangeTransaction.Giver_StudentID == Student.StudentID) & (ExchangeTransaction.Status == 'Completed')
    ).group_by(Student.StudentID).order_by(
        db.text('total_earned DESC')
    ).limit(10).all()

    total_exchanges = ExchangeTransaction.query.filter_by(Status='Completed').count()
    total_items = Item.query.count()
    total_students = Student.query.count()

    return render_template('leaderboard.html',
                           top_earners=top_earners,
                           total_exchanges=total_exchanges,
                           total_items=total_items,
                           total_students=total_students)


# ── Admin Dashboard ───────────────────────────────────────────
ADMIN_EMAILS = {'admin@campus.edu.in', 'admin@campusxchange.edu'}

@app.route('/admin')
@login_required
def admin():
    if current_user.Email not in ADMIN_EMAILS and current_user.StudentID != 1:
        flash('Admin access only.', 'error')
        return redirect(url_for('index'))

    students = Student.query.order_by(Student.StudentID.desc()).all()
    items = Item.query.order_by(Item.ItemID.desc()).all()
    transactions = ExchangeTransaction.query.order_by(
        ExchangeTransaction.TransactionDate.desc()
    ).limit(50).all()

    stats = {
        'total_students': len(students),
        'total_items': len(items),
        'available_items': sum(1 for i in items if i.Status == 'Available'),
        'completed_exchanges': ExchangeTransaction.query.filter_by(Status='Completed').count(),
        'pending_exchanges': ExchangeTransaction.query.filter_by(Status='Pending').count(),
        'total_credits_in_system': db.session.query(db.func.sum(Student.CreditBalance)).scalar() or 0,
    }

    return render_template('admin.html',
                           students=students,
                           items=items,
                           transactions=transactions,
                           stats=stats)



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

    title = item.Title
    db.session.delete(item)
    db.session.commit()
    flash(f'"{title}" has been removed.', 'info')
    return redirect(url_for('dashboard'))


# ── Edit Item ────────────────────────────────────────────────
@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)

    if item.Owner_StudentID != current_user.StudentID:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('dashboard'))

    if item.Status != 'Available':
        flash('Only Available items can be edited.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        credit_value = request.form.get('credit_value', type=int)
        category_id = request.form.get('category_id', type=int)
        condition = request.form.get('condition', 'Good')

        if not all([title, credit_value, category_id]):
            flash('Title, credit value, and category are required.', 'error')
            return redirect(url_for('edit_item', item_id=item_id))

        if len(title) > 100:
            flash('Title is too long (max 100 chars).', 'error')
            return redirect(url_for('edit_item', item_id=item_id))

        if credit_value < 1:
            flash('Credit value must be at least 1.', 'error')
            return redirect(url_for('edit_item', item_id=item_id))

        item.Title = title
        item.Description = description
        item.CreditValue = credit_value
        item.CategoryID = category_id
        item.Condition = condition
        db.session.commit()

        flash(f'"{title}" updated successfully!', 'success')
        return redirect(url_for('item_detail', item_id=item_id))

    categories = Category.query.all()
    return render_template('edit_item.html', item=item, categories=categories)


# ── How it Works (About Page) ────────────────────────────────
@app.route('/about')
def about():
    return render_template('how_it_works.html')


# ── Profile Page ─────────────────────────────────────────────
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()
        current_user.Bio = bio
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    my_items = Item.query.filter_by(Owner_StudentID=current_user.StudentID).all()

    completed_given = ExchangeTransaction.query.filter_by(
        Giver_StudentID=current_user.StudentID,
        Status='Completed'
    ).count()

    completed_received = ExchangeTransaction.query.filter_by(
        Receiver_StudentID=current_user.StudentID,
        Status='Completed'
    ).count()

    credits_earned = db.session.query(db.func.sum(CreditLedger.Amount)).filter_by(
        StudentID=current_user.StudentID,
        TransactionType='Credit'
    ).scalar() or 0

    credits_spent = db.session.query(db.func.sum(CreditLedger.Amount)).filter_by(
        StudentID=current_user.StudentID,
        TransactionType='Debit'
    ).scalar() or 0

    return render_template('profile.html',
                           my_items=my_items,
                           completed_given=completed_given,
                           completed_received=completed_received,
                           credits_earned=credits_earned,
                           credits_spent=credits_spent)


# ── Admin adjustment ─────────────────────────────────────────
@app.route('/admin/adjust-balance', methods=['POST'])
@login_required
def adjust_balance():
    if current_user.Email not in ADMIN_EMAILS and current_user.StudentID != 1:
        flash('Unauthorized.', 'error')
        return redirect(url_for('index'))

    student_id = request.form.get('student_id', type=int)
    amount = request.form.get('amount', type=int)
    adj_type = request.form.get('type')  # 'add' or 'subtract'

    student = Student.query.get_or_404(student_id)
    if adj_type == 'add':
        student.CreditBalance += amount
    else:
        student.CreditBalance = max(0, student.CreditBalance - amount)
    
    db.session.commit()
    flash(f"Adjusted balance for {student.Name} by {amount} credits.", "success")
    return redirect(url_for('admin'))


# ── Error Handlers ───────────────────────────────────────────
@app.errorhandler(404)
def error_404(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def error_500(e):
    return render_template('errors/500.html'), 500


# ══════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_all()
    app.run(debug=True, port=5000)
