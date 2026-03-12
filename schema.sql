-- ═══════════════════════════════════════════════════════════════
-- Campus Circular Economy & Barter Exchange
-- MySQL Database Schema  |  MySQL Workbench
-- Username: root  |  Password: ROOT
-- ═══════════════════════════════════════════════════════════════

-- ─── Create & Use Database ─────────────────────────────────
CREATE DATABASE IF NOT EXISTS campus_barter;
USE campus_barter;


-- ═══════════════════════════════════════════════════════════════
--  TABLE CREATION (DDL)
-- ═══════════════════════════════════════════════════════════════

-- ─── Table 1: Student ──────────────────────────────────────
CREATE TABLE Student (
    StudentID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    CreditBalance INT DEFAULT 0
);

-- ─── Table 2: Category ─────────────────────────────────────
CREATE TABLE Category (
    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
    CategoryName VARCHAR(50) NOT NULL UNIQUE,
    Description VARCHAR(255)
);

-- ─── Table 3: Item ─────────────────────────────────────────
CREATE TABLE Item (
    ItemID INT PRIMARY KEY AUTO_INCREMENT,
    Title VARCHAR(100) NOT NULL,
    Description TEXT,
    CreditValue INT NOT NULL,
    Status ENUM('Available', 'Requested', 'Exchanged') DEFAULT 'Available',
    CategoryID INT,
    Owner_StudentID INT,
    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (Owner_StudentID) REFERENCES Student(StudentID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ─── Table 4: ExchangeTransaction ──────────────────────────
CREATE TABLE ExchangeTransaction (
    TransactionID INT PRIMARY KEY AUTO_INCREMENT,
    TransactionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Status ENUM('Pending', 'Completed', 'Cancelled') DEFAULT 'Pending',
    ItemID INT,
    Giver_StudentID INT,
    Receiver_StudentID INT,
    FOREIGN KEY (ItemID) REFERENCES Item(ItemID)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (Giver_StudentID) REFERENCES Student(StudentID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (Receiver_StudentID) REFERENCES Student(StudentID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ─── Table 5: CreditLedger ────────────────────────────────
CREATE TABLE CreditLedger (
    LedgerID INT PRIMARY KEY AUTO_INCREMENT,
    TransactionType ENUM('Credit', 'Debit') NOT NULL,
    Amount INT NOT NULL,
    EntryDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    StudentID INT,
    TransactionID INT,
    FOREIGN KEY (StudentID) REFERENCES Student(StudentID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (TransactionID) REFERENCES ExchangeTransaction(TransactionID)
        ON DELETE CASCADE ON UPDATE CASCADE
);


-- ═══════════════════════════════════════════════════════════════
--  INDEXES FOR PERFORMANCE
-- ═══════════════════════════════════════════════════════════════

CREATE INDEX idx_item_status ON Item(Status);
CREATE INDEX idx_item_category ON Item(CategoryID);
CREATE INDEX idx_item_owner ON Item(Owner_StudentID);
CREATE INDEX idx_txn_giver ON ExchangeTransaction(Giver_StudentID);
CREATE INDEX idx_txn_receiver ON ExchangeTransaction(Receiver_StudentID);
CREATE INDEX idx_txn_status ON ExchangeTransaction(Status);
CREATE INDEX idx_ledger_student ON CreditLedger(StudentID);


-- ═══════════════════════════════════════════════════════════════
--  SAMPLE DATA (DML - INSERT)
-- ═══════════════════════════════════════════════════════════════

-- Insert Categories
INSERT INTO Category (CategoryName, Description) VALUES
('Textbooks', 'Academic textbooks and reference materials'),
('Electronics', 'Calculators, tablets, and gadgets'),
('Lab Equipment', 'Lab coats, goggles, and instruments'),
('Stationery', 'Notebooks, pens, and art supplies'),
('Study Materials', 'Notes, flashcards, and study guides'),
('Sports Equipment', 'Sports gear and fitness equipment');

-- Insert Students (password: demo123 — hashed by application)
INSERT INTO Student (Name, Email, PasswordHash, CreditBalance) VALUES
('Aarav Sharma', 'aarav@campus.edu', 'scrypt:32768:8:1$placeholder$hash', 100),
('Priya Patel', 'priya@campus.edu', 'scrypt:32768:8:1$placeholder$hash', 100),
('Rohit Kumar', 'rohit@campus.edu', 'scrypt:32768:8:1$placeholder$hash', 100),
('Sneha Gupta', 'sneha@campus.edu', 'scrypt:32768:8:1$placeholder$hash', 100),
('Arjun Mehta', 'arjun@campus.edu', 'scrypt:32768:8:1$placeholder$hash', 100);

-- Insert Items
INSERT INTO Item (Title, Description, CreditValue, Status, CategoryID, Owner_StudentID) VALUES
('Data Structures & Algorithms', 'Cormen CLRS 3rd Edition. Excellent condition, no highlights.', 25, 'Available', 1, 1),
('Engineering Mathematics', 'Kreyszig Advanced Engineering Mathematics 10th Ed.', 20, 'Available', 1, 2),
('Scientific Calculator', 'Casio FX-991EX ClassWiz. Perfect working condition.', 30, 'Available', 2, 3),
('Arduino Starter Kit', 'Complete Arduino UNO R3 kit with breadboard, LEDs, sensors.', 40, 'Available', 2, 4),
('Chemistry Lab Coat', 'White lab coat, size M. Used for one semester.', 10, 'Available', 3, 5),
('Physics Lab Manual', 'University prescribed physics lab manual.', 8, 'Available', 5, 1),
('Drawing Instruments Set', 'Professional drafting set with compass and protractor.', 15, 'Available', 4, 2),
('Badminton Racket', 'Yonex Nanoray series. Used for one season.', 20, 'Available', 6, 3),
('Operating Systems Textbook', 'Silberschatz, Galvin – 10th Edition. Clean copy.', 22, 'Available', 1, 4),
('Raspberry Pi 4 Model B', '4GB RAM variant with case and power supply.', 45, 'Available', 2, 5),
('Organic Chemistry Notes', 'Handwritten notes covering full semester.', 12, 'Available', 5, 2),
('Safety Goggles', 'Chemical-resistant lab safety goggles.', 8, 'Available', 3, 1);


-- ═══════════════════════════════════════════════════════════════
--  USEFUL QUERIES (SELECT)
-- ═══════════════════════════════════════════════════════════════

-- ── Q1: View all available items with category and owner ────
SELECT i.ItemID, i.Title, i.CreditValue, i.Status,
       c.CategoryName, s.Name AS OwnerName
FROM Item i
JOIN Category c ON i.CategoryID = c.CategoryID
JOIN Student s ON i.Owner_StudentID = s.StudentID
WHERE i.Status = 'Available'
ORDER BY i.ItemID DESC;

-- ── Q2: Transaction history for a specific student (ID=1) ──
SELECT t.TransactionID, t.TransactionDate, t.Status,
       i.Title, i.CreditValue,
       g.Name AS Giver, r.Name AS Receiver
FROM ExchangeTransaction t
JOIN Item i ON t.ItemID = i.ItemID
JOIN Student g ON t.Giver_StudentID = g.StudentID
JOIN Student r ON t.Receiver_StudentID = r.StudentID
WHERE g.StudentID = 1 OR r.StudentID = 1;

-- ── Q3: Credit ledger summary per student ──────────────────
SELECT s.Name, s.CreditBalance,
       SUM(CASE WHEN cl.TransactionType = 'Credit' THEN cl.Amount ELSE 0 END) AS TotalEarned,
       SUM(CASE WHEN cl.TransactionType = 'Debit' THEN cl.Amount ELSE 0 END) AS TotalSpent
FROM Student s
LEFT JOIN CreditLedger cl ON s.StudentID = cl.StudentID
GROUP BY s.StudentID, s.Name, s.CreditBalance;

-- ── Q4: Items per category count ───────────────────────────
SELECT c.CategoryName, COUNT(i.ItemID) AS ItemCount
FROM Category c
LEFT JOIN Item i ON c.CategoryID = i.CategoryID
GROUP BY c.CategoryID, c.CategoryName;

-- ── Q5: Most traded item categories ────────────────────────
SELECT c.CategoryName,
       COUNT(t.TransactionID) AS TradeCount
FROM ExchangeTransaction t
JOIN Item i ON t.ItemID = i.ItemID
JOIN Category c ON i.CategoryID = c.CategoryID
WHERE t.Status = 'Completed'
GROUP BY c.CategoryID, c.CategoryName
ORDER BY TradeCount DESC;

-- ── Q6: Pending exchange requests (JOIN 3 tables) ──────────
SELECT t.TransactionID, t.TransactionDate,
       i.Title AS ItemTitle, i.CreditValue,
       g.Name AS GiverName, r.Name AS ReceiverName
FROM ExchangeTransaction t
JOIN Item i ON t.ItemID = i.ItemID
JOIN Student g ON t.Giver_StudentID = g.StudentID
JOIN Student r ON t.Receiver_StudentID = r.StudentID
WHERE t.Status = 'Pending';

-- ── Q7: Student with highest credit balance ────────────────
SELECT StudentID, Name, Email, CreditBalance
FROM Student
ORDER BY CreditBalance DESC
LIMIT 1;

-- ── Q8: Total number of completed exchanges ────────────────
SELECT COUNT(*) AS CompletedExchanges
FROM ExchangeTransaction
WHERE Status = 'Completed';

-- ── Q9: Items listed by a specific student (ID=1) ──────────
SELECT i.ItemID, i.Title, i.CreditValue, i.Status, c.CategoryName
FROM Item i
JOIN Category c ON i.CategoryID = c.CategoryID
WHERE i.Owner_StudentID = 1;

-- ── Q10: Credit ledger for a specific student (ID=1) ───────
SELECT cl.LedgerID, cl.TransactionType, cl.Amount, cl.EntryDate,
       t.TransactionID, t.Status AS TxnStatus
FROM CreditLedger cl
JOIN ExchangeTransaction t ON cl.TransactionID = t.TransactionID
WHERE cl.StudentID = 1
ORDER BY cl.EntryDate DESC;

-- ── Q11: Update student credit balance ─────────────────────
-- UPDATE Student SET CreditBalance = CreditBalance + 25 WHERE StudentID = 1;

-- ── Q12: Update item status ────────────────────────────────
-- UPDATE Item SET Status = 'Exchanged' WHERE ItemID = 1;

-- ── Q13: Delete an item ────────────────────────────────────
-- DELETE FROM Item WHERE ItemID = 1;

-- ── Q14: Count of items by status ──────────────────────────
SELECT Status, COUNT(*) AS ItemCount
FROM Item
GROUP BY Status;

-- ── Q15: Average credit value of items per category ────────
SELECT c.CategoryName, AVG(i.CreditValue) AS AvgCreditValue
FROM Item i
JOIN Category c ON i.CategoryID = c.CategoryID
GROUP BY c.CategoryID, c.CategoryName;
