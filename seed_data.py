"""
Seed the database with sample categories and demo data
"""

from models import db, Student, Category, Item
from werkzeug.security import generate_password_hash


def seed_categories():
    """Insert default academic resource categories"""
    categories = [
        Category(CategoryName='Textbooks', Description='Academic textbooks and reference materials', Icon='📚'),
        Category(CategoryName='Electronics', Description='Calculators, tablets, and gadgets', Icon='💻'),
        Category(CategoryName='Lab Equipment', Description='Lab coats, goggles, and instruments', Icon='🔬'),
        Category(CategoryName='Stationery', Description='Notebooks, pens, and art supplies', Icon='✏️'),
        Category(CategoryName='Study Materials', Description='Notes, flashcards, and study guides', Icon='📝'),
        Category(CategoryName='Sports Equipment', Description='Sports gear and fitness equipment', Icon='⚽'),
    ]

    for cat in categories:
        existing = Category.query.filter_by(CategoryName=cat.CategoryName).first()
        if not existing:
            db.session.add(cat)

    db.session.commit()


def seed_demo_data():
    """Insert demo students and items for showcase"""
    # Demo students
    demo_students = [
        {'Name': 'Aarav Sharma', 'Email': 'aarav@campus.edu', 'Password': 'demo123', 'Avatar': '🧑‍💻'},
        {'Name': 'Priya Patel', 'Email': 'priya@campus.edu', 'Password': 'demo123', 'Avatar': '👩‍🔬'},
        {'Name': 'Rohit Kumar', 'Email': 'rohit@campus.edu', 'Password': 'demo123', 'Avatar': '👨‍🎓'},
        {'Name': 'Sneha Gupta', 'Email': 'sneha@campus.edu', 'Password': 'demo123', 'Avatar': '👩‍💻'},
        {'Name': 'Arjun Mehta', 'Email': 'arjun@campus.edu', 'Password': 'demo123', 'Avatar': '🧑‍🎓'},
    ]

    for s in demo_students:
        existing = Student.query.filter_by(Email=s['Email']).first()
        if not existing:
            student = Student(
                Name=s['Name'],
                Email=s['Email'],
                PasswordHash=generate_password_hash(s['Password']),
                CreditBalance=100,
                Avatar=s['Avatar']
            )
            db.session.add(student)

    db.session.commit()

    # Demo items
    textbooks = Category.query.filter_by(CategoryName='Textbooks').first()
    electronics = Category.query.filter_by(CategoryName='Electronics').first()
    lab = Category.query.filter_by(CategoryName='Lab Equipment').first()
    stationery = Category.query.filter_by(CategoryName='Stationery').first()
    study = Category.query.filter_by(CategoryName='Study Materials').first()
    sports = Category.query.filter_by(CategoryName='Sports Equipment').first()

    aarav = Student.query.filter_by(Email='aarav@campus.edu').first()
    priya = Student.query.filter_by(Email='priya@campus.edu').first()
    rohit = Student.query.filter_by(Email='rohit@campus.edu').first()
    sneha = Student.query.filter_by(Email='sneha@campus.edu').first()
    arjun = Student.query.filter_by(Email='arjun@campus.edu').first()

    if Item.query.count() == 0:
        items = [
            Item(Title='Data Structures & Algorithms', Description='Cormen CLRS 3rd Edition. Excellent condition, no highlights.', CreditValue=25, Status='Available', Condition='Good', CategoryID=textbooks.CategoryID, Owner_StudentID=aarav.StudentID),
            Item(Title='Engineering Mathematics', Description='Kreyszig Advanced Engineering Mathematics 10th Ed. Some notes in margins.', CreditValue=20, Status='Available', Condition='Fair', CategoryID=textbooks.CategoryID, Owner_StudentID=priya.StudentID),
            Item(Title='Scientific Calculator', Description='Casio FX-991EX ClassWiz. Perfect working condition with cover.', CreditValue=30, Status='Available', Condition='Good', CategoryID=electronics.CategoryID, Owner_StudentID=rohit.StudentID),
            Item(Title='Arduino Starter Kit', Description='Complete Arduino UNO R3 kit with breadboard, LEDs, sensors and wires.', CreditValue=40, Status='Available', Condition='Good', CategoryID=electronics.CategoryID, Owner_StudentID=sneha.StudentID),
            Item(Title='Chemistry Lab Coat', Description='White lab coat, size M. Used for one semester, freshly laundered.', CreditValue=10, Status='Available', Condition='Good', CategoryID=lab.CategoryID, Owner_StudentID=arjun.StudentID),
            Item(Title='Physics Lab Manual', Description='University prescribed physics lab manual with completed experiments.', CreditValue=8, Status='Available', Condition='Fair', CategoryID=study.CategoryID, Owner_StudentID=aarav.StudentID),
            Item(Title='Drawing Instruments Set', Description='Professional drafting set with compass, divider, and protractor.', CreditValue=15, Status='Available', Condition='Good', CategoryID=stationery.CategoryID, Owner_StudentID=priya.StudentID),
            Item(Title='Badminton Racket', Description='Yonex Nanoray series. Used for one season, strings in great shape.', CreditValue=20, Status='Available', Condition='Good', CategoryID=sports.CategoryID, Owner_StudentID=rohit.StudentID),
            Item(Title='Operating Systems Textbook', Description='Silberschatz, Galvin – 10th Edition. Clean, no markings.', CreditValue=22, Status='Available', Condition='New', CategoryID=textbooks.CategoryID, Owner_StudentID=sneha.StudentID),
            Item(Title='Raspberry Pi 4 Model B', Description='4GB RAM variant with case and power supply. Used for IoT project.', CreditValue=45, Status='Available', Condition='Good', CategoryID=electronics.CategoryID, Owner_StudentID=arjun.StudentID),
            Item(Title='Organic Chemistry Notes', Description='Handwritten notes covering full semester. Very detailed diagrams.', CreditValue=12, Status='Available', Condition='Good', CategoryID=study.CategoryID, Owner_StudentID=priya.StudentID),
            Item(Title='Safety Goggles', Description='Chemical-resistant lab safety goggles. Anti-fog coated.', CreditValue=8, Status='Available', Condition='Good', CategoryID=lab.CategoryID, Owner_StudentID=aarav.StudentID),
        ]

        for item in items:
            db.session.add(item)

        db.session.commit()


def seed_all():
    """Run all seeders"""
    seed_categories()
    seed_demo_data()
    print("✅ Database seeded successfully!")
