"""
Campus Circular Economy & Barter Exchange - Database Models
============================================================
Five primary entities: Student, Category, Item, ExchangeTransaction, CreditLedger
Uses MySQL via PyMySQL connector.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Student(UserMixin, db.Model):
    """
    Table 1: Student
    - Stores registered student information
    - CreditBalance tracks virtual currency
    """
    __tablename__ = 'student'

    StudentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), nullable=False, unique=True)
    PasswordHash = db.Column(db.String(255), nullable=False)
    CreditBalance = db.Column(db.Integer, default=0)

    # Relationships
    items = db.relationship('Item', backref='owner', lazy='dynamic',
                            foreign_keys='Item.Owner_StudentID')
    given_transactions = db.relationship('ExchangeTransaction', backref='giver', lazy='dynamic',
                                         foreign_keys='ExchangeTransaction.Giver_StudentID')
    received_transactions = db.relationship('ExchangeTransaction', backref='receiver', lazy='dynamic',
                                             foreign_keys='ExchangeTransaction.Receiver_StudentID')
    ledger_entries = db.relationship('CreditLedger', backref='student', lazy='dynamic')

    def get_id(self):
        return str(self.StudentID)

    def set_password(self, password):
        self.PasswordHash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.PasswordHash, password)

    def __repr__(self):
        return f'<Student {self.Name}>'


class Category(db.Model):
    """
    Table 2: Category
    - Classifies items into academic resource types
    """
    __tablename__ = 'category'

    CategoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CategoryName = db.Column(db.String(50), nullable=False, unique=True)
    Description = db.Column(db.String(255), nullable=True)

    # Relationships
    items = db.relationship('Item', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.CategoryName}>'


class Item(db.Model):
    """
    Table 3: Item
    - Academic resources listed for barter exchange
    - Status tracks item lifecycle: Available -> Requested -> Exchanged
    """
    __tablename__ = 'item'

    ItemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text, nullable=True)
    CreditValue = db.Column(db.Integer, nullable=False)
    Status = db.Column(db.Enum('Available', 'Requested', 'Exchanged'), default='Available')

    # Foreign Keys
    CategoryID = db.Column(db.Integer, db.ForeignKey('category.CategoryID'))
    Owner_StudentID = db.Column(db.Integer, db.ForeignKey('student.StudentID'))

    # Relationships
    transactions = db.relationship('ExchangeTransaction', backref='item', lazy='dynamic')

    def __repr__(self):
        return f'<Item {self.Title}>'


class ExchangeTransaction(db.Model):
    """
    Table 4: ExchangeTransaction
    - Central hub managing exchanges between Givers and Receivers
    - Status tracks transaction lifecycle: Pending -> Completed / Cancelled
    """
    __tablename__ = 'exchange_transaction'

    TransactionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TransactionDate = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.Enum('Pending', 'Completed', 'Cancelled'), default='Pending')

    # Foreign Keys
    ItemID = db.Column(db.Integer, db.ForeignKey('item.ItemID'))
    Giver_StudentID = db.Column(db.Integer, db.ForeignKey('student.StudentID'))
    Receiver_StudentID = db.Column(db.Integer, db.ForeignKey('student.StudentID'))

    # Relationships
    ledger_entries = db.relationship('CreditLedger', backref='transaction', lazy='dynamic')

    def __repr__(self):
        return f'<Transaction {self.TransactionID}>'


class CreditLedger(db.Model):
    """
    Table 5: CreditLedger
    - Records all credit movements for audit trail
    - Every transaction creates two entries: Credit (for giver) and Debit (for receiver)
    """
    __tablename__ = 'credit_ledger'

    LedgerID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TransactionType = db.Column(db.Enum('Credit', 'Debit'), nullable=False)
    Amount = db.Column(db.Integer, nullable=False)
    EntryDate = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    StudentID = db.Column(db.Integer, db.ForeignKey('student.StudentID'))
    TransactionID = db.Column(db.Integer, db.ForeignKey('exchange_transaction.TransactionID'))

    def __repr__(self):
        return f'<Ledger {self.LedgerID}: {self.TransactionType} {self.Amount}>'
