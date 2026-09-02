# Support Ticketing System

## Overview

A full-stack support ticketing management system built on Databricks, combining Lakebase Postgres for operational data storage with a modern web interface for ticket management and team collaboration.

**Live Application**: [https://support-ticket-management-7474648501724161.aws.databricksapps.com](https://support-ticket-management-7474648501724161.aws.databricksapps.com)

## Purpose

This application demonstrates a production-ready support ticketing system that enables:

* **Ticket Management**: Create, track, and resolve customer support tickets with status workflows (open, in progress, resolved, closed)
* **Conversation Threads**: Maintain full message history and team collaboration on each ticket
* **Real-time Updates**: Track ticket creation, updates, and resolution in real-time
* **Customer Service Operations**: Streamline support workflows for teams handling customer inquiries

## Repository Structure

### `schema.sql`
Complete Lakebase Postgres database schema including:
* **tickets** table: Core ticket tracking with status, creator, and timestamps
* **ticket_messages** table: Conversation threads linked to tickets
* Sample data with realistic support scenarios
* Verification queries for testing

### Key Features

* **PostgreSQL-backed**: Uses Lakebase Postgres for ACID-compliant transactional data
* **Relational Integrity**: Foreign key constraints and cascade deletes
* **Performance Optimized**: Indexed lookups for fast message retrieval
* **Status Workflow**: Enforced ticket status transitions with check constraints
* **Audit Trail**: Timestamped records for all tickets and messages

## Technology Stack

* **Database**: Databricks Lakebase Postgres (Autoscaling)
* **Application**: Databricks App
* **Schema**: PostgreSQL DDL with sample data
* **Cloud**: AWS

## Getting Started

1. Deploy the schema using `schema.sql` to your Lakebase Postgres instance
2. Configure the Databricks App connection to your Lakebase endpoint
3. Access the application at the URL above

---

*Built as part of DataExpert Homework - Day 1*