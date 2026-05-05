import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

from core.db_manager import DatabaseManager
from core.ai_engine import AIEngine

from ui.theme import THEME
from ui.components import polish_interactions
from ui.login_ui import LoginFrame
from ui.dashboard import AdminDashboard
from ui.financial_analytics import FinancialAnalytics
from ui.event_management import EventManagement
from ui.expense_management import ExpenseManagement
from ui.account_management import StaffControl
from ui.audit_logs import AuditLogs
from ui.reports import Reports
from ui.settings import Settings
from ui.chatbot import ChatbotScreen
from ui.staff_donation import StaffDonationEntry
from ui.profiling import ProfilingScreen


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

SESSION_CHECK_MS = 60_000  # check every 60 seconds


class ChurchTrackApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("ChurchTrack")
        self.configure(fg_color=THEME["bg_main"])
        self.minsize(1180, 720)

        self.db_manager = DatabaseManager()
        self.ai_engine  = AIEngine(self.db_manager)
        self.db_manager._ai_engine = self.ai_engine

        # Session tracking for real-time password invalidation
        self._session_username  = None
        self._session_pw_stamp  = None   # last_password_changed_at at login time
        self._session_check_job = None

        self.after(10, self._maximize)
        self.show_login()

    def _maximize(self):
        try:
            self.wm_state("zoomed")
        except Exception:
            self.geometry("1180x720")

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ── Login / logout ────────────────────────────────

    def show_login(self):
        self._stop_session_watch()
        self._session_username = None
        self._session_pw_stamp = None
        self._clear()
        self.configure(fg_color=THEME["bg_main"])
        frame = LoginFrame(self, self.on_login_success, self.db_manager)
        self.after_idle(lambda: polish_interactions(frame))

    def on_login_success(self, username, password):
        role = self.db_manager.validate_login(username, password)
        if role == "admin":
            self._start_session_watch(username)
            self._load_admin_screen("Dashboard")
        elif role == "staff":
            self._start_session_watch(username)
            self._clear()
            self.configure(fg_color=THEME["bg_main"])
            frame = StaffDonationEntry(
                self, self.db_manager, self.show_login
            )
            self.after_idle(lambda: polish_interactions(frame))
        else:
            raise ValueError("Invalid credentials")

    # ── Session watch ─────────────────────────────────

    def _start_session_watch(self, username):
        self._session_username = username
        self._session_pw_stamp = (
            self.db_manager.get_user_password_changed_at(username)
        )
        self._schedule_session_check()

    def _stop_session_watch(self):
        if self._session_check_job:
            try:
                self.after_cancel(self._session_check_job)
            except Exception:
                pass
        self._session_check_job = None

    def _schedule_session_check(self):
        self._session_check_job = self.after(
            SESSION_CHECK_MS, self._check_session
        )

    def _check_session(self):
        if not self._session_username:
            return
        current_stamp = (
            self.db_manager.get_user_password_changed_at(
                self._session_username
            )
        )
        if current_stamp != self._session_pw_stamp:
            self._force_logout()
            return
        self._schedule_session_check()

    def _force_logout(self):
        """Called when password changed externally — force re-login."""
        self._stop_session_watch()
        self._clear()
        self.configure(fg_color=THEME["bg_main"])

        overlay = ctk.CTkFrame(self, fg_color=THEME["bg_card"])
        overlay.place(relx=0.5, rely=0.5, anchor="center",
                      width=440, height=220)

        ctk.CTkLabel(
            overlay,
            text="Session Expired",
            font=("", 20, "bold"),
            text_color=THEME["danger"]
        ).pack(pady=(32, 8))

        ctk.CTkLabel(
            overlay,
            text="Your password was changed by an administrator.\n"
                 "Please sign in again with your new password.",
            font=("", 12),
            text_color=THEME["text_sub"],
            justify="center"
        ).pack(pady=(0, 24))

        ctk.CTkButton(
            overlay,
            text="Sign in again",
            height=44, corner_radius=14,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            text_color=THEME["bg_card"],
            command=self.show_login
        ).pack(fill="x", padx=40)

    # ── Admin screen router ───────────────────────────

    def _load_admin_screen(self, screen):
        self._clear()
        self.configure(fg_color=THEME["bg_main"])

        screens = {
            "Dashboard": lambda: AdminDashboard(
                self, self.db_manager, self.ai_engine,
                self._load_admin_screen, self.show_login,
            ),
            "Financial Analytics": lambda: FinancialAnalytics(
                self, self.db_manager, self.ai_engine,
                self._load_admin_screen, self.show_login,
            ),
            "Profiling": lambda: ProfilingScreen(
                self, self.db_manager,
                self._load_admin_screen, self.show_login,
            ),
            "Event Management": lambda: EventManagement(
                self, self.db_manager,
                self._load_admin_screen, self.show_login,
            ),
            "Expense Management": lambda: ExpenseManagement(
                self, self.db_manager, self.ai_engine,
                self._load_admin_screen, self.show_login,
            ),
            "Account Management": lambda: StaffControl(
                self, self.db_manager,
                self._load_admin_screen, self.show_login,
            ),
            "Staff Control": lambda: StaffControl(
                self, self.db_manager,
                self._load_admin_screen, self.show_login,
            ),
            "Audit Logs": lambda: AuditLogs(
                self, self.db_manager,
                self._load_admin_screen, self.show_login,
            ),
            "Reports": lambda: Reports(
                self, self.db_manager,
                self._load_admin_screen, self.show_login,
            ),
            "AI Assistant": lambda: ChatbotScreen(
                self, self.db_manager, self.ai_engine,
                self._load_admin_screen, self.show_login,
            ),
            "Settings": lambda: Settings(
                self, self.db_manager,
                self._load_admin_screen, self.show_login,
            ),
        }

        try:
            frame = screens.get(
                screen, screens["Dashboard"]
            )()
            self.after_idle(lambda: polish_interactions(frame))
        except Exception as error:
            import traceback
            print("Screen load error '{}': {}".format(screen, error))
            traceback.print_exc()
            frame = screens["Dashboard"]()
            self.after_idle(lambda: polish_interactions(frame))


if __name__ == "__main__":
    app = ChurchTrackApp()
    app.mainloop()