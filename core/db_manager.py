import sqlite3
import os
import pandas as pd
from core.security import SecurityManager

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
                user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT NOT NULL UNIQUE,
                password  TEXT NOT NULL,
                role      TEXT NOT NULL DEFAULT 'staff'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                trans_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                date       TEXT NOT NULL,
                donor_name TEXT,
                category   TEXT NOT NULL,
                amount     REAL NOT NULL,
                type       TEXT NOT NULL DEFAULT 'INFLOW',
                remarks    TEXT,
                user_id    INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mass_intentions (
                intention_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                trans_id       INTEGER,
                intention_type TEXT,
                offered_for    TEXT,
                mass_date      TEXT,
                mass_time      TEXT,
                FOREIGN KEY (trans_id) REFERENCES transactions(trans_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date   TEXT,
                recurring  INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                log_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER,
                action    TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details   TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                expense_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                date         TEXT NOT NULL,
                category     TEXT NOT NULL,
                amount       REAL NOT NULL,
                reason       TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'PENDING',
                submitted_by TEXT,
                approved_by  TEXT,
                approved_at  TEXT
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            """, ("admin", SecurityManager.hash_password("admin123"), "admin"))
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            """, ("staff", SecurityManager.hash_password("staff123"), "staff"))

        conn.commit()
        conn.close()

    def validate_login(self, username, password):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password, role FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            stored_hash, role = result
            if SecurityManager.verify_password(password, stored_hash):
                return role
        return None

    def get_historical_data(self):
        conn = self._get_connection()
        df = pd.read_sql_query(
            """
            SELECT date, donor_name, category, amount
            FROM transactions
            WHERE type = 'INFLOW'
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
            WHERE type = 'INFLOW'
        """)
        total_donations = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE status = 'APPROVED'
        """)
        total_expenses = cursor.fetchone()[0]

        net_balance = total_donations - total_expenses

        cursor.execute("""
            SELECT COUNT(*) FROM events
            WHERE start_date >= date('now')
            AND start_date <= date('now', '+7 days')
        """)
        events_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM expenses
            WHERE status = 'PENDING'
        """)
        pending_expenses = cursor.fetchone()[0]

        conn.close()
        return {
            "total_donations":  "₱ {:,.0f}".format(total_donations),
            "total_expenses":   "₱ {:,.0f}".format(total_expenses),
            "net_balance":      "₱ {:,.0f}".format(net_balance),
            "net_balance_raw":  net_balance,
            "events_count":     str(events_count),
            "pending_expenses": str(pending_expenses),
            "forecast":         "Stable"
        }

    def get_recent_transactions(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date(date), donor_name, category, amount
            FROM transactions
            WHERE type = 'INFLOW'
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
            SELECT date(date), donor_name, category, amount, remarks
            FROM transactions
            WHERE type = 'INFLOW'
            ORDER BY date DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_transactions_by_range(self, start_date, end_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date(date), donor_name, category, amount, remarks
            FROM transactions
            WHERE type = 'INFLOW'
            AND date(date) BETWEEN ? AND ?
            ORDER BY date ASC
        """, (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_summary_by_range(self, start_date, end_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE type = 'INFLOW'
            AND date(date) BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
        """, (start_date, end_date))
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
        import datetime
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_trail (user_id, action, timestamp, details)
            VALUES (?, ?, ?, ?)
        """, (user_id, action,
              datetime.datetime.now().isoformat(), details))
        conn.commit()
        conn.close()

    def save_transaction(self, date, donor_name, category,
                         amount, remarks="", user_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions
                (date, donor_name, category, amount, type, remarks, user_id)
            VALUES (?, ?, ?, ?, 'INFLOW', ?, ?)
        """, (date, donor_name, category, amount, remarks, user_id))
        trans_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return trans_id

    def create_user(self, username, password, role="staff"):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (username, SecurityManager.hash_password(password), role))
        conn.commit()
        conn.close()

    def get_monthly_summary(self):
        conn = self._get_connection()
        df = pd.read_sql_query("""
            SELECT
                strftime('%Y-%m', date) as month,
                category,
                SUM(amount) as total
            FROM transactions
            WHERE type = 'INFLOW'
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
        cursor = conn.cursor()

        inserted = 0
        skipped  = 0

        for _, row in df.iterrows():
            cursor.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE date(date) = date(?)
                AND donor_name   = ?
                AND category     = ?
                AND amount       = ?
            """, (
                str(row["date"])[:10],
                str(row.get("donor_name", "")),
                str(row["category"]),
                float(row["amount"])
            ))
            exists = cursor.fetchone()[0]

            if exists == 0:
                cursor.execute("""
                    INSERT INTO transactions
                        (date, donor_name, category,
                         amount, type, remarks)
                    VALUES (?, ?, ?, ?, 'INFLOW', ?)
                """, (
                    str(row["date"])[:10],
                    str(row.get("donor_name", "")),
                    str(row["category"]),
                    float(row["amount"]),
                    str(row.get("remarks", ""))
                ))
                inserted += 1
            else:
                skipped += 1

        conn.commit()
        conn.close()

        print("Import complete — " + str(inserted) +
              " new records added, " + str(skipped) +
              " duplicates skipped.")
        return inserted, skipped

    # ─── EXPENSE METHODS ───────────────────────────────

    def save_expense_request(self, date, category, amount,
                              reason, submitted_by=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses
                (date, category, amount, reason,
                 status, submitted_by)
            VALUES (?, ?, ?, ?, 'PENDING', ?)
        """, (date, category, amount, reason, submitted_by))
        expense_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return expense_id

    def approve_expense(self, expense_id, approved_by):
        import datetime
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE expenses
            SET status      = 'APPROVED',
                approved_by = ?,
                approved_at = ?
            WHERE expense_id = ?
        """, (approved_by,
              datetime.datetime.now().isoformat(),
              expense_id))
        conn.commit()
        conn.close()

    def reject_expense(self, expense_id, approved_by):
        import datetime
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE expenses
            SET status      = 'REJECTED',
                approved_by = ?,
                approved_at = ?
            WHERE expense_id = ?
        """, (approved_by,
              datetime.datetime.now().isoformat(),
              expense_id))
        conn.commit()
        conn.close()

    def get_pending_expenses(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT expense_id, date, category,
                   amount, reason, submitted_by
            FROM expenses
            WHERE status = 'PENDING'
            ORDER BY date DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_approved_expenses(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT expense_id, date, category,
                   amount, reason, approved_by, approved_at
            FROM expenses
            WHERE status = 'APPROVED'
            ORDER BY date DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_expenses(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT expense_id, date, category,
                   amount, reason, status,
                   submitted_by, approved_by
            FROM expenses
            ORDER BY date DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_expense_historical_data(self):
        conn = self._get_connection()
        df = pd.read_sql_query("""
            SELECT date, category, amount
            FROM expenses
            WHERE status = 'APPROVED'
            ORDER BY date ASC
        """, conn, parse_dates=["date"])
        conn.close()
        return df

    def get_expense_summary_by_range(self, start_date, end_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE status = 'APPROVED'
            AND date(date) BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
        """, (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_net_balance(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions WHERE type = 'INFLOW'
        """)
        total_income = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses WHERE status = 'APPROVED'
        """)
        total_expenses = cursor.fetchone()[0]
        conn.close()
        return {
            "income":   total_income,
            "expenses": total_expenses,
            "balance":  total_income - total_expenses
        }

    def get_monthly_expenses(self):
        conn = self._get_connection()
        df = pd.read_sql_query("""
            SELECT
                strftime('%Y-%m', date) as month,
                category,
                SUM(amount) as total
            FROM expenses
            WHERE status = 'APPROVED'
            GROUP BY month, category
            ORDER BY month ASC
        """, conn)
        conn.close()
        return df