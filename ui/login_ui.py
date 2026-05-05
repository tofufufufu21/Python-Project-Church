import datetime
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


def _save_remembered(username, password):
    os.makedirs("core", exist_ok=True)
    with open(REMEMBER_FILE, "w") as f:
        json.dump({"username": username, "password": password}, f)


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
            options_row, text="Remember me",
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
        if remembered.get("username") and remembered.get("password"):
            self.username_entry.insert(0, remembered["username"])
            self.password_entry.insert(0, remembered["password"])
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
        password = self.password_entry.get().strip()
        if not username or not password:
            self.error_label.configure(
                text="Please enter both username and password.")
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
    Step 1  —  Identify account (enter username)
    Step 2  —  Display one-time security code (OTP)
    Step 3  —  Verify the code (6-box digit entry)
    Step 4  —  Set new password + confirm + strength meter
    """

    STEP_LABELS = [
        "Identify account",
        "Security code",
        "Verify code",
        "New password",
    ]

    def __init__(self, master, db_manager):
        self.db        = db_manager
        self._username = None
        self._otp      = None
        self._step     = 1

        self.modal = ctk.CTkToplevel(master)
        self.modal.title("Reset Password")
        self.modal.geometry("540x600")
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
        self._content.pack(fill="both", expand=True, padx=36, pady=28)

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
         2: self._step2,
         3: self._step3,
         4: self._step4}[n]()

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
                err.configure(text="Could not generate a reset code. Try again.")
                return
            self._username = username
            self._otp      = otp
            self._show_step(2)

        self._primary_btn(p, "Next  →", proceed)
        user_entry.bind("<Return>", lambda e: proceed())
        user_entry.focus()

    # ══════════════════════════════════════════════════
    # STEP 2 — Display OTP
    # ══════════════════════════════════════════════════

    def _step2(self):
        p = self._content
        self._heading(
            p, "Your security code",
            "Note the one-time code below before proceeding. "
            "It expires in 15 minutes."
        )

        code_card = ctk.CTkFrame(
            p, fg_color=THEME["primary_soft"],
            corner_radius=16,
            border_width=2, border_color=THEME["primary"]
        )
        code_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            code_card,
            text="One-time security code",
            font=(MODERN_THEME["font_family"], 11),
            text_color=THEME["primary"],
            anchor="center",
        ).pack(pady=(14, 8))

        digits_row = ctk.CTkFrame(code_card, fg_color="transparent")
        digits_row.pack(pady=(0, 14))

        for digit in self._otp:
            box = ctk.CTkFrame(
                digits_row,
                fg_color=THEME["bg_card"],
                corner_radius=10,
                border_width=1, border_color=THEME["primary"],
                width=52, height=58
            )
            box.pack(side="left", padx=4)
            box.pack_propagate(False)
            ctk.CTkLabel(
                box, text=digit,
                font=(MODERN_THEME["font_family"], 28, "bold"),
                text_color=THEME["primary"]
            ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            code_card,
            text="Valid for 15 minutes  ·  single use",
            font=(MODERN_THEME["font_family"], 10),
            text_color=THEME["text_sub"],
            anchor="center",
        ).pack(pady=(0, 12))

        expiry_lbl = ctk.CTkLabel(
            p, text="",
            font=(MODERN_THEME["font_family"], 11),
            text_color=THEME["warning"],
            anchor="w",
        )
        expiry_lbl.pack(anchor="w", pady=(0, 8))

        _start = datetime.datetime.now()

        def _tick():
            elapsed   = (datetime.datetime.now() - _start).seconds
            remaining = max(0, 15 * 60 - elapsed)
            mins = remaining // 60
            secs = remaining % 60
            expiry_lbl.configure(
                text="Expires in:  {:02d}:{:02d}".format(mins, secs))
            if remaining > 0:
                try:
                    p.after(1000, _tick)
                except Exception:
                    pass

        _tick()
        self._primary_btn(p, "I've saved my code  →",
                          lambda: self._show_step(3))

    # ══════════════════════════════════════════════════
    # STEP 3 — Verify OTP
    # ══════════════════════════════════════════════════

    def _step3(self):
        p = self._content
        self._heading(
            p, "Enter the security code",
            "Type the 6-digit code shown in the previous step."
        )

        digits_row = ctk.CTkFrame(p, fg_color="transparent")
        digits_row.pack(anchor="w", pady=(0, 18))

        digit_vars    = []
        digit_entries = []

        def _on_key(event, idx):
            val = event.widget.get()
            if val and not val[-1].isdigit():
                event.widget.delete(0, "end")
                if len(val) > 1:
                    event.widget.insert(0, val[:-1])
                return
            if len(val) >= 1:
                event.widget.delete(0, "end")
                event.widget.insert(0, val[-1])
                if idx < 5:
                    digit_entries[idx + 1].focus()
            elif event.keysym == "BackSpace" and idx > 0:
                digit_entries[idx - 1].focus()
                digit_entries[idx - 1].delete(0, "end")

        for i in range(6):
            var = ctk.StringVar()
            outer = ctk.CTkFrame(
                digits_row,
                fg_color=THEME["input"],
                corner_radius=10,
                border_width=1, border_color=THEME["border"],
                width=56, height=62
            )
            outer.pack(side="left", padx=4)
            outer.pack_propagate(False)
            e = ctk.CTkEntry(
                outer, textvariable=var,
                width=40, height=48,
                border_width=0,
                fg_color="transparent",
                text_color=THEME["text_main"],
                font=(MODERN_THEME["font_family"], 24, "bold"),
                justify="center"
            )
            e.place(relx=0.5, rely=0.5, anchor="center")
            e.bind("<KeyRelease>", lambda ev, i=i: _on_key(ev, i))
            digit_vars.append(var)
            digit_entries.append(e)

        err = self._error(p)
        attempts_left = [3]

        def verify():
            code = "".join(v.get() for v in digit_vars)
            if len(code) < 6:
                err.configure(text="Please fill in all 6 digits.")
                return
            if self.db.verify_reset_token(self._username, code):
                self._otp = code
                self._show_step(4)
            else:
                attempts_left[0] -= 1
                for e2 in digit_entries:
                    e2.delete(0, "end")
                digit_entries[0].focus()
                if attempts_left[0] <= 0:
                    err.configure(
                        text="Too many incorrect attempts. Please start over.")
                    self._primary_btn(p, "Start over",
                                      lambda: self._show_step(1))
                    return
                err.configure(
                    text="Incorrect code.  {} attempt(s) remaining.".format(
                        attempts_left[0]))

        self._primary_btn(p, "Verify code  →", verify)
        digit_entries[-1].bind("<Return>", lambda e: verify())
        digit_entries[0].focus()

    # ══════════════════════════════════════════════════
    # STEP 4 — New password + confirm
    # ══════════════════════════════════════════════════

    def _step4(self):
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
                    text="Code expired or already used. Please start over.")
                return
            self._clear()
            self._step = 5
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