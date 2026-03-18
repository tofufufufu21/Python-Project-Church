import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from tkinter import messagebox
from core.db_manager import DatabaseManager
from core.ai_engine import AIEngine
from ui.login_ui import LoginFrame
from ui.dashboard import AdminDashboard, StaffDonationEntry

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class ChurchTrackApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("ChurchTrack AI System")
        self.db_manager = DatabaseManager()
        self.ai_engine  = AIEngine(self.db_manager)
        self._center_window(1280, 720)
        self.show_login()

    def _center_window(self, width, height):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw // 2) - (width  // 2)
        y  = (sh // 2) - (height // 2)
        self.geometry(
            str(width) + "x" + str(height) + "+" + str(x) + "+" + str(y)
        )

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_login(self):
        self._clear()
        self.configure(fg_color="#456990")
        LoginFrame(self, self.on_login_success)

    def on_login_success(self, username, password):
        role = self.db_manager.validate_login(username, password)
        if role == "admin":
            self._clear()
            self.configure(fg_color="#F4F6F9")
            AdminDashboard(self, self.db_manager, self.ai_engine, self.show_login)
        elif role == "staff":
            self._clear()
            self.configure(fg_color="#F4F6F9")
            StaffDonationEntry(self, self.db_manager, self.show_login)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")


if __name__ == "__main__":
    app = ChurchTrackApp()
    app.mainloop()
