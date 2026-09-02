# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Connect to Lakebase
# Import necessary libraries
import base64
import psycopg2
from databricks.sdk import WorkspaceClient

# Initialize workspace client
w = WorkspaceClient()

# Get Lakebase connection URL from secrets
SCOPE = "database"
KEY = "lakebase-url"

secret = w.secrets.get_secret(scope=SCOPE, key=KEY)
lakebase_url = base64.b64decode(secret.value).decode("utf-8")

print("✓ Successfully retrieved Lakebase connection URL")
print(f"  Scope: {SCOPE}")
print(f"  Key: {KEY}")

# COMMAND ----------

# DBTITLE 1,Drop Existing Tables
# Connect to Lakebase and drop tables
conn = psycopg2.connect(lakebase_url)

try:
    with conn.cursor() as cur:
        print("Dropping existing tables...")
        print()
        
        # Drop tables in correct order (child first, then parent)
        cur.execute("DROP TABLE IF EXISTS ticket_messages CASCADE")
        print("✓ Dropped table: ticket_messages")
        
        cur.execute("DROP TABLE IF EXISTS tickets CASCADE")
        print("✓ Dropped table: tickets")
        
        conn.commit()
        print()
        print("✓ All tables dropped successfully!")
        print()
        print("Next step: Redeploy your app so it can recreate the tables with proper ownership.")
        
finally:
    conn.close()

# COMMAND ----------

# DBTITLE 1,Verify Tables are Dropped
# Verify tables no longer exist
conn = psycopg2.connect(lakebase_url)

try:
    with conn.cursor() as cur:
        # Query to list all tables in the public schema
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        
        print("Current tables in database:")
        print()
        
        if not tables:
            print("  (No tables found - drop was successful!)")
        else:
            for table in tables:
                print(f"  - {table[0]}")
            
            # Check if our specific tables still exist
            table_names = [t[0] for t in tables]
            if 'tickets' in table_names or 'ticket_messages' in table_names:
                print()
                print("⚠️  WARNING: Some ticket tables still exist!")
            else:
                print()
                print("✓ ticket and ticket_messages tables successfully removed")
finally:
    conn.close()