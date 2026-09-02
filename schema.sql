-- ============================================
-- Support Ticketing System Database Schema
-- Lakebase Postgres Schema & Sample Data
-- ============================================

-- Drop existing tables if they exist (for clean re-runs)
DROP TABLE IF EXISTS ticket_messages CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;

-- ============================================
-- Table: tickets
-- ============================================
CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_status CHECK (status IN ('open', 'in_progress', 'resolved', 'closed'))
);

-- ============================================
-- Table: ticket_messages
-- ============================================
CREATE TABLE ticket_messages (
    message_id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    author VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON DELETE CASCADE
);

-- Create index for faster ticket message lookups
CREATE INDEX idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);

-- ============================================
-- Sample Data: Tickets
-- ============================================
INSERT INTO tickets (title, status, created_by, created_at) VALUES
    ('Unable to access dashboard', 'open', 'alice@company.com', '2024-01-15 09:30:00'),
    ('Query performance is slow', 'in_progress', 'bob@company.com', '2024-01-14 14:20:00'),
    ('Need help with SQL syntax', 'resolved', 'charlie@company.com', '2024-01-13 11:15:00'),
    ('Data pipeline failing', 'open', 'diana@company.com', '2024-01-16 08:45:00'),
    ('Request for new feature', 'in_progress', 'eve@company.com', '2024-01-12 16:30:00');

-- ============================================
-- Sample Data: Ticket Messages
-- ============================================
-- Messages for Ticket 1: Unable to access dashboard
INSERT INTO ticket_messages (ticket_id, message_text, author, created_at) VALUES
    (1, 'I''m getting a 403 error when trying to open the sales dashboard. Can you help?', 'alice@company.com', '2024-01-15 09:30:00'),
    (1, 'Thanks for reporting this. I''m investigating the permissions now.', 'support@company.com', '2024-01-15 10:15:00'),
    (1, 'It looks like your user group was accidentally removed. Adding you back now.', 'support@company.com', '2024-01-15 10:45:00');

-- Messages for Ticket 2: Query performance is slow
INSERT INTO ticket_messages (ticket_id, message_text, author, created_at) VALUES
    (2, 'My daily aggregation query used to take 2 minutes, now it takes over 20 minutes.', 'bob@company.com', '2024-01-14 14:20:00'),
    (2, 'Can you share the query? We''ll check if there are optimization opportunities.', 'support@company.com', '2024-01-14 15:00:00'),
    (2, 'I''ve attached the query. It joins 3 large tables with date filters.', 'bob@company.com', '2024-01-14 15:30:00'),
    (2, 'Found the issue - missing index on the date column. Adding it now and testing.', 'support@company.com', '2024-01-15 09:00:00');

-- Messages for Ticket 3: Need help with SQL syntax
INSERT INTO ticket_messages (ticket_id, message_text, author, created_at) VALUES
    (3, 'How do I write a window function to calculate running totals in Databricks SQL?', 'charlie@company.com', '2024-01-13 11:15:00'),
    (3, 'You can use: SUM(amount) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING). Let me know if that helps!', 'support@company.com', '2024-01-13 11:45:00'),
    (3, 'Perfect! That worked exactly as I needed. Thank you!', 'charlie@company.com', '2024-01-13 12:00:00');

-- Messages for Ticket 4: Data pipeline failing
INSERT INTO ticket_messages (ticket_id, message_text, author, created_at) VALUES
    (4, 'Our nightly ETL pipeline has failed for the past 2 days. Error: connection timeout.', 'diana@company.com', '2024-01-16 08:45:00'),
    (4, 'Looking into this. Can you confirm which pipeline and workspace?', 'support@company.com', '2024-01-16 09:30:00');

-- Messages for Ticket 5: Request for new feature
INSERT INTO ticket_messages (ticket_id, message_text, author, created_at) VALUES
    (5, 'Would be great to have automated email alerts when dashboard data refreshes.', 'eve@company.com', '2024-01-12 16:30:00'),
    (5, 'Great suggestion! I''ve added this to our feature backlog for Q2 planning.', 'support@company.com', '2024-01-13 10:00:00'),
    (5, 'Thanks! Looking forward to it. Any workaround in the meantime?', 'eve@company.com', '2024-01-13 14:30:00');

-- ============================================
-- Verification Queries
-- ============================================
-- Run these after creating the schema to verify:

-- Count tickets by status
-- SELECT status, COUNT(*) as count FROM tickets GROUP BY status ORDER BY status;

-- Count messages per ticket
-- SELECT t.ticket_id, t.title, COUNT(tm.message_id) as message_count
-- FROM tickets t
-- LEFT JOIN ticket_messages tm ON t.ticket_id = tm.ticket_id
-- GROUP BY t.ticket_id, t.title
-- ORDER BY t.ticket_id;

-- View all tickets with their latest message
-- SELECT 
--     t.ticket_id,
--     t.title,
--     t.status,
--     t.created_by,
--     t.created_at as ticket_created,
--     tm.message_text as latest_message,
--     tm.created_at as message_created
-- FROM tickets t
-- LEFT JOIN LATERAL (
--     SELECT message_text, created_at
--     FROM ticket_messages
--     WHERE ticket_id = t.ticket_id
--     ORDER BY created_at DESC
--     LIMIT 1
-- ) tm ON true
-- ORDER BY t.created_at DESC;