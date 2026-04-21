import customtkinter as ctk
import threading
import os
from ui.theme import THEME


SYSTEM_PROMPT = """You are ChurchTrack AI Assistant, an intelligent financial advisor
built specifically for Catholic parish financial management in the Philippines.

You have access to real-time financial data from the ChurchTrack system.
You speak in a helpful, professional, and faith-sensitive tone.
You answer questions about donations, expenses, forecasts, and parish finances.
You give practical advice based on the actual data provided.
You respond concisely — no more than 3-4 sentences unless a detailed breakdown is asked.
Always use Philippine Peso (P) for amounts.
"""


def get_church_context(db_manager, ai_engine):
    try:
        kpi     = db_manager.get_kpi_data()
        health  = ai_engine.check_financial_health()
        result  = ai_engine.run_forecast()
        pending = db_manager.get_pending_expenses()
        recent  = db_manager.get_recent_transactions()

        context  = "\n--- CURRENT CHURCH FINANCIAL DATA ---\n"
        context += "Total Donations (all time): " + kpi["total_donations"] + "\n"
        context += "Total Approved Expenses: "    + kpi["total_expenses"]  + "\n"
        context += "Net Balance: "                + kpi["net_balance"]     + "\n"
        context += "Pending Expense Requests: "   + kpi["pending_expenses"] + "\n"

        context += "\nFinancial Health:\n"
        context += "  Income:   P{:,.0f}\n".format(health["income"])
        context += "  Expenses: P{:,.0f}\n".format(health["expenses"])
        context += "  Balance:  P{:,.0f}\n".format(health["net_balance"])

        if health["warnings"]:
            context += "  Warnings:\n"
            for w in health["warnings"]:
                context += "    - " + w["level"] + ": " + w["message"] + "\n"
        else:
            context += "  Status: Financially healthy\n"

        if "error" not in result:
            context += "\n6-Month Income Forecast:\n"
            for _, row in result["forecast_df"].iterrows():
                context += "  " + row["ds"].strftime("%B %Y") + \
                           ": P{:,.0f}\n".format(row["yhat"])

            context += "\nRevenue by Category:\n"
            cat_totals = (
                result["category_df"]
                .groupby("category")["amount"]
                .sum().reset_index()
                .sort_values("amount", ascending=False)
            )
            for _, row in cat_totals.iterrows():
                context += "  " + str(row["category"]) + \
                           ": P{:,.0f}\n".format(row["amount"])

        if pending:
            context += "\nPending Expense Requests:\n"
            for exp in pending[:5]:
                exp_id, date, cat, amount, reason, submitted_by = exp
                context += "  - " + str(cat) + \
                           " P{:,.0f}".format(amount) + \
                           " (" + str(reason)[:50] + ")\n"

        if recent:
            context += "\nRecent Transactions (last 5):\n"
            for row in recent[:5]:
                date, donor, cat, amount = row
                context += "  - " + str(date) + \
                           " | " + str(donor) + \
                           " | " + str(cat) + \
                           " | P{:,.0f}\n".format(amount)

        context += "--- END OF CHURCH DATA ---\n"
        return context

    except Exception as e:
        return "\n--- Church data unavailable: " + str(e) + " ---\n"


def load_api_key():
    try:
        with open("core/.groq_key", "r") as f:
            key = f.read().strip()
            if key.startswith("gsk_"):
                return key
    except Exception:
        pass
    return None


def save_api_key(key):
    try:
        os.makedirs("core", exist_ok=True)
        with open("core/.groq_key", "w") as f:
            f.write(key)
        return True
    except Exception:
        return False


