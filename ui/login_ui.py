import customtkinter as ctk
import tkinter as tk
import os
import json
from PIL import Image, ImageTk
from ui.theme import THEME

REMEMBER_FILE = "core/.remember_me.json"


def _load_remembered():
    try:
        with open(REMEMBER_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_remembered(username, password):
    os.makedirs("core", exist_ok=True)
    with open(REMEMBER_FILE, "w") as f:
        json.dump({"username": username, "password": password}, f)


def _clear_remembered():
    try:
        os.remove(REMEMBER_FILE)
    except Exception:
        pass


class LoginFrame(ctk.CTkFrame):

    def __init__(self, master, on_login):
        super().__init__(master, fg_color="#2f3e6b")
        self.on_login      = on_login
        self._logo_img     = None
        self._bg_img       = None
        self._show_pw      = False   # track password visibility

        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self._draw_background()

        # ── SHADOW ──────────────────────────────────────
        shadow = ctk.CTkFrame(
            self, fg_color="#000000",
            width=830, height=510, corner_radius=20
        )
        shadow.place(relx=0.5, rely=0.5, anchor="center")

        # ── MAIN CARD ────────────────────────────────────
        card = ctk.CTkFrame(
            self, fg_color="#FFFFFF",
            corner_radius=18, width=820, height=500
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # ── LEFT PANEL ───────────────────────────────────
        left = ctk.CTkFrame(card, fg_color="#FFFFFF", width=450)
        left.pack(side="left", fill="both")
        left.pack_propagate(False)

        # ── RIGHT PANEL ──────────────────────────────────
        right = ctk.CTkFrame(card, fg_color="#1a3a8a", width=370)
        right.pack(side="right", fill="both", expand=True)
        right.pack_propagate(False)

        canvas = tk.Canvas(right, bg="#1a3a8a", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        canvas.bind("<Configure>",
                    lambda e: self._draw_right(canvas, e.width, e.height))

        # ── LOGO ─────────────────────────────────────────
        logo_row = ctk.CTkFrame(left, fg_color="transparent")
        logo_row.pack(anchor="w", padx=44, pady=(44, 0))

        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).resize((38, 38), Image.LANCZOS)
                self._logo_img = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(38, 38)
                )
                ctk.CTkLabel(logo_row, image=self._logo_img, text="").pack(side="left")
            except Exception:
                self._logo_fallback(logo_row)
        else:
            self._logo_fallback(logo_row)

        ctk.CTkLabel(
            logo_row, text="ChurchTrack",
            font=("Segoe UI", 20, "bold"),
            text_color="#0a3b8e"
        ).pack(side="left", padx=(10, 0))

        # ── TITLE ────────────────────────────────────────
        ctk.CTkLabel(
            left, text="WELCOME BACK!",
            font=("Georgia", 24, "bold"),
            text_color="#0a3b8e"
        ).pack(anchor="w", padx=44, pady=(45, 0))

        ctk.CTkLabel(
            left, text="Please sign in to continue.",
            font=("Segoe UI", 11), text_color="#333333"
        ).pack(anchor="w", padx=44, pady=(2, 25))

        # ── USERNAME ─────────────────────────────────────
        user_frame = ctk.CTkFrame(
            left, fg_color="#F5F7FA", corner_radius=30
        )
        user_frame.pack(fill="x", padx=44, pady=(0, 12))

        ctk.CTkLabel(
            user_frame, text="👤",
            font=("Arial", 14), text_color="#555555"
        ).pack(side="left", padx=(18, 8), pady=12)

        self.username_entry = ctk.CTkEntry(
            user_frame,
            placeholder_text="Username",
            height=38, border_width=0,
            fg_color="#F5F7FA",
            text_color="#333333",
            placeholder_text_color="#888888",
            font=("Segoe UI", 12)
        )
        self.username_entry.pack(
            side="left", fill="x", expand=True,
            padx=(0, 16), pady=6
        )

        # ── PASSWORD ─────────────────────────────────────
        pass_frame = ctk.CTkFrame(
            left, fg_color="#F5F7FA", corner_radius=30
        )
        pass_frame.pack(fill="x", padx=44, pady=(0, 10))

        ctk.CTkLabel(
            pass_frame, text="🔒",
            font=("Arial", 14), text_color="#555555"
        ).pack(side="left", padx=(18, 8), pady=12)

        self.password_entry = ctk.CTkEntry(
            pass_frame,
            placeholder_text="Password",
            show="•",
            height=38, border_width=0,
            fg_color="#F5F7FA",
            text_color="#333333",
            placeholder_text_color="#888888",
            font=("Segoe UI", 12)
        )
        self.password_entry.pack(
            side="left", fill="x", expand=True,
            padx=(0, 4), pady=6
        )

        # Show / Hide password toggle button
        self._eye_btn = ctk.CTkButton(
            pass_frame,
            text="👁",
            width=36, height=36,
            corner_radius=18,
            fg_color="transparent",
            hover_color="#E8EDF5",
            text_color="#888888",
            font=("Arial", 14),
            command=self._toggle_password
        )
        self._eye_btn.pack(side="right", padx=(0, 10), pady=6)

        # ── OPTIONS ROW ──────────────────────────────────
        options_row = ctk.CTkFrame(left, fg_color="transparent")
        options_row.pack(fill="x", padx=44, pady=(2, 0))

        self.remember_var = ctk.BooleanVar(value=False)

        self._remember_cb = ctk.CTkCheckBox(
            options_row,
            text="Remember Me",
            variable=self.remember_var,
            font=("Segoe UI", 11, "italic"),
            text_color="#707070",
            fg_color="#0a3b8e",
            hover_color="#072b69",
            checkmark_color="#FFFFFF",
            border_color="#B0B0B0"
        )
        self._remember_cb.pack(side="left")

        forgot = ctk.CTkLabel(
            options_row,
            text="Forgot Password?",
            font=("Segoe UI", 11, "italic"),
            text_color="#0a3b8e",
            cursor="hand2"
        )
        forgot.pack(side="right")
        forgot.bind("<Enter>", lambda e: forgot.configure(text_color="#072b69"))
        forgot.bind("<Leave>", lambda e: forgot.configure(text_color="#0a3b8e"))

        # ── ERROR LABEL ──────────────────────────────────
        self.error_label = ctk.CTkLabel(
            left, text="",
            font=("Segoe UI", 11),
            text_color=THEME["danger"]
        )
        self.error_label.pack(pady=(8, 0))

        # ── LOGIN BUTTON ─────────────────────────────────
        self.login_btn = ctk.CTkButton(
            left,
            text="Log in",
            font=("Segoe UI", 14, "bold"),
            height=45, corner_radius=25,
            fg_color="#0a3b8e",
            hover_color="#06245c",
            text_color="#FFFFFF",
            command=self._attempt_login
        )
        self.login_btn.pack(fill="x", padx=44, pady=(10, 0))

        self.login_btn.bind("<Enter>",
            lambda e: self.login_btn.configure(fg_color="#06245c"))
        self.login_btn.bind("<Leave>",
            lambda e: self.login_btn.configure(fg_color="#0a3b8e"))

        # ── KEY BINDS ────────────────────────────────────
        self.username_entry.bind("<Return>", lambda e: self._attempt_login())
        self.password_entry.bind("<Return>", lambda e: self._attempt_login())
        self.username_entry.focus()

        # ── PRE-FILL if Remember Me was saved ────────────
        remembered = _load_remembered()
        if remembered.get("username") and remembered.get("password"):
            self.username_entry.insert(0, remembered["username"])
            self.password_entry.insert(0, remembered["password"])
            self.remember_var.set(True)

    # ─── TOGGLE PASSWORD VISIBILITY ───────────────────

    def _toggle_password(self):
        self._show_pw = not self._show_pw
        if self._show_pw:
            self.password_entry.configure(show="")
            self._eye_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="•")
            self._eye_btn.configure(text="👁")

    # ─── HELPERS ──────────────────────────────────────

    def _logo_fallback(self, parent):
        placeholder = ctk.CTkFrame(
            parent, width=38, height=38,
            fg_color="#E8EDF5", corner_radius=8
        )
        placeholder.pack(side="left")
        placeholder.pack_propagate(False)
        ctk.CTkLabel(
            placeholder, text="⛪",
            font=("Arial", 20), text_color="#1a2a4a"
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _draw_background(self):
        bg_path = os.path.join("assets", "bg.png")
        if os.path.exists(bg_path):
            try:
                img = Image.open(bg_path)
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                img = img.resize((sw, sh), Image.LANCZOS)
                self._bg_img = ImageTk.PhotoImage(img)
                tk.Label(self, image=self._bg_img, bd=0).place(
                    x=0, y=0, relwidth=1, relheight=1
                )
            except Exception:
                pass

    def _draw_right(self, c, W, H):
        c.delete("all")
        c.create_rectangle(0, 0, W, H, fill="#1a3a8a", outline="")

        shade_colors = [
            "#2d5be3", "#1f4bc6",
            "#2a56d6", "#1c43b5",
            "#244fca", "#183da3",
            "#2b58dc", "#1e46c2",
        ]
        shapes = [
            [
                (W*0.5, H*0.05), (W*0.75, H*0.22),
                (W*0.75, H*0.55), (W*0.5, H*0.72),
                (W*0.25, H*0.55), (W*0.25, H*0.22)
            ],
            [
                (W*0.72, 0), (W*0.97, H*0.12),
                (W*0.97, H*0.38), (W*0.72, H*0.5),
                (W*0.47, H*0.38), (W*0.47, H*0.12)
            ],
        ]
        for shape, color in zip(shapes, shade_colors):
            flat = [coord for point in shape for coord in point]
            c.create_polygon(flat, fill=color, outline="#3a5acc")

    # ─── LOGIN LOGIC ──────────────────────────────────

    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_label.configure(
                text="Please enter both username and password."
            )
            return

        self.login_btn.configure(state="disabled", text="Signing in...")
        self.after(300, lambda: self._do_login(username, password))

    def _do_login(self, username, password):
        try:
            # Handle Remember Me before calling on_login
            if self.remember_var.get():
                _save_remembered(username, password)
            else:
                _clear_remembered()

            self.on_login(username, password)
        except Exception:
            self.error_label.configure(
                text="Invalid username or password."
            )
            self.login_btn.configure(state="normal", text="Log in")

