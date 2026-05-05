import datetime
import sqlite3

import pandas as pd

from core.security import SecurityManager


DB_PATH = "churchtrack.db"


class DatabaseManager:

    def __init__(self):
        self.db_path = DB_PATH
        self._ai_engine = None
        self._init_database()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _now(self):
        return datetime.datetime.now().isoformat(timespec="seconds")

    def _normalize_filter(self, value):
        if value is None:
            return None
        value = str(value).strip()
        if not value or value.lower() == "all":
            return None
        return value

    def _ensure_column(self, cursor, table, column, definition):
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            if column not in columns:
                cursor.execute(
                    f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                )
        except Exception:
            pass

    def _init_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role     TEXT NOT NULL DEFAULT 'staff'
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
                FOREIGN KEY (trans_id)
                    REFERENCES transactions(trans_id)
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

        self._run_migrations(cursor)

        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            """, (
                "admin",
                SecurityManager.hash_password("admin123"),
                "admin",
            ))
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            """, (
                "staff",
                SecurityManager.hash_password("staff123"),
                "staff",
            ))

        self._init_member_tables(cursor)

        conn.commit()
        conn.close()

    # ─── MEMBER TABLES SETUP ──────────────────────────

    def _init_member_tables(self, cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS member_families (
                family_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                family_name TEXT NOT NULL,
                address     TEXT DEFAULT '',
                created_at  TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                member_id            INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name            TEXT NOT NULL,
                nickname             TEXT DEFAULT '',
                date_of_birth        TEXT,
                gender               TEXT DEFAULT '',
                civil_status         TEXT DEFAULT '',
                address              TEXT DEFAULT '',
                contact_number       TEXT DEFAULT '',
                email                TEXT DEFAULT '',
                date_joined          TEXT,
                ministry             TEXT DEFAULT '',
                role                 TEXT DEFAULT 'Member',
                is_active            INTEGER DEFAULT 1,
                family_id            INTEGER,
                is_head_of_family    INTEGER DEFAULT 0,
                baptism_date         TEXT,
                confirmation_date    TEXT,
                first_communion_date TEXT,
                marriage_date        TEXT,
                anointing_date       TEXT,
                church_wedding       INTEGER DEFAULT 0,
                notes                TEXT DEFAULT '',
                created_at           TEXT,
                FOREIGN KEY (family_id)
                    REFERENCES member_families(family_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS member_sacraments (
                sacrament_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id          INTEGER NOT NULL,
                sacrament_type     TEXT NOT NULL,
                sacrament_date     TEXT,
                officiating_priest TEXT DEFAULT '',
                location           TEXT DEFAULT '',
                notes              TEXT DEFAULT '',
                FOREIGN KEY (member_id)
                    REFERENCES members(member_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS member_attendance (
                attendance_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id       INTEGER NOT NULL,
                attendance_type TEXT NOT NULL,
                event_name      TEXT DEFAULT '',
                attendance_date TEXT NOT NULL,
                notes           TEXT DEFAULT '',
                FOREIGN KEY (member_id)
                    REFERENCES members(member_id)
            )
        """)

    def _run_migrations(self, cursor):
        self._ensure_column(cursor, "events", "event_time", "TEXT DEFAULT '09:00'")
        self._ensure_column(cursor, "events", "description", "TEXT DEFAULT ''")
        self._ensure_column(cursor, "events", "organizer", "TEXT DEFAULT ''")
        self._ensure_column(cursor, "events", "location", "TEXT DEFAULT ''")
        self._ensure_column(cursor, "events", "attendees", "INTEGER DEFAULT 0")
        self._ensure_column(cursor, "events", "status", "TEXT DEFAULT 'Upcoming'")
        self._ensure_column(cursor, "events", "color", "TEXT DEFAULT 'Blue'")
        self._ensure_column(cursor, "expenses", "description", "TEXT DEFAULT ''")
        self._ensure_column(cursor, "expenses", "requested_at", "TEXT")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expense_budgets (
                budget_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                category      TEXT NOT NULL UNIQUE,
                budget_amount REAL NOT NULL DEFAULT 0,
                period        TEXT NOT NULL DEFAULT 'MONTHLY',
                updated_at    TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_reports (
                report_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type    TEXT NOT NULL,
                start_date     TEXT,
                end_date       TEXT,
                generated_by   TEXT,
                generated_role TEXT,
                generated_at   TEXT NOT NULL,
                file_path      TEXT,
                filters        TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_activity (
                activity_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_username  TEXT NOT NULL,
                action          TEXT NOT NULL,
                affected_record TEXT,
                timestamp       TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'Success',
                details         TEXT
            )
        """)

    # ─── AUTHENTICATION ───────────────────────────────

    def validate_login(self, username, password):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password, role FROM users WHERE username = ?",
            (username,),
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            stored_hash, role = result
            if SecurityManager.verify_password(password, stored_hash):
                return role
        return None

    def create_user(self, username, password, role="staff"):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (
            username,
            SecurityManager.hash_password(password),
            role,
        ))
        conn.commit()
        conn.close()

    # ─── DASHBOARD AND DONATIONS ──────────────────────

    def get_dashboard_overview(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0), COUNT(*)
            FROM transactions
            WHERE type = 'INFLOW'
        """)
        total_donations, donation_records = cursor.fetchone()
        cursor.execute("""
            SELECT COUNT(DISTINCT donor_name)
            FROM transactions
            WHERE type = 'INFLOW'
            AND donor_name IS NOT NULL
            AND TRIM(donor_name) != ''
        """)
        total_donors = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0), COUNT(*)
            FROM expenses
            WHERE status = 'APPROVED'
        """)
        total_expenses, approved_expense_records = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'staff'")
        total_staff = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM events
            WHERE date(start_date) >= date('now')
        """)
        upcoming_events = cursor.fetchone()[0]
        conn.close()
        return {
            "total_donations":        total_donations or 0,
            "donation_records":       donation_records or 0,
            "total_donors":           total_donors or 0,
            "total_expenses":         total_expenses or 0,
            "approved_expense_records": approved_expense_records or 0,
            "net_balance":            (total_donations or 0) - (total_expenses or 0),
            "total_users":            total_users or 0,
            "total_staff":            total_staff or 0,
            "total_events":           total_events or 0,
            "upcoming_events":        upcoming_events or 0,
        }

    def get_kpi_data(self):
        overview = self.get_dashboard_overview()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM events
            WHERE start_date >= date('now')
            AND start_date <= date('now', '+7 days')
        """)
        events_count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM expenses WHERE status = 'PENDING'"
        )
        pending_expenses = cursor.fetchone()[0]
        conn.close()
        return {
            "total_donations":  "P {:,.0f}".format(overview["total_donations"]),
            "total_expenses":   "P {:,.0f}".format(overview["total_expenses"]),
            "net_balance":      "P {:,.0f}".format(overview["net_balance"]),
            "net_balance_raw":  overview["net_balance"],
            "events_count":     str(events_count),
            "pending_expenses": str(pending_expenses),
            "donor_count":      str(overview["total_donors"]),
            "forecast":         "Stable",
        }

    def get_historical_data(self):
        conn = self._get_connection()
        df = pd.read_sql_query("""
            SELECT date, donor_name, category, amount
            FROM transactions
            WHERE type = 'INFLOW'
            ORDER BY date ASC
        """, conn, parse_dates=["date"])
        conn.close()
        return df

    def get_recent_transactions(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date(date), donor_name, category, amount
            FROM transactions
            WHERE type = 'INFLOW'
            ORDER BY date DESC, trans_id DESC
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
            ORDER BY date DESC, trans_id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_transactions_by_range(self, start_date, end_date):
        return self.get_filtered_donations(start_date, end_date)

    def get_summary_by_range(self, start_date, end_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE type = 'INFLOW'
            AND date(date) BETWEEN date(?) AND date(?)
            GROUP BY category
            ORDER BY total DESC
        """, (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def save_transaction(self, date, donor_name, category,
                         amount, remarks="", user_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions
                (date, donor_name, category, amount,
                 type, remarks, user_id)
            VALUES (?, ?, ?, ?, 'INFLOW', ?, ?)
        """, (date, donor_name, category, amount, remarks, user_id))
        trans_id = cursor.lastrowid
        conn.commit()
        conn.close()
        if self._ai_engine is not None:
            try:
                self._ai_engine.retrain_if_needed()
            except Exception:
                pass
        return trans_id

    def get_donation_categories(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT category
            FROM transactions
            WHERE type = 'INFLOW'
            AND category IS NOT NULL
            AND TRIM(category) != ''
            ORDER BY category
        """)
        rows = [row[0] for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_filtered_donations(self, start_date=None, end_date=None,
                               category=None, search=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        clauses = ["type = 'INFLOW'"]
        params = []
        if start_date:
            clauses.append("date(date) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(date) <= date(?)")
            params.append(end_date)
        category = self._normalize_filter(category)
        if category:
            clauses.append("category = ?")
            params.append(category)
        search = self._normalize_filter(search)
        if search:
            clauses.append(
                "(donor_name LIKE ? OR category LIKE ? OR remarks LIKE ?)"
            )
            like = "%" + search + "%"
            params.extend([like, like, like])
        cursor.execute("""
            SELECT date(date), donor_name, category, amount, remarks
            FROM transactions
            WHERE """ + " AND ".join(clauses) + """
            ORDER BY date(date) DESC, trans_id DESC
        """, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_donation_totals(self, start_date=None, end_date=None,
                            category=None, search=None):
        rows = self.get_filtered_donations(
            start_date=start_date, end_date=end_date,
            category=category, search=search,
        )
        total = sum(float(row[3] or 0) for row in rows)
        donors = {
            str(row[1]).strip()
            for row in rows
            if row[1] is not None and str(row[1]).strip()
        }
        return {
            "total": total,
            "donor_count": len(donors),
            "record_count": len(rows),
        }

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

    def get_monthly_donation_totals(self, year=None,
                                    start_date=None, end_date=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        clauses = ["type = 'INFLOW'"]
        params = []
        if year:
            clauses.append("strftime('%Y', date) = ?")
            params.append(str(year))
        if start_date:
            clauses.append("date(date) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(date) <= date(?)")
            params.append(end_date)
        cursor.execute("""
            SELECT strftime('%Y-%m', date) AS month,
                   COALESCE(SUM(amount), 0) AS total,
                   COUNT(DISTINCT donor_name) AS donors,
                   COUNT(*) AS records
            FROM transactions
            WHERE """ + " AND ".join(clauses) + """
            GROUP BY month
            ORDER BY month ASC
        """, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def import_from_excel(self, filepath):
        from core.ai_engine import load_from_excel
        df = load_from_excel(filepath)
        df["type"] = "INFLOW"
        conn = self._get_connection()
        cursor = conn.cursor()
        inserted = 0
        skipped = 0
        for _, row in df.iterrows():
            cursor.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE date(date) = date(?)
                AND donor_name = ?
                AND category = ?
                AND amount = ?
            """, (
                str(row["date"])[:10],
                str(row.get("donor_name", "")),
                str(row["category"]),
                float(row["amount"]),
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
                    str(row.get("remarks", "")),
                ))
                inserted += 1
            else:
                skipped += 1
        conn.commit()
        conn.close()
        if self._ai_engine is not None:
            try:
                self._ai_engine.retrain_if_needed()
            except Exception:
                pass
        print("Import complete - {} new, {} skipped.".format(inserted, skipped))
        return inserted, skipped

    # ─── EXPENSES AND BUDGETS ─────────────────────────

    def save_expense_request(self, date, category, amount,
                              reason, submitted_by=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses
                (date, category, amount, reason, status,
                 submitted_by, description, requested_at)
            VALUES (?, ?, ?, ?, 'PENDING', ?, ?, ?)
        """, (
            date, category, amount, reason,
            submitted_by, reason, self._now(),
        ))
        expense_id = cursor.lastrowid
        conn.commit()
        conn.close()
        if submitted_by:
            self.log_staff_activity(
                submitted_by, "CREATE_EXPENSE_REQUEST",
                "Expense ID {}".format(expense_id), "Pending",
                "{} | P {:,.2f}".format(category, float(amount or 0)),
            )
        return expense_id

    def approve_expense(self, expense_id, approved_by):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE expenses
            SET status = 'APPROVED', approved_by = ?, approved_at = ?
            WHERE expense_id = ?
        """, (approved_by, self._now(), expense_id))
        conn.commit()
        conn.close()

    def reject_expense(self, expense_id, approved_by):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE expenses
            SET status = 'REJECTED', approved_by = ?, approved_at = ?
            WHERE expense_id = ?
        """, (approved_by, self._now(), expense_id))
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
            ORDER BY date DESC, expense_id DESC
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
            ORDER BY date DESC, expense_id DESC
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
            ORDER BY date DESC, expense_id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_expenses_filtered(self, start_date=None, end_date=None,
                              category=None, status=None, search=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        clauses = ["1 = 1"]
        params = []
        if start_date:
            clauses.append("date(date) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(date) <= date(?)")
            params.append(end_date)
        category = self._normalize_filter(category)
        if category:
            clauses.append("category = ?")
            params.append(category)
        status = self._normalize_filter(status)
        if status:
            clauses.append("UPPER(status) = ?")
            params.append(status.upper())
        search = self._normalize_filter(search)
        if search:
            clauses.append(
                "(category LIKE ? OR reason LIKE ? OR submitted_by LIKE ?)"
            )
            like = "%" + search + "%"
            params.extend([like, like, like])
        cursor.execute("""
            SELECT expense_id, date, category, amount, reason, status,
                   submitted_by, approved_by, approved_at
            FROM expenses
            WHERE """ + " AND ".join(clauses) + """
            ORDER BY date(date) DESC, expense_id DESC
        """, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_expense_categories(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT category
            FROM expenses
            WHERE category IS NOT NULL
            AND TRIM(category) != ''
            ORDER BY category
        """)
        rows = [row[0] for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_expense_status_counts(self, start_date=None, end_date=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        clauses = ["1 = 1"]
        params = []
        if start_date:
            clauses.append("date(date) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(date) <= date(?)")
            params.append(end_date)
        cursor.execute("""
            SELECT UPPER(status), COUNT(*)
            FROM expenses
            WHERE """ + " AND ".join(clauses) + """
            GROUP BY UPPER(status)
        """, params)
        counts = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("""
            SELECT COUNT(*) FROM expenses
            WHERE UPPER(status) = 'PENDING'
            AND date(COALESCE(requested_at, date)) >= date('now', '-7 days')
        """)
        new_requests = cursor.fetchone()[0]
        conn.close()
        return {
            "pending":  counts.get("PENDING", 0),
            "approved": counts.get("APPROVED", 0),
            "rejected": counts.get("REJECTED", 0),
            "new":      new_requests,
            "total":    sum(counts.values()),
        }

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
            AND date(date) BETWEEN date(?) AND date(?)
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
            "balance":  total_income - total_expenses,
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

    def set_category_budget(self, category, budget_amount, period="MONTHLY"):
        conn = self._get_connection()
        cursor = conn.cursor()
        now = self._now()
        cursor.execute(
            "SELECT budget_id FROM expense_budgets WHERE category = ?",
            (category,),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE expense_budgets
                SET budget_amount = ?, period = ?, updated_at = ?
                WHERE category = ?
            """, (float(budget_amount or 0), period or "MONTHLY", now, category))
        else:
            cursor.execute("""
                INSERT INTO expense_budgets
                    (category, budget_amount, period, updated_at)
                VALUES (?, ?, ?, ?)
            """, (category, float(budget_amount or 0), period or "MONTHLY", now))
        conn.commit()
        conn.close()

    def get_category_budgets(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, budget_amount, period, updated_at
            FROM expense_budgets
            ORDER BY category ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_budget_usage(self, start_date=None, end_date=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        clauses = ["UPPER(status) = 'APPROVED'"]
        params = []
        if start_date:
            clauses.append("date(date) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(date) <= date(?)")
            params.append(end_date)
        cursor.execute("""
            SELECT category, COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE """ + " AND ".join(clauses) + """
            GROUP BY category
        """, params)
        actuals = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("""
            SELECT category, budget_amount, period
            FROM expense_budgets
            ORDER BY category
        """)
        budgets = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        categories = sorted(set(actuals.keys()) | set(budgets.keys()))
        rows = []
        for category in categories:
            budget, period = budgets.get(category, (0, "MONTHLY"))
            actual = actuals.get(category, 0)
            remaining = budget - actual
            if budget <= 0:
                status = "No Budget"
            elif remaining < 0:
                status = "Over Budget"
            elif actual >= budget * 0.85:
                status = "Near Limit"
            else:
                status = "On Track"
            rows.append((category, budget, actual, remaining, status, period))
        conn.close()
        return rows

    # ─── EVENTS ───────────────────────────────────────

    def save_event(self, name, start_date, event_time="09:00",
                   end_date=None, location="", description="",
                   recurring=0, organizer="", attendees=0,
                   status="Upcoming", color="Blue"):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events
                (name, start_date, event_time, end_date, recurring,
                 location, description, organizer, attendees, status, color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, start_date, event_time or "09:00",
            end_date or None, int(recurring or 0),
            location or "", description or "", organizer or "",
            int(attendees or 0), status or "Upcoming", color or "Blue",
        ))
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return event_id

    def update_event(self, event_id, name, start_date,
                     event_time="09:00", end_date=None,
                     location="", description="", recurring=0,
                     organizer="", attendees=0,
                     status="Upcoming", color="Blue"):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE events
            SET name=?, start_date=?, event_time=?,
                end_date=?, recurring=?, location=?,
                description=?, organizer=?, attendees=?,
                status=?, color=?
            WHERE event_id=?
        """, (
            name, start_date, event_time or "09:00",
            end_date or None, int(recurring or 0),
            location or "", description or "", organizer or "",
            int(attendees or 0), status or "Upcoming",
            color or "Blue", event_id,
        ))
        conn.commit()
        conn.close()

    def delete_event(self, event_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
        conn.commit()
        conn.close()

    def get_events_filtered(self, start_date=None, end_date=None,
                            timing=None, search=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        clauses = ["1 = 1"]
        params = []
        today = datetime.date.today().isoformat()
        if timing == "Upcoming":
            clauses.append("date(start_date) >= date(?)")
            params.append(today)
        elif timing == "Past":
            clauses.append("date(start_date) < date(?)")
            params.append(today)
        else:
            if start_date:
                clauses.append("date(start_date) >= date(?)")
                params.append(start_date)
            if end_date:
                clauses.append("date(start_date) <= date(?)")
                params.append(end_date)
        search = self._normalize_filter(search)
        if search:
            clauses.append(
                "(name LIKE ? OR location LIKE ? OR description LIKE ?)"
            )
            like = "%" + search + "%"
            params.extend([like, like, like])
        cursor.execute("""
            SELECT event_id, name, start_date, event_time, end_date,
                   location, description, organizer, attendees,
                   status, recurring, color
            FROM events
            WHERE """ + " AND ".join(clauses) + """
            ORDER BY date(start_date) ASC, event_time ASC
        """, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_event_by_id(self, event_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_id, name, start_date, event_time, end_date,
                   location, description, organizer, attendees,
                   status, recurring, color
            FROM events
            WHERE event_id = ?
        """, (event_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    # ─── AUDIT, STAFF ACTIVITY, REPORTS ──────────────

    def get_audit_trail(self, start_date=None, end_date=None, limit=100):
        conn = self._get_connection()
        cursor = conn.cursor()
        clauses = ["1 = 1"]
        params = []
        if start_date:
            clauses.append("date(timestamp) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(timestamp) <= date(?)")
            params.append(end_date)
        params.append(limit)
        cursor.execute("""
            SELECT log_id, user_id, action, timestamp, details
            FROM audit_trail
            WHERE """ + " AND ".join(clauses) + """
            ORDER BY timestamp DESC
            LIMIT ?
        """, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def log_action(self, user_id, action, details=""):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_trail
                (user_id, action, timestamp, details)
            VALUES (?, ?, ?, ?)
        """, (user_id, action, self._now(), details))
        conn.commit()
        conn.close()

    def log_staff_activity(self, staff_username, action,
                           affected_record="", status="Success",
                           details=""):
        timestamp = self._now()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO staff_activity
                (staff_username, action, affected_record,
                 timestamp, status, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            staff_username or "staff", action,
            affected_record or "", timestamp,
            status or "Success", details or "",
        ))
        cursor.execute("""
            INSERT INTO audit_trail
                (user_id, action, timestamp, details)
            VALUES (?, ?, ?, ?)
        """, (
            staff_username or "staff", action, timestamp,
            "{} | {} | {}".format(
                affected_record or "",
                status or "Success",
                details or "",
            ).strip(),
        ))
        conn.commit()
        conn.close()

    def get_staff_activity(self, username=None, start_date=None,
                           end_date=None, limit=200):
        conn = self._get_connection()
        cursor = conn.cursor()
        clauses = ["1 = 1"]
        params = []
        username = self._normalize_filter(username)
        if username:
            clauses.append("staff_username = ?")
            params.append(username)
        if start_date:
            clauses.append("date(timestamp) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(timestamp) <= date(?)")
            params.append(end_date)
        params.append(limit)
        cursor.execute("""
            SELECT activity_id, staff_username, action,
                   affected_record, timestamp, status, details
            FROM staff_activity
            WHERE """ + " AND ".join(clauses) + """
            ORDER BY timestamp DESC
            LIMIT ?
        """, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def record_generated_report(self, report_type, start_date, end_date,
                                generated_by, generated_role,
                                file_path="", filters=""):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO generated_reports
                (report_type, start_date, end_date, generated_by,
                 generated_role, generated_at, file_path, filters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report_type, start_date, end_date, generated_by,
            generated_role, self._now(), file_path, filters,
        ))
        conn.commit()
        conn.close()

    def get_generated_reports(self, limit=20):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT report_id, report_type, start_date, end_date,
                   generated_by, generated_role, generated_at,
                   file_path, filters
            FROM generated_reports
            ORDER BY generated_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_report_rows(self, report_type, start_date=None, end_date=None):
        report_type = (report_type or "").lower()
        if "donation" in report_type:
            return self.get_filtered_donations(start_date, end_date)
        if "expense" in report_type:
            return self.get_expenses_filtered(start_date, end_date)
        if "event" in report_type:
            return self.get_events_filtered(start_date, end_date)
        if "audit" in report_type:
            return self.get_audit_trail(start_date, end_date, limit=500)
        if "staff" in report_type:
            return self.get_staff_activity(
                start_date=start_date, end_date=end_date, limit=500)
        return []

    # ─── MEMBER CRUD ──────────────────────────────────

    def save_member(self, full_name, nickname="", date_of_birth=None,
                    gender="", civil_status="", address="",
                    contact_number="", email="", date_joined=None,
                    ministry="", role="Member", family_id=None,
                    is_head_of_family=0, baptism_date=None,
                    confirmation_date=None, first_communion_date=None,
                    marriage_date=None, anointing_date=None,
                    church_wedding=0, notes=""):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO members (
                full_name, nickname, date_of_birth, gender,
                civil_status, address, contact_number, email,
                date_joined, ministry, role, is_active,
                family_id, is_head_of_family, baptism_date,
                confirmation_date, first_communion_date,
                marriage_date, anointing_date, church_wedding,
                notes, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,1,?,?,?,?,?,?,?,?,?,?)
        """, (
            full_name, nickname, date_of_birth, gender,
            civil_status, address, contact_number, email,
            date_joined, ministry, role,
            family_id, is_head_of_family, baptism_date,
            confirmation_date, first_communion_date,
            marriage_date, anointing_date, church_wedding,
            notes, self._now()
        ))
        member_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return member_id

    def update_member(self, member_id, full_name, nickname="",
                      date_of_birth=None, gender="", civil_status="",
                      address="", contact_number="", email="",
                      date_joined=None, ministry="", role="Member",
                      family_id=None, is_head_of_family=0,
                      baptism_date=None, confirmation_date=None,
                      first_communion_date=None, marriage_date=None,
                      anointing_date=None, church_wedding=0, notes=""):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE members SET
                full_name=?, nickname=?, date_of_birth=?,
                gender=?, civil_status=?, address=?,
                contact_number=?, email=?, date_joined=?,
                ministry=?, role=?, family_id=?,
                is_head_of_family=?, baptism_date=?,
                confirmation_date=?, first_communion_date=?,
                marriage_date=?, anointing_date=?,
                church_wedding=?, notes=?
            WHERE member_id=?
        """, (
            full_name, nickname, date_of_birth, gender,
            civil_status, address, contact_number, email,
            date_joined, ministry, role, family_id,
            is_head_of_family, baptism_date, confirmation_date,
            first_communion_date, marriage_date, anointing_date,
            church_wedding, notes, member_id
        ))
        conn.commit()
        conn.close()

    def set_member_active(self, member_id, is_active):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE members SET is_active=? WHERE member_id=?",
            (int(is_active), member_id)
        )
        conn.commit()
        conn.close()

    def delete_member(self, member_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM members WHERE member_id=?", (member_id,)
        )
        conn.commit()
        conn.close()

    def get_member_by_id(self, member_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM members WHERE member_id=?", (member_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row

    def get_all_members(self, search=None, ministry=None,
                        role=None, is_active=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        clauses = ["1=1"]
        params = []
        if search:
            clauses.append(
                "(full_name LIKE ? OR nickname LIKE ? "
                "OR contact_number LIKE ? OR email LIKE ?)"
            )
            like = "%" + search + "%"
            params.extend([like, like, like, like])
        if ministry and ministry != "All":
            clauses.append("ministry=?")
            params.append(ministry)
        if role and role != "All":
            clauses.append("role=?")
            params.append(role)
        if is_active is not None:
            clauses.append("is_active=?")
            params.append(int(is_active))
        cursor.execute("""
            SELECT member_id, full_name, nickname, gender,
                   contact_number, ministry, role, is_active,
                   date_joined, date_of_birth
            FROM members
            WHERE """ + " AND ".join(clauses) + """
            ORDER BY full_name ASC
        """, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_member_stats(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM members")
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM members WHERE is_active=1"
        )
        active = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM members WHERE is_active=0"
        )
        inactive = cursor.fetchone()[0]
        first_of_month = datetime.date.today().replace(day=1).isoformat()
        cursor.execute(
            "SELECT COUNT(*) FROM members WHERE created_at >= ?",
            (first_of_month,)
        )
        new_this_month = cursor.fetchone()[0]
        conn.close()
        return {
            "total": total, "active": active,
            "inactive": inactive, "new_this_month": new_this_month
        }

    def get_member_ministries(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ministry FROM members
            WHERE ministry IS NOT NULL AND TRIM(ministry) != ''
            ORDER BY ministry
        """)
        rows = [r[0] for r in cursor.fetchall()]
        conn.close()
        return rows

    # ─── SACRAMENTS ───────────────────────────────────

    def save_sacrament(self, member_id, sacrament_type,
                       sacrament_date=None, officiating_priest="",
                       location="", notes=""):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO member_sacraments
                (member_id, sacrament_type, sacrament_date,
                 officiating_priest, location, notes)
            VALUES (?,?,?,?,?,?)
        """, (
            member_id, sacrament_type, sacrament_date,
            officiating_priest, location, notes
        ))
        conn.commit()
        conn.close()

    def get_member_sacraments(self, member_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sacrament_id, sacrament_type, sacrament_date,
                   officiating_priest, location, notes
            FROM member_sacraments
            WHERE member_id=?
            ORDER BY sacrament_date ASC
        """, (member_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_sacrament(self, sacrament_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM member_sacraments WHERE sacrament_id=?",
            (sacrament_id,)
        )
        conn.commit()
        conn.close()

    # ─── ATTENDANCE ───────────────────────────────────

    def save_attendance(self, member_id, attendance_type,
                        attendance_date, event_name="", notes=""):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO member_attendance
                (member_id, attendance_type, event_name,
                 attendance_date, notes)
            VALUES (?,?,?,?,?)
        """, (
            member_id, attendance_type, event_name,
            attendance_date, notes
        ))
        conn.commit()
        conn.close()

    def get_member_attendance(self, member_id, limit=50):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT attendance_id, attendance_type, event_name,
                   attendance_date, notes
            FROM member_attendance
            WHERE member_id=?
            ORDER BY attendance_date DESC
            LIMIT ?
        """, (member_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_attendance(self, attendance_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM member_attendance WHERE attendance_id=?",
            (attendance_id,)
        )
        conn.commit()
        conn.close()

    # ─── FAMILIES ─────────────────────────────────────

    def save_family(self, family_name, address=""):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO member_families (family_name, address, created_at)
            VALUES (?,?,?)
        """, (family_name, address, self._now()))
        family_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return family_id

    def get_all_families(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.family_id, f.family_name, f.address,
                   COUNT(m.member_id) as member_count
            FROM member_families f
            LEFT JOIN members m ON m.family_id = f.family_id
            GROUP BY f.family_id
            ORDER BY f.family_name
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_family_members(self, family_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT member_id, full_name, role, is_head_of_family
            FROM members WHERE family_id=?
            ORDER BY is_head_of_family DESC, full_name
        """, (family_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows