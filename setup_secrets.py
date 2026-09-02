"""
One-time script to store your Lakebase connection URL in Databricks Secrets.

Run this once from a Databricks notebook or cluster terminal:
    python setup_secrets.py

It will prompt you for your Lakebase connection URL and store it base64-encoded
in the secret scope 'database' with key 'lakebase-url'.
"""

import base64
import getpass
import sys

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

SCOPE = "database"
KEY = "lakebase-url"


def ensure_scope_exists(scope_name: str):
    """Create the secret scope if it doesn't exist."""
    try:
        existing_scopes = [s.name for s in w.secrets.list_scopes()]
        if scope_name not in existing_scopes:
            print(f"Creating secret scope: {scope_name}")
            w.secrets.create_scope(scope=scope_name)
        else:
            print(f"Secret scope '{scope_name}' already exists.")
    except Exception as e:
        print(f"Error checking/creating scope: {e}")
        sys.exit(1)


def store_secret(scope: str, key: str, value: str):
    """Store a secret (base64-encoded) in Databricks."""
    encoded_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
    try:
        w.secrets.put_secret(scope=scope, key=key, string_value=encoded_value)
        print(f"✓ Stored secret: {scope}/{key}")
    except Exception as e:
        print(f"Error storing secret: {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("Lakebase Connection URL Setup")
    print("=" * 60)
    print()
    print("You need your Lakebase connection URL in this format:")
    print("  postgresql://role:password@host:5432/databricks_postgres?sslmode=require")
    print()
    print("Get this from your Lakebase instance UI:")
    print("  1. Open your Lakebase instance in Databricks")
    print("  2. Go to 'Roles & Databases' tab")
    print("  3. Copy the connection URL for your role")
    print()

    # Ensure scope exists
    ensure_scope_exists(SCOPE)

    # Prompt for Lakebase URL (hidden input)
    lakebase_url = getpass.getpass("Enter your Lakebase connection URL: ").strip()

    if not lakebase_url.startswith("postgresql://"):
        print("Error: URL should start with 'postgresql://'")
        sys.exit(1)

    # Store the secret
    store_secret(SCOPE, KEY, lakebase_url)

    print()
    print("=" * 60)
    print("Setup complete! Your app can now connect to Lakebase.")
    print("=" * 60)


if __name__ == "__main__":
    main()