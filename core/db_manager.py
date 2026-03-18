import sqlite3
import os
import pandas as pd

DB_PATH = "churchtrack.db"


class DatabaseManager:

    def __init__(self):
        self.db_path = DB_PATH
        self._init_database()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT NOT NULL UNIQUE,
                password    TEXT NOT NULL,
                role        TEXT NOT NULL DEFAULT 'staff'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                trans_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                donor_name  TEXT,
                category    TEXT NOT NULL,
                amount      REAL NOT NULL,
                type        TEXT NOT NULL DEFAULT 'INFLOW',
                remarks     TEXT,
                user_id     INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mass_intentions (
                intention_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                trans_id        INTEGER,
                intention_type  TEXT,
                offered_for     TEXT,
                mass_date       TEXT,
                mass_time       TEXT,
                FOREIGN KEY (trans_id) REFERENCES transactions(trans_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                start_date  TEXT NOT NULL,
                end_date    TEXT,
                recurring   INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                action      TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                details     TEXT
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES ('admin', 'admin123', 'admin')
            """)
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES ('staff', 'staff123', 'staff')
            """)

        conn.commit()
        conn.close()

    def validate_login(self, username, password):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_historical_data(self):
        conn = self._get_connection()
        df = pd.read_sql_query(
            """
            SELECT date, donor_name, category, amount
            FROM transactions
            WHERE type='INFLOW'
            ORDER BY date ASC
            """,
            conn,
            parse_dates=["date"]
        )
        conn.close()
        return df

    def get_kpi_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE type='INFLOW'
        """)
        total_donations = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM events
            WHERE start_date >= date('now')
            AND start_date <= date('now', '+7 days')
        """)
        events_count = cursor.fetchone()[0]

        conn.close()
        return {
            "total_donations": "₱ {:,.0f}".format(total_donations),
            "events_count":    str(events_count),
            "forecast":        "Stable"
        }

    def get_recent_transactions(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                date(date) as date,
                donor_name,
                category,
                amount
            FROM transactions
            WHERE type='INFLOW'
            ORDER BY date DESC
            LIMIT 20
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_transactions(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                date(date) as date,
                donor_name,
                category,
                amount,
                remarks
            FROM transactions
            WHERE type='INFLOW'
            ORDER BY date DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_audit_trail(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT log_id, user_id, action, timestamp, details
            FROM audit_trail
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def log_action(self, user_id, action, details=""):
        conn = self._get_connection()
        cursor = conn.cursor()
        import datetime
        cursor.execute("""
            INSERT INTO audit_trail (user_id, action, timestamp, details)
            VALUES (?, ?, ?, ?)
        """, (user_id, action, datetime.datetime.now().isoformat(), details))
        conn.commit()
        conn.close()

    def save_transaction(self, date, donor_name, category, amount, remarks="", user_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (date, donor_name, category, amount, type, remarks, user_id)
            VALUES (?, ?, ?, ?, 'INFLOW', ?, ?)
        """, (date, donor_name, category, amount, remarks, user_id))
        trans_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return trans_id

    def get_monthly_summary(self):
        conn = self._get_connection()
        df = pd.read_sql_query("""
            SELECT
                strftime('%Y-%m', date) as month,
                category,
                SUM(amount) as total
            FROM transactions
            WHERE type='INFLOW'
            GROUP BY month, category
            ORDER BY month ASC
        """, conn)
        conn.close()
        return df

    def import_from_excel(self, filepath):
        from core.ai_engine import load_from_excel
        df = load_from_excel(filepath)
        df["type"] = "INFLOW"
        conn = self._get_connection()
        df.to_sql("transactions", conn, if_exists="append", index=False)
        conn.close()
        print("Imported " + str(len(df)) + " records from " + filepath)