import customtkinter as ctk
from tkinter import messagebox

THEME = {
    "primary":      "#4F86F7",
    "primary_dark": "#3a6bc0",
    "bg_main":      "#456990",
    "bg_card":      "#FFFFFF",
    "text_main":    "#333333",
    "text_sub":     "#888888",
    "border":       "#E0E0E0",
    "success":      "#28A745",
    "danger":       "#FF4D4D"
}


class LoginFrame(ctk.CTkFrame):

    def __init__(self, master, login_callback):
        super().__init__(master, fg_color="transparent")
        self.login_callback = login_callback
        self.place(relx=0.5, rely=0.5, anchor="center")

        self.card = ctk.CTkFrame(
            self,
            width=450,
            height=560,
            corner_radius=20,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border"]
        )
        self.card.pack_propagate(False)
        self.card.pack(padx=20, pady=20)

        # Header
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(pady=(50, 30))

        ctk.CTkLabel(
            header,
            text="⛪",
            font=("Segoe UI Emoji", 52),
            text_color=THEME["primary"]
        ).pack()

        ctk.CTkLabel(
            header,
            text="ChurchTrack",
            font=("Arial", 26, "bold"),
            text_color=THEME["text_main"]
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            header,
            text="Sign in to your dashboard",
            font=("Arial", 13),
            text_color=THEME["text_sub"]
        ).pack(pady=(5, 0))

        # Inputs
        input_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        input_frame.pack(pady=10, padx=50, fill="x")

        ctk.CTkLabel(
            input_frame,
            text="Username",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"],
            anchor="w"
        ).pack(fill="x", pady=(0, 6))

        self.username_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter username",
            height=45,
            corner_radius=10,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"]
        )
        self.username_entry.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            input_frame,
            text="Password",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"],
            anchor="w"
        ).pack(fill="x", pady=(0, 6))

        self.password_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter password",
            show="•",
            height=45,
            corner_radius=10,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"]
        )
        self.password_entry.pack(fill="x")

        # Sign in button
        ctk.CTkButton(
            self.card,
            text="Sign In",
            font=("Arial", 14, "bold"),
            height=50,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self.attempt_login
        ).pack(pady=(24, 10), padx=50, fill="x")

        ctk.CTkLabel(
            self.card,
            text="admin / admin123   |   staff / staff123",
            font=("Arial", 11),
            text_color=THEME["text_sub"]
        ).pack(side="bottom", pady=25)

        self.username_entry.bind("<Return>", lambda e: self.attempt_login())
        self.password_entry.bind("<Return>", lambda e: self.attempt_login())

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing Fields", "Please enter both username and password.")
            return
        self.login_callback(username, password)