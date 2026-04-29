import customtkinter as ctk
import tkinter as tk
import os
import json
from PIL import Image, ImageTk
from ui.theme import THEME, MODERN_THEME

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
        super().__init__(master, fg_color=THEME["bg_main"])

        self.on_login = on_login
        self._logo_img = None
        self._bg_img = None
        self._show_pw = False

        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self._draw_background()

        shadow = ctk.CTkFrame(
            self,
            fg_color=MODERN_THEME["shadow"],
            width=886,
            height=566,
            corner_radius=22,
        )
        shadow.place(relx=0.5, rely=0.508, anchor="center")

        card = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=28,
            width=880,
            height=560,
            border_width=1,
            border_color=THEME["border"],
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        left = ctk.CTkFrame(card, fg_color=THEME["bg_card"], width=500)
        left.pack(side="left", fill="both")
        left.pack_propagate(False)

        right = ctk.CTkFrame(
            card,
            fg_color=THEME["sidebar"],
            width=380,
            corner_radius=24,
        )
        right.pack(side="right", fill="both", expand=True, padx=(0, 8), pady=8)
        right.pack_propagate(False)

        canvas = tk.Canvas(
            right,
            bg=THEME["sidebar"],
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill="both", expand=True)
        canvas.bind(
            "<Configure>",
            lambda event: self._draw_right(canvas, event.width, event.height),
        )

        logo_row = ctk.CTkFrame(left, fg_color="transparent")
        logo_row.pack(anchor="w", padx=52, pady=(52, 0))

        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).resize((38, 38), Image.LANCZOS)
                self._logo_img = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(38, 38),
                )
                ctk.CTkLabel(logo_row, image=self._logo_img, text="").pack(
                    side="left"
                )
            except Exception:
                self._logo_fallback(logo_row)
        else:
            self._logo_fallback(logo_row)

        ctk.CTkLabel(
            logo_row,
            text="ChurchTrack",
            font=(MODERN_THEME["font_family"], 21, "bold"),
            text_color=THEME["text_main"],
        ).pack(side="left", padx=(12, 0))

        ctk.CTkLabel(
            left,
            text="Welcome back",
            font=(MODERN_THEME["font_family"], 30, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=52, pady=(54, 0))

        ctk.CTkLabel(
            left,
            text="Sign in to manage donations, reports, events, and church operations.",
            font=(MODERN_THEME["font_family"], 12),
            text_color=THEME["text_sub"],
            wraplength=360,
            justify="left",
        ).pack(anchor="w", padx=52, pady=(6, 30))

        user_frame = self._field_frame(left)
        user_frame.pack(fill="x", padx=52, pady=(0, 14))

        ctk.CTkLabel(
            user_frame,
            text="👤",
            font=(MODERN_THEME["font_family"], 14),
            text_color=THEME["text_sub"],
        ).pack(side="left", padx=(18, 8), pady=12)

        self.username_entry = ctk.CTkEntry(
            user_frame,
            placeholder_text="Username",
            height=42,
            border_width=0,
            fg_color=THEME["input"],
            text_color=THEME["text_main"],
            placeholder_text_color=THEME["text_muted"],
            font=(MODERN_THEME["font_family"], 12),
        )
        self.username_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 16),
            pady=6,
        )

        pass_frame = self._field_frame(left)
        pass_frame.pack(fill="x", padx=52, pady=(0, 12))

        ctk.CTkLabel(
            pass_frame,
            text="🔒",
            font=(MODERN_THEME["font_family"], 14),
            text_color=THEME["text_sub"],
        ).pack(side="left", padx=(18, 8), pady=12)

        self.password_entry = ctk.CTkEntry(
            pass_frame,
            placeholder_text="Password",
            show="•",
            height=42,
            border_width=0,
            fg_color=THEME["input"],
            text_color=THEME["text_main"],
            placeholder_text_color=THEME["text_muted"],
            font=(MODERN_THEME["font_family"], 12),
        )
        self.password_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 4),
            pady=6,
        )

        self._eye_btn = ctk.CTkButton(
            pass_frame,
            text="👁",
            width=36,
            height=36,
            corner_radius=14,
            fg_color="transparent",
            hover_color=MODERN_THEME["surface_hover"],
            text_color=THEME["text_sub"],
            font=(MODERN_THEME["font_family"], 14),
            command=self._toggle_password,
        )
        self._eye_btn.pack(side="right", padx=(0, 10), pady=6)

        options_row = ctk.CTkFrame(left, fg_color="transparent")
        options_row.pack(fill="x", padx=52, pady=(2, 0))

        self.remember_var = ctk.BooleanVar(value=False)

        self._remember_cb = ctk.CTkCheckBox(
            options_row,
            text="Remember me",
            variable=self.remember_var,
            font=(MODERN_THEME["font_family"], 11),
            text_color=THEME["text_sub"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            checkmark_color=THEME["bg_card"],
            border_color=THEME["border_strong"],
        )
        self._remember_cb.pack(side="left")

        forgot = ctk.CTkLabel(
            options_row,
            text="Need help?",
            font=(MODERN_THEME["font_family"], 11),
            text_color=THEME["primary"],
            cursor="hand2",
        )
        forgot.pack(side="right")
        forgot.bind(
            "<Enter>",
            lambda event: forgot.configure(text_color=THEME["primary_dark"]),
        )
        forgot.bind(
            "<Leave>",
            lambda event: forgot.configure(text_color=THEME["primary"]),
        )

        self.error_label = ctk.CTkLabel(
            left,
            text="",
            font=(MODERN_THEME["font_family"], 11),
            text_color=THEME["danger"],
        )
        self.error_label.pack(pady=(10, 0))

        self.login_btn = ctk.CTkButton(
            left,
            text="Sign in",
            font=(MODERN_THEME["font_family"], 14, "bold"),
            height=48,
            corner_radius=16,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            text_color=THEME["bg_card"],
            command=self._attempt_login,
        )
        self.login_btn.pack(fill="x", padx=52, pady=(12, 0))

        ctk.CTkLabel(
            left,
            text="Minimal church operations platform • local desktop system",
            font=(MODERN_THEME["font_family"], 10),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", padx=52, pady=(24, 0))

        self.username_entry.bind("<Return>", lambda event: self._attempt_login())
        self.password_entry.bind("<Return>", lambda event: self._attempt_login())
        self.username_entry.focus()

        remembered = _load_remembered()
        if remembered.get("username") and remembered.get("password"):
            self.username_entry.insert(0, remembered["username"])
            self.password_entry.insert(0, remembered["password"])
            self.remember_var.set(True)

    def _field_frame(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color=THEME["input"],
            corner_radius=22,
            border_width=1,
            border_color=THEME["border"],
        )

    def _toggle_password(self):
        self._show_pw = not self._show_pw

        if self._show_pw:
            self.password_entry.configure(show="")
            self._eye_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="•")
            self._eye_btn.configure(text="👁")

    def _logo_fallback(self, parent):
        placeholder = ctk.CTkFrame(
            parent,
            width=38,
            height=38,
            fg_color=MODERN_THEME["primary_soft"],
            corner_radius=16,
        )
        placeholder.pack(side="left")
        placeholder.pack_propagate(False)

        ctk.CTkLabel(
            placeholder,
            text="⛪",
            font=(MODERN_THEME["font_family"], 19),
            text_color=THEME["primary"],
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _draw_background(self):
        bg_path = os.path.join("assets", "bg.png")

        if os.path.exists(bg_path):
            try:
                img = Image.open(bg_path)
                screen_w = self.winfo_screenwidth()
                screen_h = self.winfo_screenheight()
                img = img.resize((screen_w, screen_h), Image.LANCZOS)
                self._bg_img = ImageTk.PhotoImage(img)

                tk.Label(self, image=self._bg_img, bd=0).place(
                    x=0,
                    y=0,
                    relwidth=1,
                    relheight=1,
                )
            except Exception:
                self.configure(fg_color=THEME["bg_main"])
        else:
            self.configure(fg_color=THEME["bg_main"])

    def _draw_right(self, canvas, width, height):
        canvas.delete("all")

        canvas.create_rectangle(
            0,
            0,
            width,
            height,
            fill=THEME["sidebar"],
            outline="",
        )

        canvas.create_oval(
            width * 0.46,
            height * -0.10,
            width * 1.20,
            height * 0.50,
            fill=THEME["sidebar_alt"],
            outline="",
        )

        canvas.create_oval(
            width * 0.52,
            height * 0.42,
            width * 1.20,
            height * 1.18,
            fill=THEME["primary_dark"],
            outline="",
        )

        canvas.create_rectangle(
            42,
            42,
            width - 42,
            44,
            fill=THEME["primary"],
            outline="",
        )

        canvas.create_text(
            42,
            86,
            anchor="w",
            text="CHURCHTRACK",
            font=(MODERN_THEME["font_family"], 11, "bold"),
            fill=THEME["primary_soft"],
        )

        canvas.create_text(
            42,
            146,
            anchor="w",
            text="Focused tools for\nfaithful financial\nstewardship.",
            font=(MODERN_THEME["font_family"], 26, "bold"),
            fill=THEME["bg_card"],
        )

        canvas.create_text(
            42,
            292,
            anchor="w",
            text="Monitor donations, requests, reports,\nand daily church activity from one\nclean local workspace.",
            font=(MODERN_THEME["font_family"], 12),
            fill=THEME["border_strong"],
        )

        canvas.create_rectangle(
            42,
            height - 128,
            width - 42,
            height - 54,
            fill=THEME["text_main"],
            outline=THEME["border_strong"],
            width=1,
        )

        canvas.create_text(
            62,
            height - 103,
            anchor="w",
            text="Modernized GUI",
            font=(MODERN_THEME["font_family"], 12, "bold"),
            fill=THEME["bg_card"],
        )

        canvas.create_text(
            62,
            height - 78,
            anchor="w",
            text="Minimal. readable. operational.",
            font=(MODERN_THEME["font_family"], 11),
            fill=THEME["text_muted"],
        )

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
            if self.remember_var.get():
                _save_remembered(username, password)
            else:
                _clear_remembered()

            self.on_login(username, password)
        except Exception:
            self.error_label.configure(text="Invalid username or password.")
            self.login_btn.configure(state="normal", text="Sign in")