def call_groq(api_key, system_prompt, history, user_message):
    from groq import Groq

    client   = Groq(api_key=api_key)
    messages = [{"role": "system", "content": system_prompt}]

    for msg in history[-10:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────
# FLOATING CHAT WINDOW
# ─────────────────────────────────────────

class ChatbotWindow(ctk.CTkToplevel):

    def __init__(self, master, db_manager, ai_engine):
        super().__init__(master)
        self.db      = db_manager
        self.ai      = ai_engine
        self.history = []
        self.api_key = load_api_key()

        self.title("ChurchTrack AI Assistant")
        self.geometry("520x700")
        self.resizable(True, True)
        self.grab_set()
        self._build()

    def _build(self):
        # Header
        header = ctk.CTkFrame(
            self, fg_color=THEME["sidebar"], corner_radius=0
        )
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="⛪  ChurchTrack AI Assistant",
            font=("Arial", 15, "bold"),
            text_color="#FFFFFF"
        ).pack(side="left", padx=20, pady=14)

        ctk.CTkLabel(
            header,
            text="Free — Groq + Llama 3.3",
            font=("Arial", 10),
            text_color=THEME["sidebar_sub"]
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Clear",
            font=("Arial", 11), width=60, height=28,
            corner_radius=6,
            fg_color=THEME["sidebar_hover"],
            hover_color="#3A4A5E",
            text_color="#FFFFFF",
            command=self._clear_chat
        ).pack(side="right", padx=10)

        # API key frame
        self.api_frame = ctk.CTkFrame(
            self, fg_color="#FFF9C4",
            corner_radius=0, border_width=1,
            border_color="#FFC107"
        )

        ctk.CTkLabel(
            self.api_frame,
            text="Enter your FREE Groq API Key to activate:",
            font=("Arial", 11, "bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(10, 2))

        ctk.CTkLabel(
            self.api_frame,
            text="Get your free key at console.groq.com (takes 2 minutes)",
            font=("Arial", 10),
            text_color=THEME["text_sub"]
        ).pack(anchor="w", padx=16, pady=(0, 6))

        api_row = ctk.CTkFrame(
            self.api_frame, fg_color="transparent"
        )
        api_row.pack(fill="x", padx=16, pady=(0, 10))

        self.api_entry = ctk.CTkEntry(
            api_row,
            placeholder_text="gsk_...",
            show="•", height=36, corner_radius=8,
            border_color=THEME["border"],
            fg_color="#FFFFFF",
            text_color=THEME["text_main"]
        )
        self.api_entry.pack(
            side="left", fill="x", expand=True
        )

        ctk.CTkButton(
            api_row, text="Activate",
            font=("Arial", 12, "bold"),
            width=80, height=36,
            corner_radius=8,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._save_api_key
        ).pack(side="left", padx=(8, 0))

        # Chat messages
        self.chat_frame = ctk.CTkScrollableFrame(
            self, fg_color=THEME["bg_main"]
        )
        self.chat_frame.pack(fill="both", expand=True)

        # Suggested questions
        sugg_frame = ctk.CTkFrame(
            self, fg_color=THEME["bg_main"]
        )
        sugg_frame.pack(fill="x", padx=8, pady=(4, 0))

        for s in [
            "Our balance?",
            "Donation trends?",
            "Any warnings?",
            "This month summary",
        ]:
            ctk.CTkButton(
                sugg_frame, text=s,
                font=("Arial", 9), height=24,
                corner_radius=20,
                fg_color=THEME["bg_card"],
                text_color=THEME["text_main"],
                border_width=1,
                border_color=THEME["border"],
                hover_color="#E8EDF5",
                command=lambda q=s: self._quick_ask(q)
            ).pack(side="left", padx=2, pady=2)

        # Input bar
        input_frame = ctk.CTkFrame(
            self, fg_color=THEME["bg_card"],
            corner_radius=0, border_width=1,
            border_color=THEME["border"]
        )
        input_frame.pack(fill="x")

        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Ask about your church finances...",
            height=44, corner_radius=10,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"],
            font=("Arial", 12)
        )
        self.input_entry.pack(
            side="left", fill="x", expand=True,
            padx=(12, 8), pady=10
        )
        self.input_entry.bind("<Return>", lambda e: self._send())

        self.send_btn = ctk.CTkButton(
            input_frame, text="Send",
            font=("Arial", 12, "bold"),
            width=70, height=44,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._send
        )
        self.send_btn.pack(
            side="right", padx=(0, 10), pady=10
        )

        # Show API frame or welcome
        if self.api_key:
            self.api_frame.pack_forget()
            self._welcome_message()
        else:
            self.api_frame.pack(fill="x", after=header)
            self._add_message(
                "bot",
                "Please enter your free Groq API key "
                "in the yellow bar above to get started.\n\n"
                "Get it free at console.groq.com"
            )

    def _save_api_key(self):
        key = self.api_entry.get().strip()
        if not key.startswith("gsk_"):
            self._add_message(
                "bot",
                "Invalid key format. "
                "Groq keys start with gsk_..."
            )
            return
        if save_api_key(key):
            self.api_key = key
            self.api_frame.pack_forget()
            self._clear_chat()
            self._welcome_message()
        else:
            self._add_message(
                "bot",
                "Could not save key. Please try again."
            )

    def _welcome_message(self):
        try:
            health = self.ai.check_financial_health()
            msg = (
                "Hello! I am your ChurchTrack AI Assistant "
                "powered by Groq + Llama 3.3 — completely free.\n\n"
                "Current Net Balance: P{:,.0f}\n".format(
                    health["net_balance"]
                )
            )
            if health["warnings"]:
                msg += "Warning: " + \
                       health["warnings"][0]["message"]
            else:
                msg += "Finances are looking healthy."
            msg += "\n\nAsk me anything about your parish finances."
            self._add_message("bot", msg)
        except Exception:
            self._add_message(
                "bot",
                "Hello! Ask me anything about your church finances."
            )

    def _quick_ask(self, question):
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, question)
        self._send()

    def _send(self):
        message = self.input_entry.get().strip()
        if not message:
            return
        if not self.api_key:
            self._add_message(
                "bot",
                "Please enter your Groq API key first."
            )
            return

        self.input_entry.delete(0, "end")
        self.send_btn.configure(state="disabled", text="...")
        self._add_message("user", message)
        self._add_typing_indicator()

        def worker():
            try:
                context  = get_church_context(self.db, self.ai)
                system   = SYSTEM_PROMPT + "\n" + context
                response = call_groq(
                    self.api_key, system,
                    self.history, message
                )
                self.history.append({
                    "role": "user", "content": message
                })
                self.history.append({
                    "role": "assistant", "content": response
                })
                self.after(
                    0, lambda: self._on_response(response)
                )
            except Exception as e:
                self.after(
                    0,
                    lambda: self._on_response(
                        "Error: " + str(e)
                    )
                )

        threading.Thread(target=worker, daemon=True).start()

    def _on_response(self, response):
        self._remove_typing_indicator()
        self._add_message("bot", response)
        self.send_btn.configure(state="normal", text="Send")

    def _add_message(self, role, text):
        is_user = role == "user"
        outer   = ctk.CTkFrame(
            self.chat_frame, fg_color="transparent"
        )
        outer.pack(fill="x", padx=12, pady=4)

        bubble = ctk.CTkFrame(
            outer,
            fg_color=THEME["primary"] if is_user
            else THEME["bg_card"],
            corner_radius=12,
            border_width=0 if is_user else 1,
            border_color=THEME["border"]
        )
        bubble.pack(
            side="right" if is_user else "left",
            anchor="e" if is_user else "w"
        )

        ctk.CTkLabel(
            bubble, text=text,
            font=("Arial", 12),
            text_color="#FFFFFF" if is_user
            else THEME["text_main"],
            wraplength=360,
            justify="left"
        ).pack(padx=14, pady=10)

        self.after(
            100,
            lambda: self.chat_frame._parent_canvas
            .yview_moveto(1)
        )

    def _add_typing_indicator(self):
        self.typing_frame = ctk.CTkFrame(
            self.chat_frame, fg_color="transparent"
        )
        self.typing_frame.pack(
            fill="x", padx=12, pady=4, anchor="w"
        )
        ctk.CTkLabel(
            self.typing_frame,
            text="ChurchTrack AI is thinking...",
            font=("Arial", 11),
            text_color=THEME["text_sub"]
        ).pack(side="left", pady=6)

    def _remove_typing_indicator(self):
        try:
            self.typing_frame.destroy()
        except Exception:
            pass

    def _clear_chat(self):
        for w in self.chat_frame.winfo_children():
            w.destroy()
        self.history = []
        if self.api_key:
            self._welcome_message()


