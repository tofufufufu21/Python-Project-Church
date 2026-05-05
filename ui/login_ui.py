import customtkinter as ctk
import tkinter as tk
import os
import json
from PIL import Image, ImageTk

from ui.theme import THEME, MODERN_THEME
from core.security import SecurityManager

REMEMBER_FILE = "core/.remember_me.json"

STRENGTH_COLORS = [
    "#E24B4A", "#E24B4A", "#EF9F27", "#1D9E75", "#1D9E75"
]


def _load_remembered():
    try:
        with open(REMEMBER_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_remembered(username):
    os.makedirs("core", exist_ok=True)
    with open(REMEMBER_FILE, "w") as f:
        json.dump({"username": username}, f)


def _clear_remembered():
    try:
        os.remove(REMEMBER_FILE)
    except Exception:
        pass


# ══════════════════════════════════════════════════════
# LOGIN FRAME
# ══════════════════════════════════════════════════════

class LoginFrame(ctk.CTkFrame):

    def __init__(self, master, on_login, db_manager=None):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.on_login  = on_login
        self.db        = db_manager
        self._logo_img = None
        self._bg_img   = None
        self._show_pw  = False
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        self._draw_background()

        shadow = ctk.CTkFrame(
            self, fg_color=MODERN_THEME["shadow"],
            width=886, height=566, corner_radius=22,
        )
        shadow.place(relx=0.5, rely=0.508, anchor="center")

        card = ctk.CTkFrame(
            self, fg_color=THEME["bg_card"], corner_radius=28,
            width=1000, height=560,
            border_width=1, border_color=THEME["border"],
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        left = ctk.CTkFrame(card, fg_color=THEME["bg_card"], width=500)
        left.pack(side="left", fill="both")
        left.pack_propagate(False)

        right = ctk.CTkFrame(
            card, fg_color=THEME["sidebar"],
            width=380, corner_radius=24,
        )
        right.pack(side="right", fill="both", expand=True,
                   padx=(0, 8), pady=8)
        right.pack_propagate(False)

        canvas = tk.Canvas(right, bg=THEME["sidebar"],
                           highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        canvas.bind("<Configure>",
                    lambda event: self._draw_right(canvas, event.width, event.height))

        # ── Logo row ──────────────────────────────────
        logo_row = ctk.CTkFrame(left, fg_color="transparent")
        logo_row.pack(anchor="w", padx=52, pady=(52, 0))

        logo_path = os.path.join("church_logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).resize((80, 80), Image.LANCZOS)
                self._logo_img = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(80, 80))
                ctk.CTkLabel(logo_row, image=self._logo_img, text="").pack(side="left")
            except Exception:
                self._logo_fallback(logo_row)
        else:
            self._logo_fallback(logo_row)

        ctk.CTkLabel(
            logo_row, text="ChurchTrack",
            font=(MODERN_THEME["font_family"], 21, "bold"),
            text_color=THEME["text_main"],
        ).pack(side="left", padx=(12, 0))

        # ── Welcome ───────────────────────────────────
        ctk.CTkLabel(
            left, text="Welcome back",
            font=(MODERN_THEME["font_family"], 30, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=52, pady=(54, 0))

        ctk.CTkLabel(
            left, text="Sign in to continue.",
            font=(MODERN_THEME["font_family"], 12),
            text_color=THEME["text_sub"],
            justify="left",
        ).pack(anchor="w", padx=52, pady=(4, 28))

        # ── Username field ────────────────────────────
        user_frame = self._field_frame(left)
        user_frame.pack(fill="x", padx=52, pady=(0, 14))

        ctk.CTkLabel(
            user_frame, text="👤",
            font=(MODERN_THEME["font_family"], 14),
            text_color=THEME["text_sub"],
        ).pack(side="left", padx=(18, 8), pady=12)

        self.username_entry = ctk.CTkEntry(
            user_frame, placeholder_text="Username",
            height=42, border_width=0,
            fg_color=THEME["input"],
            text_color=THEME["text_main"],
            placeholder_text_color=THEME["text_muted"],
            font=(MODERN_THEME["font_family"], 12),
        )
        self.username_entry.pack(side="left", fill="x", expand=True,
                                 padx=(0, 16), pady=6)

        # ── Password field ────────────────────────────
        pass_frame = self._field_frame(left)
        pass_frame.pack(fill="x", padx=52, pady=(0, 8))

        ctk.CTkLabel(
            pass_frame, text="🔒",
            font=(MODERN_THEME["font_family"], 14),
            text_color=THEME["text_sub"],
        ).pack(side="left", padx=(18, 8), pady=12)

        self.password_entry = ctk.CTkEntry(
            pass_frame, placeholder_text="Password",
            show="•", height=42, border_width=0,
            fg_color=THEME["input"],
            text_color=THEME["text_main"],
            placeholder_text_color=THEME["text_muted"],
            font=(MODERN_THEME["font_family"], 12),
        )
        self.password_entry.pack(side="left", fill="x", expand=True,
                                 padx=(0, 4), pady=6)

        self._eye_btn = ctk.CTkButton(
            pass_frame, text="👁", width=36, height=36,
            corner_radius=14, fg_color="transparent",
            hover_color=MODERN_THEME["surface_hover"],
            text_color=THEME["text_sub"],
            font=(MODERN_THEME["font_family"], 14),
            command=self._toggle_password,
        )
        self._eye_btn.pack(side="right", padx=(0, 10), pady=6)

        # ── Options row ───────────────────────────────
        options_row = ctk.CTkFrame(left, fg_color="transparent")
        options_row.pack(fill="x", padx=52, pady=(2, 0))

        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_row, text="Remember username",
            variable=self.remember_var,
            font=(MODERN_THEME["font_family"], 11),
            text_color=THEME["text_sub"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            checkmark_color=THEME["bg_card"],
            border_color=THEME["border_strong"],
        ).pack(side="left")

        # ── Forgot password link ──────────────────────
        ctk.CTkButton(
            options_row, text="Forgot password?",
            font=(MODERN_THEME["font_family"], 11),
            fg_color="transparent",
            hover_color=THEME["bg_main"],   # ← fixed: no "transparent"
            text_color=THEME["primary"],
            cursor="hand2",
            command=self._open_forgot_password,
        ).pack(side="right")

        # ── Error label ───────────────────────────────
        self.error_label = ctk.CTkLabel(
            left, text="",
            font=(MODERN_THEME["font_family"], 11),
            text_color=THEME["danger"],
        )
        self.error_label.pack(pady=(12, 0))

        # ── Sign in button ────────────────────────────
        self.login_btn = ctk.CTkButton(
            left, text="Sign in",
            font=(MODERN_THEME["font_family"], 14, "bold"),
            height=48, corner_radius=16,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            text_color=THEME["bg_card"],
            command=self._attempt_login,
        )
        self.login_btn.pack(fill="x", padx=52, pady=(12, 0))

        self.username_entry.bind("<Return>", lambda event: self._attempt_login())
        self.password_entry.bind("<Return>", lambda event: self._attempt_login())
        self.username_entry.focus()

        remembered = _load_remembered()
        if "password" in remembered:
            if remembered.get("username"):
                _save_remembered(remembered["username"])
            else:
                _clear_remembered()
        if remembered.get("username"):
            self.username_entry.insert(0, remembered["username"])
            self.remember_var.set(True)

    def _field_frame(self, parent):
        return ctk.CTkFrame(
            parent, fg_color=THEME["input"], corner_radius=22,
            border_width=1, border_color=THEME["border"],
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
            parent, width=38, height=38,
            fg_color=MODERN_THEME["primary_soft"], corner_radius=16,
        )
        placeholder.pack(side="left")
        placeholder.pack_propagate(False)
        ctk.CTkLabel(
            placeholder, text="⛪",
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
                    x=0, y=0, relwidth=1, relheight=1)
                return
            except Exception:
                pass
        self.configure(fg_color=THEME["bg_main"])

    def _draw_right(self, canvas, width, height):
        canvas.delete("all")
        try:
            if not hasattr(self, "_right_img_original"):
                img_path = os.path.join(os.getcwd(), "church_login.jpg")
                self._right_img_original = Image.open(img_path)
            resized = self._right_img_original.resize(
                (width, height), Image.LANCZOS)
            self._right_img = ImageTk.PhotoImage(resized)
            canvas.create_image(0, 0, anchor="nw", image=self._right_img)
        except Exception:
            canvas.create_rectangle(0, 0, width, height, fill="#000000")
        canvas.create_rectangle(
            0, 0, width, height,
            fill="#000000", stipple="gray25", outline="")

    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.error_label.configure(
                text="Please enter both username and password.")
            return
        self.login_btn.configure(state="disabled", text="Signing in...")
        self.after(300, lambda: self._do_login(username, password))

    def _do_login(self, username, password):
        try:
            self.on_login(username, password)
            if self.remember_var.get():
                _save_remembered(username)
            else:
                _clear_remembered()
        except Exception:
            self.error_label.configure(text="Invalid username or password.")
            self.login_btn.configure(state="normal", text="Sign in")

    def _open_forgot_password(self):
        if self.db is None:
            self.error_label.configure(text="Password reset is unavailable.")
            return
        ForgotPasswordModal(self, self.db)


# ══════════════════════════════════════════════════════
# FORGOT PASSWORD MODAL  (4-step flow)
# ══════════════════════════════════════════════════════

class ForgotPasswordModal:
    """
    Step 1  -  Identify account (enter username)
    Step 2  -  Set new password + confirm + strength meter
    """

    STEP_LABELS = [
        "Identify account",
        "New password",
    ]

    def __init__(self, master, db_manager):
        self.db        = db_manager
        self._username = None
        self._otp      = None
        self._step     = 1

        self.modal = ctk.CTkToplevel(master)
        self.modal.title("Reset Password")
        self.modal.geometry("620x720")
        self.modal.resizable(False, False)
        self.modal.grab_set()
        self.modal.configure(fg_color=THEME["bg_card"])

        self._build_shell()
        self._show_step(1)

    # ── Shell ──────────────────────────────────────────

    def _build_shell(self):
        # Coloured header bar
        hdr = ctk.CTkFrame(
            self.modal, fg_color=THEME["primary"], corner_radius=0
        )
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="Reset Password",
            font=(MODERN_THEME["font_family"], 15, "bold"),
            text_color=THEME["bg_card"]
        ).pack(side="left", padx=20, pady=14)

        # Step progress strip
        prog = ctk.CTkFrame(
            self.modal, fg_color=THEME["bg_panel"], height=52
        )
        prog.pack(fill="x")
        prog.pack_propagate(False)

        self._step_widgets = []
        for i, label in enumerate(self.STEP_LABELS):
            sf = ctk.CTkFrame(prog, fg_color="transparent")
            sf.pack(side="left", expand=True, fill="both")
            lbl = ctk.CTkLabel(
                sf,
                text="{}. {}".format(i + 1, label),
                font=(MODERN_THEME["font_family"], 10),
                text_color=THEME["text_muted"],
                anchor="center",
            )
            lbl.pack(expand=True, pady=6)
            line = ctk.CTkFrame(sf, fg_color=THEME["border"], height=3)
            line.pack(fill="x", side="bottom")
            self._step_widgets.append((lbl, line))

        # Swappable content area
        self._content = ctk.CTkFrame(
            self.modal, fg_color=THEME["bg_card"]
        )
        self._content.pack(fill="both", expand=True, padx=40, pady=(24, 20))

    def _update_progress(self):
        for i, (lbl, line) in enumerate(self._step_widgets):
            n = i + 1
            if n == self._step:
                lbl.configure(
                    text_color=THEME["primary"],
                    font=(MODERN_THEME["font_family"], 10, "bold")
                )
                line.configure(fg_color=THEME["primary"])
            elif n < self._step:
                lbl.configure(
                    text_color=THEME["success"],
                    font=(MODERN_THEME["font_family"], 10)
                )
                line.configure(fg_color=THEME["success"])
            else:
                lbl.configure(
                    text_color=THEME["text_muted"],
                    font=(MODERN_THEME["font_family"], 10)
                )
                line.configure(fg_color=THEME["border"])

    def _clear(self):
        for w in self._content.winfo_children():
            w.destroy()

    def _show_step(self, n):
        self._step = n
        self._update_progress()
        self._clear()
        {1: self._step1,
         2: self._step2}[n]()

    # ── Reusable widget helpers ────────────────────────

    def _heading(self, parent, title, subtitle=""):
        ctk.CTkLabel(
            parent, text=title,
            font=(MODERN_THEME["font_family"], 18, "bold"),
            text_color=THEME["text_main"],
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))
        if subtitle:
            ctk.CTkLabel(
                parent, text=subtitle,
                font=(MODERN_THEME["font_family"], 11),
                text_color=THEME["text_sub"],
                wraplength=460, justify="left", anchor="w",
            ).pack(anchor="w", pady=(0, 20))

    def _plain_entry(self, parent, placeholder, show=""):
        e = ctk.CTkEntry(
            parent, placeholder_text=placeholder,
            height=46, corner_radius=12, show=show,
            border_width=1, border_color=THEME["border"],
            fg_color=THEME["input"],
            text_color=THEME["text_main"],
            placeholder_text_color=THEME["text_muted"],
            font=(MODERN_THEME["font_family"], 13),
        )
        e.pack(fill="x", pady=(0, 14))
        return e

    def _pw_field(self, parent, placeholder):
        wrap = ctk.CTkFrame(
            parent, fg_color=THEME["input"],
            corner_radius=12,
            border_width=1, border_color=THEME["border"]
        )
        wrap.pack(fill="x", pady=(0, 8))
        entry = ctk.CTkEntry(
            wrap, placeholder_text=placeholder,
            show="•", height=42, border_width=0,
            fg_color="transparent",
            text_color=THEME["text_main"],
            placeholder_text_color=THEME["text_muted"],
            font=(MODERN_THEME["font_family"], 13),
        )
        entry.pack(side="left", fill="x", expand=True, padx=(14, 0))
        visible = [False]

        def _toggle():
            visible[0] = not visible[0]
            entry.configure(show="" if visible[0] else "•")
            eye.configure(text="🙈" if visible[0] else "👁")

        eye = ctk.CTkButton(
            wrap, text="👁", width=36, height=36,
            corner_radius=14, fg_color="transparent",
            hover_color=THEME["border"],
            text_color=THEME["text_sub"],
            font=(MODERN_THEME["font_family"], 14),
            command=_toggle
        )
        eye.pack(side="right", padx=(0, 6))
        return entry

    def _error(self, parent):
        lbl = ctk.CTkLabel(
            parent, text="",
            font=(MODERN_THEME["font_family"], 11),
            text_color=THEME["danger"],
            anchor="w",
        )
        lbl.pack(anchor="w", pady=(0, 6))
        return lbl

    def _primary_btn(self, parent, text, command):
        btn = ctk.CTkButton(
            parent, text=text,
            height=48, corner_radius=14,
            font=(MODERN_THEME["font_family"], 13, "bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            text_color=THEME["bg_card"],
            command=command
        )
        btn.pack(fill="x", pady=(10, 0))
        return btn

    # ══════════════════════════════════════════════════
    # STEP 1 — Enter username
    # ══════════════════════════════════════════════════

    def _step1(self):
        p = self._content
        self._heading(
            p, "Identify your account",
            "Enter the username of the account you want to reset."
        )
        user_entry = self._plain_entry(p, "Username")
        err = self._error(p)

        def proceed():
            username = user_entry.get().strip()
            if not username:
                err.configure(text="Please enter your username.")
                return
            if not self.db.user_exists(username):
                err.configure(text="No account found with that username.")
                return
            otp = self.db.generate_reset_token(username)
            if not otp:
                err.configure(text="Could not start password reset. Try again.")
                return
            self._username = username
            self._otp      = otp
            self._show_step(2)

        self._primary_btn(p, "Next  →", proceed)
        user_entry.bind("<Return>", lambda e: proceed())
        user_entry.focus()

    # Step 2 - New password + confirm

    def _step2(self):
        p = self._content
        self._heading(
            p, "Create a new password",
            "Must be 12+ characters with uppercase, lowercase, "
            "numbers, and special characters."
        )

        pw_entry = self._pw_field(p, "New password")

        # Strength bar
        bar_outer = ctk.CTkFrame(
            p, fg_color=THEME["bg_panel"],
            corner_radius=4, height=8
        )
        bar_outer.pack(fill="x", pady=(0, 4))
        bar_outer.pack_propagate(False)

        bar_inner = ctk.CTkFrame(
            bar_outer, fg_color=THEME["border"],
            corner_radius=4, height=8
        )
        bar_inner.place(x=0, y=0, relheight=1, relwidth=0)

        strength_lbl = ctk.CTkLabel(
            p, text="",
            font=(MODERN_THEME["font_family"], 10),
            text_color=THEME["text_sub"],
            anchor="e",
        )
        strength_lbl.pack(anchor="e", pady=(0, 8))

        # Requirements checklist
        req_card = ctk.CTkFrame(
            p, fg_color=THEME["bg_panel"],
            corner_radius=10,
            border_width=1, border_color=THEME["border"]
        )
        req_card.pack(fill="x", pady=(0, 10))

        req_items = [
            ("length",    "At least 12 characters"),
            ("uppercase", "Uppercase letter (A–Z)"),
            ("lowercase", "Lowercase letter (a–z)"),
            ("digit",     "Number (0–9)"),
            ("special",   "Special character (!@#$%…)"),
        ]
        req_widgets = {}
        for key, text in req_items:
            row = ctk.CTkFrame(req_card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            dot = ctk.CTkLabel(
                row, text="○",
                font=(MODERN_THEME["font_family"], 11),
                text_color=THEME["text_muted"], width=18, anchor="w",
            )
            dot.pack(side="left")
            txt = ctk.CTkLabel(
                row, text=text,
                font=(MODERN_THEME["font_family"], 11),
                text_color=THEME["text_muted"], anchor="w",
            )
            txt.pack(side="left")
            req_widgets[key] = (dot, txt)
        ctk.CTkLabel(req_card, text="").pack(pady=2)

        conf_entry = self._pw_field(p, "Confirm new password")

        match_lbl = ctk.CTkLabel(
            p, text="",
            font=(MODERN_THEME["font_family"], 10),
            text_color=THEME["text_sub"],
            anchor="w",
        )
        match_lbl.pack(anchor="w", pady=(0, 4))

        err = self._error(p)

        def _on_pw(*_):
            pw     = pw_entry.get()
            result = SecurityManager.validate_password_strength(pw)
            score  = result["score"]
            bar_inner.place(x=0, y=0, relheight=1, relwidth=score / 5.0)
            color = STRENGTH_COLORS[min(score, 4)]
            bar_inner.configure(fg_color=color)
            strength_lbl.configure(
                text=result["label"] if pw else "",
                text_color=color)
            for key, (dot, txt) in req_widgets.items():
                ok = result["checks"][key]
                dot.configure(
                    text="✓" if ok else "○",
                    text_color=THEME["success"] if ok else THEME["text_muted"])
                txt.configure(
                    text_color=THEME["text_main"] if ok else THEME["text_muted"])
            _on_conf()

        def _on_conf(*_):
            pw   = pw_entry.get()
            conf = conf_entry.get()
            if not conf:
                match_lbl.configure(text="")
                return
            if pw == conf:
                match_lbl.configure(
                    text="✓  Passwords match", text_color=THEME["success"])
            else:
                match_lbl.configure(
                    text="✗  Passwords do not match", text_color=THEME["danger"])

        pw_entry.bind("<KeyRelease>", _on_pw)
        conf_entry.bind("<KeyRelease>", _on_conf)

        def do_reset():
            pw   = pw_entry.get()
            conf = conf_entry.get()
            result = SecurityManager.validate_password_strength(pw)
            if not result["valid"]:
                err.configure(text=result["errors"][0])
                return
            if pw != conf:
                err.configure(text="Passwords do not match.")
                return
            ok = self.db.reset_password_with_token(self._username, self._otp, pw)
            if not ok:
                err.configure(
                    text="Reset session expired. Please start over.")
                return
            self._clear()
            self._step = len(self.STEP_LABELS) + 1
            self._update_progress()
            self._success_screen()

        ctk.CTkButton(
            p, text="Reset Password  →",
            height=48, corner_radius=14,
            font=(MODERN_THEME["font_family"], 13, "bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            text_color=THEME["bg_card"],
            command=do_reset
        ).pack(fill="x", pady=(10, 0))
        conf_entry.bind("<Return>", lambda e: do_reset())

    # ── Success screen ─────────────────────────────────

    def _success_screen(self):
        p = self._content

        ctk.CTkLabel(
            p, text="✓",
            font=(MODERN_THEME["font_family"], 52),
            text_color=THEME["success"]
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            p, text="Password reset successfully!",
            font=(MODERN_THEME["font_family"], 18, "bold"),
            text_color=THEME["text_main"]
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            p,
            text="Your password has been updated.\n"
                 "You can now sign in with your new password.",
            font=(MODERN_THEME["font_family"], 12),
            text_color=THEME["text_sub"],
            justify="center"
        ).pack(pady=(0, 28))

        ctk.CTkButton(
            p, text="Back to Sign In",
            height=46, corner_radius=14,
            font=(MODERN_THEME["font_family"], 13, "bold"),
            fg_color=THEME["success"],
            hover_color=THEME["success"],
            text_color="#FFFFFF",
            command=self.modal.destroy
        ).pack(fill="x")
