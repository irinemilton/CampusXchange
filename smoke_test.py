import unittest
import os
import sys
from app import app, db
from models import Student, Category, Item

class CampusXchangeTestCase(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite database for testing to avoid affecting production data
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for simpler tests
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Seed basic categories
            cat = Category(CategoryName='Testing', Description='Test Cat')
            db.session.add(cat)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_health_check(self):
        """Test the new health check route"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'healthy', response.data)

    def test_registration(self):
        """Test student registration flow"""
        response = self.app.post('/register', data={
            'name': 'Tester',
            'email': 'test@college.edu',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to CampusXchange', response.data)
        
        with app.app_context():
            student = Student.query.filter_by(Email='test@college.edu').first()
            self.assertIsNotNone(student)
            self.assertEqual(student.Name, 'Tester')

    def test_invalid_email(self):
        """Test registration with non-.edu email"""
        response = self.app.post('/register', data={
            'name': 'Hacker',
            'email': 'hacker@gmail.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Only university .edu email addresses are allowed', response.data)

    def test_marketplace_search(self):
        """Test that marketplace search returns correct items"""
        with app.app_context():
            student = Student(Name='Owner', Email='owner@college.edu', PasswordHash='none')
            db.session.add(student)
            db.session.commit()
            
            cat = Category.query.first()
            item = Item(Title='Unique Gadget', Description='Find me', CreditValue=10, CategoryID=cat.CategoryID, Status='Available', Owner_StudentID=student.StudentID)
            db.session.add(item)
            db.session.commit()

        response = self.app.get('/marketplace?search=Unique')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Unique Gadget', response.data)
        
        response = self.app.get('/marketplace?search=Unknown')
        self.assertNotIn(b'Unique Gadget', response.data)

if __name__ == '__main__':
    unittest.main()