# ─────────────────────────────────────────
# FLOATING BUTTON
# ─────────────────────────────────────────

class ChatbotButton(ctk.CTkButton):

    def __init__(self, master, db_manager, ai_engine, **kwargs):
        super().__init__(
            master,
            text="💬  Ask AI",
            font=("Arial", 12, "bold"),
            height=38,
            corner_radius=20,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._open,
            **kwargs
        )
        self.db      = db_manager
        self.ai      = ai_engine
        self._window = None

    def _open(self):
        if self._window and self._window.winfo_exists():
            self._window.focus()
            return
        self._window = ChatbotWindow(
            self.winfo_toplevel(), self.db, self.ai
        )


# ─────────────────────────────────────────
# SIDEBAR SCREEN
# ─────────────────────────────────────────

class ChatbotScreen(ctk.CTkFrame):

    def __init__(self, master, db_manager, ai_engine,
                 on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db          = db_manager
        self.ai          = ai_engine
        self.on_navigate = on_navigate
        self.on_logout   = on_logout
        self.history     = []
        self.api_key     = load_api_key()
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        from ui.components import (
            build_sidebar, build_topbar, ADMIN_NAV
        )
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "AI Assistant", self.on_logout, self.on_navigate
        )
        for item, btn in self.nav_btns.items():
            btn.configure(
                command=lambda i=item: self.on_navigate(i)
            )

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)
        build_topbar(right, "Admin", self.db)

        # Chat header
        chat_header = ctk.CTkFrame(
            right, fg_color=THEME["bg_card"],
            corner_radius=0, border_width=1,
            border_color=THEME["border"]
        )
        chat_header.pack(fill="x")

        ctk.CTkLabel(
            chat_header,
            text="⛪  ChurchTrack AI Assistant",
            font=("Arial", 16, "bold"),
            text_color=THEME["text_main"]
        ).pack(side="left", padx=20, pady=14)

        ctk.CTkLabel(
            chat_header,
            text="Free — Groq + Llama 3.3",
            font=("Arial", 10),
            text_color=THEME["text_sub"]
        ).pack(side="left", padx=(0, 16))

        ctk.CTkButton(
            chat_header, text="Clear Chat",
            font=("Arial", 11), width=90, height=30,
            corner_radius=6,
            fg_color=THEME["bg_main"],
            text_color=THEME["text_main"],
            border_width=1,
            border_color=THEME["border"],
            hover_color="#E8EDF5",
            command=self._clear_chat
        ).pack(side="right", padx=16)

        # API key banner
        self.api_banner = ctk.CTkFrame(
            right, fg_color="#FFF9C4",
            corner_radius=0, border_width=1,
            border_color="#FFC107"
        )

        api_inner = ctk.CTkFrame(
            self.api_banner, fg_color="transparent"
        )
        api_inner.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(
            api_inner,
            text="Enter your FREE Groq API Key:",
            font=("Arial", 12, "bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        self.api_entry = ctk.CTkEntry(
            api_inner,
            placeholder_text="gsk_...",
            show="•", width=280, height=34,
            corner_radius=8,
            border_color=THEME["border"],
            fg_color="#FFFFFF",
            text_color=THEME["text_main"]
        )
        self.api_entry.pack(side="left", padx=(10, 8))

        ctk.CTkButton(
            api_inner, text="Activate",
            font=("Arial", 12, "bold"),
            width=80, height=34,
            corner_radius=8,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._save_api_key
        ).pack(side="left")

        ctk.CTkLabel(
            api_inner,
            text="  Get free key at console.groq.com",
            font=("Arial", 10),
            text_color=THEME["text_sub"]
        ).pack(side="left")

        # Suggested questions
        sugg_frame = ctk.CTkFrame(
            right, fg_color=THEME["bg_main"]
        )
        sugg_frame.pack(fill="x", padx=16, pady=(8, 0))

        for s in [
            "What is our current balance?",
            "How are collections trending?",
            "Any financial warnings?",
            "Summarize this month",
            "Should we approve a P50,000 expense?",
        ]:
            ctk.CTkButton(
                sugg_frame, text=s,
                font=("Arial", 10), height=28,
                corner_radius=20,
                fg_color=THEME["bg_card"],
                text_color=THEME["text_main"],
                border_width=1,
                border_color=THEME["border"],
                hover_color="#E8EDF5",
                command=lambda q=s: self._quick_ask(q)
            ).pack(side="left", padx=3, pady=4)

        # Chat messages
        self.chat_frame = ctk.CTkScrollableFrame(
            right, fg_color=THEME["bg_main"]
        )
        self.chat_frame.pack(fill="both", expand=True)

        # Input bar
        input_bar = ctk.CTkFrame(
            right, fg_color=THEME["bg_card"],
            corner_radius=0, border_width=1,
            border_color=THEME["border"]
        )
        input_bar.pack(fill="x")

        self.input_entry = ctk.CTkEntry(
            input_bar,
            placeholder_text="Ask about your church finances...",
            height=48, corner_radius=12,
            border_color=THEME["border"],
            fg_color="#FAFAFA",
            text_color=THEME["text_main"],
            font=("Arial", 13)
        )
        self.input_entry.pack(
            side="left", fill="x", expand=True,
            padx=(16, 8), pady=12
        )
        self.input_entry.bind("<Return>", lambda e: self._send())

        self.send_btn = ctk.CTkButton(
            input_bar, text="Send",
            font=("Arial", 13, "bold"),
            width=80, height=48,
            corner_radius=12,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_dark"],
            command=self._send
        )
        self.send_btn.pack(
            side="right", padx=(0, 16), pady=12
        )

        # Show banner or welcome
        if self.api_key:
            self.api_banner.pack_forget()
            self._welcome_message()
        else:
            self.api_banner.pack(fill="x")
            self._add_message(
                "bot",
                "Welcome to ChurchTrack AI Assistant!\n\n"
                "To activate, enter your FREE Groq API key "
                "in the yellow bar above.\n\n"
                "Get your free key at console.groq.com — "
                "sign up takes 2 minutes and the key is "
                "completely free with generous limits."
            )

    def _save_api_key(self):
        key = self.api_entry.get().strip()
        if not key.startswith("gsk_"):
            self._add_message(
                "bot",
                "Invalid key format. "
                "Groq keys start with gsk_..."
            )
            return
        if save_api_key(key):
            self.api_key = key
            self.api_banner.pack_forget()
            self._clear_chat()
            self._welcome_message()
        else:
            self._add_message(
                "bot",
                "Could not save key. Please try again."
            )

    def _welcome_message(self):
        try:
            health = self.ai.check_financial_health()
            msg = (
                "Hello! I am your ChurchTrack AI Assistant "
                "powered by Groq + Llama 3.3 — completely free.\n\n"
                "Current Net Balance: P{:,.0f}\n".format(
                    health["net_balance"]
                )
            )
            if health["warnings"]:
                msg += "\nWarning: " + \
                       health["warnings"][0]["message"]
            else:
                msg += "Finances are looking healthy."
            msg += (
                "\n\nAsk me anything — donation trends, "
                "expense approvals, forecasts, "
                "or financial summaries."
            )
            self._add_message("bot", msg)
        except Exception:
            self._add_message(
                "bot",
                "Hello! Ask me anything about your "
                "church finances."
            )

    def _quick_ask(self, question):
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, question)
        self._send()

    def _send(self):
        message = self.input_entry.get().strip()
        if not message:
            return
        if not self.api_key:
            self._add_message(
                "bot",
                "Please enter your Groq API key first."
            )
            return

        self.input_entry.delete(0, "end")
        self.send_btn.configure(state="disabled", text="...")
        self._add_message("user", message)
        self._add_typing_indicator()

        def worker():
            try:
                context  = get_church_context(self.db, self.ai)
                system   = SYSTEM_PROMPT + "\n" + context
                response = call_groq(
                    self.api_key, system,
                    self.history, message
                )
                self.history.append({
                    "role": "user", "content": message
                })
                self.history.append({
                    "role": "assistant", "content": response
                })
                self.after(
                    0, lambda: self._on_response(response)
                )
            except Exception as e:
                err = str(e)
                if "401" in err or "invalid" in err.lower():
                    err = (
                        "Invalid API key. Please check your "
                        "Groq key at console.groq.com"
                    )
                elif "rate" in err.lower():
                    err = (
                        "Rate limit reached. "
                        "Please wait a moment and try again."
                    )
                self.after(
                    0, lambda: self._on_response(err)
                )

        threading.Thread(target=worker, daemon=True).start()

    def _on_response(self, response):
        self._remove_typing_indicator()
        self._add_message("bot", response)
        self.send_btn.configure(state="normal", text="Send")

    def _add_message(self, role, text):
        is_user = role == "user"
        outer   = ctk.CTkFrame(
            self.chat_frame, fg_color="transparent"
        )
        outer.pack(fill="x", padx=16, pady=4)

        bubble = ctk.CTkFrame(
            outer,
            fg_color=THEME["primary"] if is_user
            else THEME["bg_card"],
            corner_radius=12,
            border_width=0 if is_user else 1,
            border_color=THEME["border"]
        )
        bubble.pack(
            side="right" if is_user else "left",
            anchor="e" if is_user else "w"
        )

        ctk.CTkLabel(
            bubble, text=text,
            font=("Arial", 12),
            text_color="#FFFFFF" if is_user
            else THEME["text_main"],
            wraplength=700,
            justify="left"
        ).pack(padx=16, pady=10)

        self.after(
            100,
            lambda: self.chat_frame._parent_canvas
            .yview_moveto(1)
        )

    def _add_typing_indicator(self):
        self.typing_frame = ctk.CTkFrame(
            self.chat_frame, fg_color="transparent"
        )
        self.typing_frame.pack(
            fill="x", padx=16, pady=4, anchor="w"
        )
        ctk.CTkLabel(
            self.typing_frame,
            text="ChurchTrack AI is thinking...",
            font=("Arial", 12),
            text_color=THEME["text_sub"]
        ).pack(side="left", pady=8)

    def _remove_typing_indicator(self):
        try:
            self.typing_frame.destroy()
        except Exception:
            pass

    def _clear_chat(self):
        for w in self.chat_frame.winfo_children():
            w.destroy()
        self.history = []
        if self.api_key:
            self._welcome_message()
