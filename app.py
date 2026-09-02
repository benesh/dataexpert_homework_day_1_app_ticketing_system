"""
Support Ticketing System - Databricks App

A Flask application that manages support tickets and messages, backed by Lakebase.

Features:
- View all support tickets
- View ticket details with messages
- Create new tickets
- Add messages to tickets
- Update ticket status
"""

import logging
import os
from datetime import datetime

from databricks.sdk import WorkspaceClient
from flask import Flask, jsonify, render_template, request

import lakebase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ticketing-app")

app = Flask(__name__)
_w = WorkspaceClient()


def ensure_tables():
    """Create the tickets and ticket_messages tables if they don't exist."""
    lakebase.run_write(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_by VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT check_status CHECK (status IN ('open', 'in_progress', 'resolved', 'closed'))
        )
        """
    )
    
    lakebase.run_write(
        """
        CREATE TABLE IF NOT EXISTS ticket_messages (
            message_id SERIAL PRIMARY KEY,
            ticket_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            author VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_ticket
                FOREIGN KEY (ticket_id)
                REFERENCES tickets(ticket_id)
                ON DELETE CASCADE
        )
        """
    )
    
    # Create index if it doesn't exist
    try:
        lakebase.run_write(
            "CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket_id ON ticket_messages(ticket_id)"
        )
    except Exception as e:
        # Index might already exist, ignore
        logger.info(f"Index creation info: {e}")


def ensure_sample_data():
    """Insert sample tickets and messages if the database is empty."""
    # Check if we already have data
    existing = lakebase.run_query("SELECT COUNT(*) as count FROM tickets")
    if existing and existing[0].get('count', 0) > 0:
        logger.info("Sample data already exists, skipping initialization")
        return
    
    logger.info("Inserting sample data...")
    
    # Sample tickets with different statuses
    sample_tickets = [
        ('Unable to access dashboard', 'open', 'alice@company.com'),
        ('Query performance is slow', 'in_progress', 'bob@company.com'),
        ('Need help with SQL syntax', 'resolved', 'charlie@company.com'),
        ('Data pipeline failing', 'open', 'diana@company.com'),
        ('Request for new feature', 'in_progress', 'eve@company.com'),
    ]
    
    # Sample messages for each ticket (ticket_number -> list of (message_text, author))
    sample_messages = {
        1: [
            ("I'm getting a 403 error when trying to open the sales dashboard. Can you help?", 'alice@company.com'),
            ("Thanks for reporting this. I'm investigating the permissions now.", 'support@company.com'),
            ("It looks like your user group was accidentally removed. Adding you back now.", 'support@company.com'),
        ],
        2: [
            ("My daily aggregation query used to take 2 minutes, now it takes over 20 minutes.", 'bob@company.com'),
            ("Can you share the query? We'll check if there are optimization opportunities.", 'support@company.com'),
            ("I've attached the query. It joins 3 large tables with date filters.", 'bob@company.com'),
            ("Found the issue - missing index on the date column. Adding it now and testing.", 'support@company.com'),
        ],
        3: [
            ("How do I write a window function to calculate running totals in Databricks SQL?", 'charlie@company.com'),
            ("You can use: SUM(amount) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING). Let me know if that helps!", 'support@company.com'),
            ("Perfect! That worked exactly as I needed. Thank you!", 'charlie@company.com'),
        ],
        4: [
            ("Our nightly ETL pipeline has failed for the past 2 days. Error: connection timeout.", 'diana@company.com'),
            ("Looking into this. Can you confirm which pipeline and workspace?", 'support@company.com'),
        ],
        5: [
            ("Would be great to have automated email alerts when dashboard data refreshes.", 'eve@company.com'),
            ("Great suggestion! I've added this to our feature backlog for Q2 planning.", 'support@company.com'),
            ("Thanks! Looking forward to it. Any workaround in the meantime?", 'eve@company.com'),
        ],
    }
    
    with lakebase.get_connection() as conn:
        with conn.cursor() as cur:
            # Insert tickets
            for title, status, created_by in sample_tickets:
                cur.execute(
                    """
                    INSERT INTO tickets (title, status, created_by)
                    VALUES (%s, %s, %s)
                    RETURNING ticket_id
                    """,
                    (title, status, created_by)
                )
                ticket_id = cur.fetchone()['ticket_id']
                
                # Insert messages for this ticket
                messages = sample_messages.get(ticket_id, [])
                for message_text, author in messages:
                    cur.execute(
                        """
                        INSERT INTO ticket_messages (ticket_id, message_text, author)
                        VALUES (%s, %s, %s)
                        """,
                        (ticket_id, message_text, author)
                    )
            
            conn.commit()
    
    logger.info(f"Sample data inserted: {len(sample_tickets)} tickets with messages")


def _current_user_email() -> str:
    """
    Resolve the current user's email for tracking ticket creators.
    
    Databricks Apps inject the logged-in user's identity via the
    X-Forwarded-Email header. Fall back to SDK for local development.
    """
    header_email = request.headers.get("X-Forwarded-Email")
    if header_email:
        return header_email
    return _w.current_user.me().user_name


@app.route("/healthz")
def healthz():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@app.errorhandler(Exception)
def handle_exception(err):
    """Ensure all unhandled errors return JSON, not HTML error pages."""
    logger.exception("Unhandled exception while processing request")
    status_code = getattr(err, "code", 500)
    if not isinstance(status_code, int):
        status_code = 500
    return jsonify({"error": str(err)}), status_code


@app.route("/")
def index():
    """Serve the main UI for managing support tickets."""
    return render_template("index.html")


# ============================================
# Ticket Endpoints
# ============================================

# Initialize tables on startup
with app.app_context():
    try:
        ensure_tables()
        logger.info("Tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize tables: {e}")


@app.route("/tickets", methods=["GET"])
def list_tickets():
    """
    Get all support tickets, ordered by creation date (newest first).
    
    Returns: list[dict] with ticket details
    """
    rows = lakebase.run_query(
        """
        SELECT ticket_id, title, status, created_by, created_at
        FROM tickets
        ORDER BY created_at DESC
        """
    )
    return jsonify(rows)


@app.route("/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    """
    Get a specific ticket with all its messages.
    
    Returns: dict with ticket details and messages array
    """
    # Get ticket details
    ticket_rows = lakebase.run_query(
        """
        SELECT ticket_id, title, status, created_by, created_at
        FROM tickets
        WHERE ticket_id = %s
        """,
        (ticket_id,)
    )
    
    if not ticket_rows:
        return jsonify({"error": "Ticket not found"}), 404
    
    ticket = ticket_rows[0]
    
    # Get messages for this ticket
    messages = lakebase.run_query(
        """
        SELECT message_id, ticket_id, message_text, author, created_at
        FROM ticket_messages
        WHERE ticket_id = %s
        ORDER BY created_at ASC
        """,
        (ticket_id,)
    )
    
    ticket["messages"] = messages
    return jsonify(ticket)


@app.route("/tickets", methods=["POST"])
def create_ticket():
    """
    Create a new support ticket.
    
    Expected JSON body:
    {
        "title": "Ticket title",
        "status": "open"  # optional, defaults to 'open'
    }
    
    Returns: newly created ticket with ticket_id
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    title = data.get("title", "").strip()
    status = data.get("status", "open").strip().lower()
    
    # Validation
    if not title:
        return jsonify({"error": "Title is required"}), 400
    
    if status not in ["open", "in_progress", "resolved", "closed"]:
        return jsonify({"error": "Invalid status. Must be: open, in_progress, resolved, or closed"}), 400
    
    # Get current user
    created_by = _current_user_email()
    
    # Insert ticket and return it (use direct connection for RETURNING with commit)
    with lakebase.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tickets (title, status, created_by)
                VALUES (%s, %s, %s)
                RETURNING ticket_id, title, status, created_by, created_at
                """,
                (title, status, created_by)
            )
            result = cur.fetchall()
            conn.commit()
    
    return jsonify(result[0]), 201


@app.route("/tickets/<int:ticket_id>/messages", methods=["POST"])
def add_message(ticket_id):
    """
    Add a message to an existing ticket.
    
    Expected JSON body:
    {
        "message_text": "Message content"
    }
    
    Returns: newly created message with message_id
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    message_text = data.get("message_text", "").strip()
    
    # Validation
    if not message_text:
        return jsonify({"error": "Message text is required"}), 400
    
    # Verify ticket exists
    ticket_check = lakebase.run_query(
        "SELECT ticket_id FROM tickets WHERE ticket_id = %s",
        (ticket_id,)
    )
    
    if not ticket_check:
        return jsonify({"error": "Ticket not found"}), 404
    
    # Get current user
    author = _current_user_email()
    
    # Insert message and return it (use direct connection for RETURNING with commit)
    with lakebase.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ticket_messages (ticket_id, message_text, author)
                VALUES (%s, %s, %s)
                RETURNING message_id, ticket_id, message_text, author, created_at
                """,
                (ticket_id, message_text, author)
            )
            result = cur.fetchall()
            conn.commit()
    
    return jsonify(result[0]), 201


@app.route("/tickets/<int:ticket_id>/status", methods=["PATCH"])
def update_status(ticket_id):
    """
    Update the status of a ticket.
    
    Expected JSON body:
    {
        "status": "in_progress"  # or "open", "resolved", "closed"
    }
    
    Returns: updated ticket
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    new_status = data.get("status", "").strip().lower()
    
    # Validation
    if not new_status:
        return jsonify({"error": "Status is required"}), 400
    
    if new_status not in ["open", "in_progress", "resolved", "closed"]:
        return jsonify({"error": "Invalid status. Must be: open, in_progress, resolved, or closed"}), 400
    
    # Update and return updated ticket (use direct connection for RETURNING with commit)
    with lakebase.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tickets
                SET status = %s
                WHERE ticket_id = %s
                RETURNING ticket_id, title, status, created_by, created_at
                """,
                (new_status, ticket_id)
            )
            result = cur.fetchall()
            conn.commit()
    
    if not result:
        return jsonify({"error": "Ticket not found"}), 404
    
    return jsonify(result[0])


if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 8000))
    app.run(debug=True, host=host, port=port)
    print(f"Flask app running on http://{host}:{port}")