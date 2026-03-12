-- ═══════════════════════════════════════════════════════════════
-- Campus Circular Economy & Barter Exchange
-- MySQL Database Schema
-- ═══════════════════════════════════════════════════════════════

-- Create Database
CREATE DATABASE IF NOT EXISTS campus_barter;
USE campus_barter;

-- ─── Table 1: Student ───────────────────────────────────────
CREATE TABLE Student (
    StudentID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    CreditBalance INT DEFAULT 100,
    JoinDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Avatar VARCHAR(10) DEFAULT '🎓'
);

-- ─── Table 2: Category ──────────────────────────────────────
CREATE TABLE Category (
    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
    CategoryName VARCHAR(50) NOT NULL UNIQUE,
    Description VARCHAR(255),
    Icon VARCHAR(10) DEFAULT '📦'
);

-- ─── Table 3: Item ──────────────────────────────────────────
CREATE TABLE Item (
    ItemID INT PRIMARY KEY AUTO_INCREMENT,
    Title VARCHAR(100) NOT NULL,
    Description TEXT,
    CreditValue INT NOT NULL,
    Status ENUM('Available', 'Requested', 'Exchanged') DEFAULT 'Available',
    `Condition` VARCHAR(20) DEFAULT 'Good',
    ImageURL VARCHAR(255),
    ListedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    CategoryID INT NOT NULL,
    Owner_StudentID INT NOT NULL,
    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (Owner_StudentID) REFERENCES Student(StudentID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ─── Table 4: ExchangeTransaction ───────────────────────────
CREATE TABLE ExchangeTransaction (
    TransactionID INT PRIMARY KEY AUTO_INCREMENT,
    TransactionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Status ENUM('Pending', 'Completed', 'Cancelled') DEFAULT 'Pending',
    CompletedDate DATETIME,
    ItemID INT NOT NULL,
    Giver_StudentID INT NOT NULL,
    Receiver_StudentID INT NOT NULL,
    FOREIGN KEY (ItemID) REFERENCES Item(ItemID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (Giver_StudentID) REFERENCES Student(StudentID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (Receiver_StudentID) REFERENCES Student(StudentID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    -- Constraint: A student cannot exchange with themselves
    CHECK (Giver_StudentID != Receiver_StudentID)
);

-- ─── Table 5: CreditLedger ─────────────────────────────────
CREATE TABLE CreditLedger (
    LedgerID INT PRIMARY KEY AUTO_INCREMENT,
    TransactionType ENUM('Credit', 'Debit') NOT NULL,
    Amount INT NOT NULL,
    EntryDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    BalanceAfter INT NOT NULL,
    StudentID INT NOT NULL,
    TransactionID INT NOT NULL,
    FOREIGN KEY (StudentID) REFERENCES Student(StudentID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (TransactionID) REFERENCES ExchangeTransaction(TransactionID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ═══════════════════════════════════════════════════════════════
-- INDEXES for Performance
-- ═══════════════════════════════════════════════════════════════

CREATE INDEX idx_item_status ON Item(Status);
CREATE INDEX idx_item_category ON Item(CategoryID);
CREATE INDEX idx_item_owner ON Item(Owner_StudentID);
CREATE INDEX idx_txn_giver ON ExchangeTransaction(Giver_StudentID);
CREATE INDEX idx_txn_receiver ON ExchangeTransaction(Receiver_StudentID);
CREATE INDEX idx_txn_status ON ExchangeTransaction(Status);
CREATE INDEX idx_ledger_student ON CreditLedger(StudentID);

-- ═══════════════════════════════════════════════════════════════
-- SAMPLE DATA
-- ═══════════════════════════════════════════════════════════════

-- Categories
INSERT INTO Category (CategoryName, Description, Icon) VALUES
('Textbooks', 'Academic textbooks and reference materials', '📚'),
('Electronics', 'Calculators, tablets, and gadgets', '💻'),
('Lab Equipment', 'Lab coats, goggles, and instruments', '🔬'),
('Stationery', 'Notebooks, pens, and art supplies', '✏️'),
('Study Materials', 'Notes, flashcards, and study guides', '📝'),
('Sports Equipment', 'Sports gear and fitness equipment', '⚽');

-- Students (password: demo123)
INSERT INTO Student (Name, Email, PasswordHash, CreditBalance, Avatar) VALUES
('Aarav Sharma', 'aarav@campus.edu', 'scrypt:32768:8:1$salt$hash', 100, '🧑‍💻'),
('Priya Patel', 'priya@campus.edu', 'scrypt:32768:8:1$salt$hash', 100, '👩‍🔬'),
('Rohit Kumar', 'rohit@campus.edu', 'scrypt:32768:8:1$salt$hash', 100, '👨‍🎓'),
('Sneha Gupta', 'sneha@campus.edu', 'scrypt:32768:8:1$salt$hash', 100, '👩‍💻'),
('Arjun Mehta', 'arjun@campus.edu', 'scrypt:32768:8:1$salt$hash', 100, '🧑‍🎓');

-- ═══════════════════════════════════════════════════════════════
-- USEFUL QUERIES
-- ═══════════════════════════════════════════════════════════════

-- 1. View all available items with category and owner
-- SELECT i.ItemID, i.Title, i.CreditValue, i.Status,
--        c.CategoryName, s.Name AS Owner
-- FROM Item i
-- JOIN Category c ON i.CategoryID = c.CategoryID
-- JOIN Student s ON i.Owner_StudentID = s.StudentID
-- WHERE i.Status = 'Available'
-- ORDER BY i.ListedDate DESC;

-- 2. Transaction history for a specific student
-- SELECT t.TransactionID, t.TransactionDate, t.Status,
--        i.Title, i.CreditValue,
--        g.Name AS Giver, r.Name AS Receiver
-- FROM ExchangeTransaction t
-- JOIN Item i ON t.ItemID = i.ItemID
-- JOIN Student g ON t.Giver_StudentID = g.StudentID
-- JOIN Student r ON t.Receiver_StudentID = r.StudentID
-- WHERE g.StudentID = 1 OR r.StudentID = 1;

-- 3. Credit ledger summary
-- SELECT s.Name, s.CreditBalance,
--        SUM(CASE WHEN cl.TransactionType = 'Credit' THEN cl.Amount ELSE 0 END) AS TotalEarned,
--        SUM(CASE WHEN cl.TransactionType = 'Debit' THEN cl.Amount ELSE 0 END) AS TotalSpent
-- FROM Student s
-- LEFT JOIN CreditLedger cl ON s.StudentID = cl.StudentID
-- GROUP BY s.StudentID;

-- 4. Items per category count
-- SELECT c.CategoryName, c.Icon, COUNT(i.ItemID) AS ItemCount
-- FROM Category c
-- LEFT JOIN Item i ON c.CategoryID = i.CategoryID
-- GROUP BY c.CategoryID;

-- 5. Most traded item categories
-- SELECT c.CategoryName,
--        COUNT(t.TransactionID) AS TradeCount
-- FROM ExchangeTransaction t
-- JOIN Item i ON t.ItemID = i.ItemID
-- JOIN Category c ON i.CategoryID = c.CategoryID
-- WHERE t.Status = 'Completed'
-- GROUP BY c.CategoryID
-- ORDER BY TradeCount DESC;
