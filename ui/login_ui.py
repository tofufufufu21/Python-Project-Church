import customtkinter as ctk
import tkinter as tk
import os
from PIL import Image, ImageTk
from ui.theme import THEME


class LoginFrame(ctk.CTkFrame):

    def __init__(self, master, on_login):
        super().__init__(master, fg_color="#4a5a8a")
        self.on_login  = on_login
        self._logo_img = None
        self._bg_img   = None
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self._draw_background()

        card = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=18,
            border_width=2,
            border_color="#C8D8F0",
            width=820,
            height=500
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # ── LEFT PANEL ──────────────────────────────────
        left = ctk.CTkFrame(
            card, fg_color="#FFFFFF",
            corner_radius=0, width=420
        )
        left.pack(side="left", fill="both")
        left.pack_propagate(False)

        # Logo row
        logo_row = ctk.CTkFrame(
            left, fg_color="transparent"
        )
        logo_row.pack(anchor="w", padx=44, pady=(44, 0))

        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).resize(
                    (38, 38), Image.LANCZOS
                )
                self._logo_img = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(38, 38)
                )
                ctk.CTkLabel(
                    logo_row,
                    image=self._logo_img,
                    text=""
                ).pack(side="left")
            except Exception:
                self._logo_fallback(logo_row)
        else:
            self._logo_fallback(logo_row)

        ctk.CTkLabel(
            logo_row, text="ChurchTrack",
            font=("Arial", 20, "bold"),
            text_color="#1a2a4a"
        ).pack(side="left", padx=(10, 0))

        # Welcome text
        ctk.CTkLabel(
            left,
            text="Welcome Back!",
            font=("Georgia", 28, "bold"),
            text_color="#1a2a4a"
        ).pack(anchor="w", padx=44, pady=(28, 0))

        ctk.CTkLabel(
            left,
            text="Please sign in to continue.",
            font=("Arial", 12),
            text_color="#888888"
        ).pack(anchor="w", padx=44, pady=(4, 20))

        # Username field
        user_frame = ctk.CTkFrame(
            left, fg_color="#F3F6FB",
            corner_radius=30, border_width=1,
            border_color="#D0DCF0"
        )
        user_frame.pack(fill="x", padx=44, pady=(0, 12))

        ctk.CTkLabel(
            user_frame, text="👤",
            font=("Arial", 14),
            fg_color="transparent"
        ).pack(side="left", padx=(18, 4), pady=10)

        self.username_entry = ctk.CTkEntry(
            user_frame,
            placeholder_text="Username",
            height=38, border_width=0,
            fg_color="#F3F6FB",
            text_color="#1a2a4a",
            placeholder_text_color="#AAAAAA",
            font=("Arial", 13)
        )
        self.username_entry.pack(
            side="left", fill="x", expand=True,
            padx=(0, 16), pady=6
        )

        # Password field
        pass_frame = ctk.CTkFrame(
            left, fg_color="#F3F6FB",
            corner_radius=30, border_width=1,
            border_color="#D0DCF0"
        )
        pass_frame.pack(fill="x", padx=44, pady=(0, 10))

        ctk.CTkLabel(
            pass_frame, text="🔒",
            font=("Arial", 14),
            fg_color="transparent"
        ).pack(side="left", padx=(18, 4), pady=10)

        self.password_entry = ctk.CTkEntry(
            pass_frame,
            placeholder_text="Password",
            show="•", height=38,
            border_width=0,
            fg_color="#F3F6FB",
            text_color="#1a2a4a",
            placeholder_text_color="#AAAAAA",
            font=("Arial", 13)
        )
        self.password_entry.pack(
            side="left", fill="x", expand=True,
            padx=(0, 16), pady=6
        )

        # Remember me + Forgot password
        options_row = ctk.CTkFrame(
            left, fg_color="transparent"
        )
        options_row.pack(fill="x", padx=44, pady=(2, 0))

        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_row,
            text="Remember Me",
            variable=self.remember_var,
            font=("Arial", 11),
            text_color="#555555",
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            checkmark_color="#FFFFFF",
            border_color="#CCCCCC",
            width=16, height=16,
            corner_radius=4
        ).pack(side="left")

        ctk.CTkLabel(
            options_row,
            text="Forgot  Password?",
            font=("Arial", 11),
            text_color=THEME["primary"],
            cursor="hand2"
        ).pack(side="right")

        # Error label
        self.error_label = ctk.CTkLabel(
            left, text="",
            font=("Arial", 11),
            text_color=THEME["danger"]
        )
        self.error_label.pack(pady=(8, 0))

        # Login button
        self.login_btn = ctk.CTkButton(
            left,
            text="Log in",
            font=("Arial", 14, "bold"),
            height=48, corner_radius=30,
            fg_color="#1a3a8a",
            hover_color="#1a2a6a",
            text_color="#FFFFFF",
            command=self._attempt_login
        )
        self.login_btn.pack(
            fill="x", padx=44, pady=(10, 0)
        )

        self.username_entry.bind(
            "<Return>", lambda e: self._attempt_login()
        )
        self.password_entry.bind(
            "<Return>", lambda e: self._attempt_login()
        )
        self.username_entry.focus()

        # ── RIGHT PANEL ─────────────────────────────────
        right = ctk.CTkFrame(
            card, fg_color="#1a3a8a",
            corner_radius=18, width=400
        )
        right.pack(side="right", fill="both", expand=True)
        right.pack_propagate(False)

        canvas = tk.Canvas(
            right, bg="#1a3a8a",
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True)

        canvas.bind(
            "<Configure>",
            lambda e: self._draw_right(
                canvas, e.width, e.height
            )
        )

    def _logo_fallback(self, parent):
        placeholder = ctk.CTkFrame(
            parent,
            width=38, height=38,
            fg_color="#E8EDF5",
            corner_radius=8,
            border_width=1,
            border_color="#D0DCF0"
        )
        placeholder.pack(side="left")
        placeholder.pack_propagate(False)
        ctk.CTkLabel(
            placeholder,
            text="⛪",
            font=("Arial", 20),
            text_color="#1a2a4a"
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _draw_background(self):
        bg_path = os.path.join("assets", "bg.png")
        if os.path.exists(bg_path):
            try:
                img = Image.open(bg_path)
                sw  = self.winfo_screenwidth()
                sh  = self.winfo_screenheight()
                img = img.resize(
                    (sw, sh), Image.LANCZOS
                )
                self._bg_img = ImageTk.PhotoImage(img)
                tk.Label(
                    self,
                    image=self._bg_img,
                    bd=0
                ).place(
                    x=0, y=0,
                    relwidth=1, relheight=1
                )
                return
            except Exception:
                pass
        self.configure(fg_color="#4a5a8a")

    def _draw_right(self, c, W, H):
        c.delete("all")

        c.create_rectangle(
            0, 0, W, H,
            fill="#1a3a8a", outline=""
        )

        shapes = [
            [
                (W * 0.50, H * 0.05),
                (W * 0.75, H * 0.22),
                (W * 0.75, H * 0.55),
                (W * 0.50, H * 0.72),
                (W * 0.25, H * 0.55),
                (W * 0.25, H * 0.22),
            ],
            [
                (W * 0.72, H * 0.00),
                (W * 0.97, H * 0.12),
                (W * 0.97, H * 0.38),
                (W * 0.72, H * 0.50),
                (W * 0.47, H * 0.38),
                (W * 0.47, H * 0.12),
            ],
            [
                (W * 0.05, H * 0.55),
                (W * 0.30, H * 0.67),
                (W * 0.30, H * 0.93),
                (W * 0.05, H * 1.05),
                (-W * 0.20, H * 0.93),
                (-W * 0.20, H * 0.67),
            ],
            [
                (-W * 0.05, H * 0.10),
                (W * 0.12, H * 0.20),
                (W * 0.12, H * 0.42),
                (-W * 0.05, H * 0.52),
                (-W * 0.22, H * 0.42),
                (-W * 0.22, H * 0.20),
            ],
            [
                (W * 0.78, H * 0.65),
                (W * 1.03, H * 0.77),
                (W * 1.03, H * 1.03),
                (W * 0.78, H * 1.15),
                (W * 0.53, H * 1.03),
                (W * 0.53, H * 0.77),
            ],
            [
                (W * 0.28, H * 0.00),
                (W * 0.53, H * 0.12),
                (W * 0.53, H * 0.38),
                (W * 0.28, H * 0.50),
                (W * 0.03, H * 0.38),
                (W * 0.03, H * 0.12),
            ],
            [
                (W * 0.50, H * 0.55),
                (W * 0.75, H * 0.67),
                (W * 0.75, H * 0.93),
                (W * 0.50, H * 1.05),
                (W * 0.25, H * 0.93),
                (W * 0.25, H * 0.67),
            ],
            [
                (W * 0.28, H * 0.40),
                (W * 0.53, H * 0.52),
                (W * 0.53, H * 0.78),
                (W * 0.28, H * 0.90),
                (W * 0.03, H * 0.78),
                (W * 0.03, H * 0.52),
            ],
        ]

        shade_colors = [
            "#2a4fbb", "#1e3f9a",
            "#2a52b8", "#1e3a92",
            "#2248a8", "#1a3888",
            "#2a4db5", "#1e3d96",
        ]

        for shape, color in zip(shapes, shade_colors):
            flat = [
                coord
                for point in shape
                for coord in point
            ]
            c.create_polygon(
                flat, fill=color,
                outline="#3a5acc", width=1
            )

    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_label.configure(
                text="Please enter both username and password."
            )
            return

        self.login_btn.configure(
            state="disabled", text="Signing in..."
        )
        self.error_label.configure(text="")
        self.after(
            300,
            lambda: self._do_login(username, password)
        )

    def _do_login(self, username, password):
        try:
            self.on_login(username, password)
        except Exception:
            self.error_label.configure(
                text="Invalid username or password."
            )
            self.login_btn.configure(
                state="normal", text="Log in"
            )
