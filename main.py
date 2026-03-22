import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from tkinter import messagebox
from core.db_manager import DatabaseManager
from core.ai_engine import AIEngine
from ui.login_ui import LoginFrame
from ui.dashboard import AdminDashboard
from ui.financial_analytics import FinancialAnalytics
from ui.event_management import EventManagement
from ui.expense_management import ExpenseManagement
from ui.staff_control import StaffControl
from ui.audit_logs import AuditLogs
from ui.reports import Reports
from ui.settings import Settings
from ui.chatbot import ChatbotScreen
from ui.staff_donation import StaffDonationEntry

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class ChurchTrackApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("ChurchTrack AI System")
        self.db_manager            = DatabaseManager()
        self.ai_engine             = AIEngine(self.db_manager)
        self.db_manager._ai_engine = self.ai_engine
        self.after(10, self._maximize)
        self.show_login()

    def _maximize(self):
        self.wm_state("zoomed")

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_login(self):
        self._clear()
        self.configure(fg_color="#4a5a8a")
        LoginFrame(self, self.on_login_success)

    def on_login_success(self, username, password):
        role = self.db_manager.validate_login(
            username, password
        )
        if role == "admin":
            self._load_admin_screen("Dashboard")
        elif role == "staff":
            self._clear()
            self.configure(fg_color="#F4F6F9")
            StaffDonationEntry(
                self, self.db_manager, self.show_login
            )
        else:
            raise ValueError("Invalid credentials")

    def _load_admin_screen(self, screen):
        self._clear()
        self.configure(fg_color="#F4F6F9")

        screens = {
            "Dashboard": lambda: AdminDashboard(
                self, self.db_manager, self.ai_engine,
                self._load_admin_screen, self.show_login
            ),
            "Financial Analytics": lambda: FinancialAnalytics(
                self, self.db_manager, self.ai_engine,
                self._load_admin_screen, self.show_login
            ),
            "Event Management": lambda: EventManagement(
                self, self.db_manager,
                self._load_admin_screen, self.show_login
            ),
            "Expense Management": lambda: ExpenseManagement(
                self, self.db_manager, self.ai_engine,
                self._load_admin_screen, self.show_login
            ),
            "Staff Control": lambda: StaffControl(
                self, self.db_manager,
                self._load_admin_screen, self.show_login
            ),
            "Audit Logs": lambda: AuditLogs(
                self, self.db_manager,
                self._load_admin_screen, self.show_login
            ),
            "Reports": lambda: Reports(
                self, self.db_manager,
                self._load_admin_screen, self.show_login
            ),
            "AI Assistant": lambda: ChatbotScreen(
                self, self.db_manager, self.ai_engine,
                self._load_admin_screen, self.show_login
            ),
            "Settings": lambda: Settings(
                self, self.db_manager,
                self._load_admin_screen, self.show_login
            ),
        }

        action = screens.get(screen, screens["Dashboard"])
        action()


if __name__ == "__main__":
    app = ChurchTrackApp()
    app.mainloop()