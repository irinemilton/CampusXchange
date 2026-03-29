import unittest
import os
import sys
from datetime import datetime, timezone
from app import app, db
from models import Student, Category, Item, ExchangeTransaction, CreditLedger

class CampusXchangeFullTestSuite(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Setup initial data
            self.cat1 = Category(CategoryName='Books', Description='Reading material')
            self.cat2 = Category(CategoryName='Tech', Description='Electronics')
            db.session.add_all([self.cat1, self.cat2])
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def register_user(self, name='Test User', email='test@college.edu', password='password123'):
        return self.client.post('/register', data={
            'name': name,
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)

    def login_user(self, email='test@college.edu', password='password123'):
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_auth_flow(self):
        """Test Register -> Login -> Logout"""
        # 1. Register
        resp = self.register_user()
        self.assertIn(b'Welcome to CampusXchange', resp.data)
        
        # 2. Logout
        resp = self.client.post('/logout', follow_redirects=True)
        self.assertIn(b'logged out', resp.data)
        
        # 3. Login
        resp = self.login_user()
        self.assertIn(b'Welcome back', resp.data)

    def test_item_management(self):
        """Test Listing, Editing, and Deleting items"""
        self.register_user()
        
        # 1. List Item
        resp = self.client.post('/items/new', data={
            'title': 'Test Item',
            'description': 'Test Description',
            'credit_value': 50,
            'category_id': 1,
            'condition': 'New'
        }, follow_redirects=True)
        self.assertIn(b'listed successfully', resp.data)
        self.assertIn(b'Test Item', resp.data)

        # 2. Edit Item
        resp = self.client.post('/items/1/edit', data={
            'title': 'Updated Item',
            'description': 'Updated Desc',
            'credit_value': 60,
            'category_id': 2,
            'condition': 'Fair'
        }, follow_redirects=True)
        self.assertIn(b'updated successfully', resp.data)
        self.assertIn(b'Updated Item', resp.data)

        # 3. Delete Item
        resp = self.client.post('/items/1/delete', follow_redirects=True)
        self.assertIn(b'has been removed', resp.data)

    def test_exchange_workflow(self):
        """Test the full exchange lifecycle and credit transfer"""
        # Create Giver
        self.register_user(name='Giver', email='giver@college.edu')
        self.client.post('/items/new', data={'title': 'Giver Item', 'credit_value': 30, 'category_id': 1})
        self.client.post('/logout')

        # Create Receiver
        self.register_user(name='Receiver', email='recevier@college.edu') # Start with 100 credits
        
        # 1. Request Item
        resp = self.client.post('/exchange/request/1', follow_redirects=True)
        self.assertIn(b'request sent successfully', resp.data)
        
        # Switch to Giver to Accept
        self.client.post('/logout')
        self.login_user(email='giver@college.edu')
        
        # 2. Accept Request
        resp = self.client.post('/exchange/1/accept', follow_redirects=True)
        self.assertIn(b'Exchange completed', resp.data)
        
        # 3. Verify Credit Transfer
        with app.app_context():
            giver = Student.query.filter_by(Email='giver@college.edu').first()
            receiver = Student.query.filter_by(Email='recevier@college.edu').first()
            # Giver: 100 (starter) + 30 = 130
            # Receiver: 100 (starter) - 30 = 70
            self.assertEqual(giver.CreditBalance, 130)
            self.assertEqual(receiver.CreditBalance, 70)

    def test_admin_balance_adjustment(self):
        """Test Admin tool for shifting credits"""
        # admin@campus.edu.in is in ADMIN_EMAILS set in app.py
        self.register_user(email='admin@campus.edu.in')
        
        # Adjust balance of self
        resp = self.client.post('/admin/adjust-balance', data={
            'student_id': 1,
            'amount': 500,
            'type': 'add'
        }, follow_redirects=True)
        
        self.assertIn(b'Adjusted balance', resp.data)
        with app.app_context():
            admin = Student.query.get(1)
            self.assertEqual(admin.CreditBalance, 600) # 100 + 500

    def test_bio_update(self):
        """Test editing student profile bio"""
        self.register_user()
        resp = self.client.post('/profile', data={'bio': 'This is my new bio'}, follow_redirects=True)
        self.assertIn(b'Profile updated successfully', resp.data)
        self.assertIn(b'This is my new bio', resp.data)

    def test_insufficient_credits(self):
        """Verify items cannot be requested with low balance"""
        self.register_user(email='giver@college.edu')
        self.client.post('/items/new', data={'title': 'Expensive', 'credit_value': 200, 'category_id': 1})
        self.client.post('/logout')

        self.register_user(email='poor@college.edu') # Has 100
        resp = self.client.post('/exchange/request/1', follow_redirects=True)
        self.assertIn(b'Insufficient credits', resp.data)

    def test_protected_routes(self):
        """Ensure non-logged in users cannot access private areas"""
        protected_urls = ['/dashboard', '/profile', '/items/new', '/admin', '/transactions']
        for url in protected_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302) # Redirects to login

    def test_registration_failures(self):
        """Test various registration failure scenarios"""
        # 1. Missing fields
        resp = self.client.post('/register', data={'name': 'fail', 'email': 'fail@test.edu'}, follow_redirects=True)
        if b'All fields are required' not in resp.data:
            print(f"DEBUG Registration Missing Fields: {resp.data[:500]}")
        self.assertIn(b'All fields are required', resp.data)
        
        # 2. Duplicate email
        self.register_user(email='dup@college.edu')
        self.client.post('/logout') # Must logout to test registration again
        resp = self.register_user(email='dup@college.edu')
        if b'Email already registered' not in resp.data:
            print(f"DEBUG Registration Duplicate: {resp.data[:1000]}")
        self.assertIn(b'Email already registered', resp.data)
        
        # 3. Mismatched password
        resp = self.client.post('/register', data={
            'name': 'mismatch', 'email': 'mismatch@college.edu', 'password': '1', 'confirm_password': '2'
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', resp.data)

    def test_login_failures(self):
        """Test invalid login credentials"""
        self.register_user()
        self.client.post('/logout') # Must logout after registering to test login
        resp = self.client.post('/login', data={'email': 'test@college.edu', 'password': 'wrong'}, follow_redirects=True)
        self.assertIn(b'Invalid email or password', resp.data)

    def test_view_counter(self):
        """Verify view incrementing on item detail access"""
        self.register_user()
        self.client.post('/items/new', data={'title': 'Eye-Catcher', 'credit_value': 10, 'category_id': 1})
        
        # Access 5 times
        for _ in range(5):
            self.client.get('/items/1')
            
        with app.app_context():
            item = db.session.get(Item, 1) # Safer than query.get
            self.assertEqual(item.ViewCount, 5)

    def test_advanced_exchange_logic(self):
        """Test logic where receiver spends credits *after* requesting an item"""
        # Giver has target item (cost: 50)
        self.register_user(name='Giver', email='giver@college.edu')
        self.client.post('/items/new', data={'title': 'Target', 'description': 'desc', 'credit_value': 50, 'category_id': 1})
        self.client.post('/logout')

        # Giver starts with 100
        self.register_user(name='Other Giver', email='other@college.edu')
        self.client.post('/items/new', data={'title': 'Other', 'description': 'desc', 'credit_value': 80, 'category_id': 1})
        self.client.post('/logout')

        # Receiver starts with 100
        self.register_user(name='Receiver', email='receiver@college.edu')
        
        # 1. Receiver requests Target (Cost 50). Success (Balance: 100 >= 50).
        self.client.post('/exchange/request/1', follow_redirects=True)
        
        # 2. Receiver requests Other (Cost 150). Fail (Balance 100 < 150).
        # We need an item that costs 150.
        self.client.post('/logout')
        self.login_user(email='giver@college.edu')
        self.client.post('/items/new', data={'title': 'Expensive', 'description': 'desc', 'credit_value': 150, 'category_id': 1})
        self.client.post('/logout')
        self.login_user(email='receiver@college.edu')
        
        resp = self.client.post('/exchange/request/3', follow_redirects=True)
        self.assertIn(b'Insufficient credits', resp.data)

    def test_api_and_pages(self):
        """General check of public views and simple API"""
        # API Stats
        resp = self.client.get('/api/stats')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'total_credits', resp.data)
        
        # Leaderboard
        resp = self.client.get('/leaderboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Leaderboard', resp.data)
        
        # Marketplace Page
        resp = self.client.get('/marketplace')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Marketplace', resp.data)

if __name__ == '__main__':
    unittest.main()
