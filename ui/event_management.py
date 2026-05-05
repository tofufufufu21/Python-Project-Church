import calendar
import datetime
from collections import defaultdict

import customtkinter as ctk

from ui.theme import THEME, font, input_style, primary_button_style, secondary_button_style
from ui.components import (
    ADMIN_NAV,
    DatePickerEntry,
    build_screen_topbar,
    build_sidebar,
    create_labeled_entry,
    create_labeled_option,
    create_metric_card,
    create_status_badge,
    format_currency,
    get_date_range,
)


MONTHS = [datetime.date(2000, month, 1).strftime("%B") for month in range(1, 13)]
EVENT_FILTERS = [
    "All Events",
    "Specific Date",
    "By Month",
    "This Week",
    "This Month",
    "Upcoming",
    "Past",
    "Custom Range",
]
EVENT_COLORS = ["Blue", "Green", "Purple", "Orange", "Teal", "Gold"]


class EventManagement(ctk.CTkFrame):

    def __init__(self, master, db_manager, on_navigate, on_logout):
        super().__init__(master, fg_color=THEME["bg_main"])
        self.db = db_manager
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        today = datetime.date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.filter_mode = ctk.StringVar(value="Upcoming")
        self.month_var = ctk.StringVar(value=today.strftime("%B"))
        self.search_var = ctk.StringVar(value="")
        self.pack(fill="both", expand=True)
        self._build()
        self._refresh()

    def _build(self):
        self.sidebar, self.nav_btns = build_sidebar(
            self, ADMIN_NAV, "Event Management", self.on_logout, self.on_navigate
        )

        right = ctk.CTkFrame(self, fg_color=THEME["bg_main"])
        right.pack(side="right", fill="both", expand=True)

        build_screen_topbar(
            right,
            "Event Management",
            "Plan events with dates, times, locations, and practical filters.",
            db_manager=self.db,
            role="Admin",
            show_search=True,
            search_placeholder="Search events...",
        )

        self.content = ctk.CTkScrollableFrame(right, fg_color=THEME["bg_main"])
        self.content.pack(fill="both", expand=True, padx=24, pady=20)

        self._build_filter_card()

        self.stats_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 16))

        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.pack(fill="x", pady=(0, 16))
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)

        self.calendar_card = self._card(body)
        self.calendar_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.records_card = self._card(body)
        self.records_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    def _card(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_card"],
            corner_radius=THEME["radius_lg"],
            border_width=1,
            border_color=THEME["border"],
        )

    def _build_filter_card(self):
        card = self._card(self.content)
        card.pack(fill="x", pady=(0, 16))

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            header,
            text="Event Filters",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(side="left")
        ctk.CTkButton(
            header,
            text="Create Event",
            height=36,
            font=font(12, "bold"),
            command=self._open_event_modal,
            **primary_button_style(THEME["radius_md"]),
        ).pack(side="right")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))
        for col in range(6):
            row.grid_columnconfigure(col, weight=1, uniform="event_filter")

        create_labeled_option(
            row,
            "Filter",
            EVENT_FILTERS,
            variable=self.filter_mode,
            command=lambda _v: self._refresh(),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        create_labeled_option(
            row,
            "Month",
            MONTHS,
            variable=self.month_var,
            command=lambda _v: self._refresh(),
        ).grid(row=0, column=1, sticky="ew", padx=8)

        specific_col = ctk.CTkFrame(row, fg_color="transparent")
        specific_col.grid(row=0, column=2, sticky="ew", padx=8)
        ctk.CTkLabel(
            specific_col,
            text="Specific / From",
            font=font(11, "bold"),
            text_color=THEME["text_sub"],
        ).pack(anchor="w", pady=(0, 4))
        self.from_date = DatePickerEntry(specific_col)
        self.from_date.pack(fill="x")

        to_col = ctk.CTkFrame(row, fg_color="transparent")
        to_col.grid(row=0, column=3, sticky="ew", padx=8)
        ctk.CTkLabel(
            to_col,
            text="To Date",
            font=font(11, "bold"),
            text_color=THEME["text_sub"],
        ).pack(anchor="w", pady=(0, 4))
        self.to_date = DatePickerEntry(to_col)
        self.to_date.pack(fill="x")

        search = create_labeled_entry(row, "Search", "Event, location, description")
        search.grid(row=0, column=4, sticky="ew", padx=8)
        self.search_entry = search.entry
        self.search_entry.bind("<Return>", lambda _event: self._refresh())

        ctk.CTkButton(
            row,
            text="Apply",
            height=THEME["control_h"],
            font=font(12, "bold"),
            command=self._refresh,
            **secondary_button_style(THEME["radius_md"]),
        ).grid(row=0, column=5, sticky="ew", padx=(8, 0), pady=(23, 0))

    def _range(self):
        mode = self.filter_mode.get()
        if mode == "All Events":
            return None, None, None
        if mode == "Upcoming":
            return None, None, "Upcoming"
        if mode == "Past":
            return None, None, "Past"
        if mode == "Specific Date":
            start, end = get_date_range(
                "Specific Date",
                specific_date=self.from_date.get(),
            )
            return start, end, None
        start, end = get_date_range(
            mode,
            from_date=self.from_date.get(),
            to_date=self.to_date.get(),
            month_name=self.month_var.get(),
        )
        return start, end, None

    def _refresh(self):
        if not hasattr(self, "stats_frame"):
            return
        for frame in (self.stats_frame, self.calendar_card, self.records_card):
            for child in frame.winfo_children():
                child.destroy()
        start, end, timing = self._range()
        rows = self.db.get_events_filtered(
            start_date=start,
            end_date=end,
            timing=timing,
            search=self.search_entry.get().strip() if hasattr(self, "search_entry") else "",
        )
        self._render_stats(rows)
        self._render_calendar()
        self._render_records(rows, start, end, timing)

    def _render_stats(self, filtered_rows):
        today = datetime.date.today().isoformat()
        all_rows = self.db.get_events_filtered()
        upcoming = [row for row in all_rows if str(row[2]) >= today]
        past = [row for row in all_rows if str(row[2]) < today]
        this_month_start = datetime.date.today().replace(day=1).isoformat()
        this_month_end = self._month_end(datetime.date.today().year, datetime.date.today().month).isoformat()
        this_month = [
            row for row in all_rows
            if this_month_start <= str(row[2]) <= this_month_end
        ]

        for col in range(4):
            self.stats_frame.grid_columnconfigure(col, weight=1, uniform="event_stat")
        cards = [
            ("Filtered Events", len(filtered_rows), "Current result set", "FT", THEME["primary"]),
            ("Upcoming", len(upcoming), "Events from today", "UP", THEME["success"]),
            ("Past", len(past), "Completed by date", "PA", THEME["text_sub"]),
            ("This Month", len(this_month), datetime.date.today().strftime("%B"), "MO", THEME["warning"]),
        ]
        for col, data in enumerate(cards):
            card = create_metric_card(
                self.stats_frame,
                data[0],
                data[1],
                data[2],
                icon=data[3],
                accent=data[4],
            )
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0 if col == 3 else 8))

    def _render_calendar(self):
        header = ctk.CTkFrame(self.calendar_card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkButton(
            header,
            text="<",
            width=34,
            height=34,
            font=font(14, "bold"),
            command=self._prev_month,
            **secondary_button_style(THEME["radius_sm"]),
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=datetime.date(self.current_year, self.current_month, 1).strftime("%B %Y"),
            font=font(17, "bold"),
            text_color=THEME["text_main"],
        ).pack(side="left", padx=12)
        ctk.CTkButton(
            header,
            text=">",
            width=34,
            height=34,
            font=font(14, "bold"),
            command=self._next_month,
            **secondary_button_style(THEME["radius_sm"]),
        ).pack(side="right")

        month_start = datetime.date(self.current_year, self.current_month, 1)
        month_end = self._month_end(self.current_year, self.current_month)
        month_events = self.db.get_events_filtered(
            start_date=month_start.isoformat(),
            end_date=month_end.isoformat(),
        )
        event_days = defaultdict(list)
        for row in month_events:
            try:
                day = int(str(row[2]).split("-")[2])
                event_days[day].append(row)
            except Exception:
                pass

        grid = ctk.CTkFrame(self.calendar_card, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=(4, 16))
        for col, name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
            grid.grid_columnconfigure(col, weight=1, uniform="day")
            ctk.CTkLabel(
                grid,
                text=name,
                font=font(10, "bold"),
                text_color=THEME["text_sub"],
            ).grid(row=0, column=col, sticky="ew", pady=(0, 6))

        today = datetime.date.today()
        for week_index, week in enumerate(calendar.monthcalendar(self.current_year, self.current_month), start=1):
            for day_index, day in enumerate(week):
                if day == 0:
                    cell = ctk.CTkFrame(grid, fg_color="transparent", height=48)
                    cell.grid(row=week_index, column=day_index, padx=3, pady=3, sticky="nsew")
                    continue
                date_value = datetime.date(self.current_year, self.current_month, day)
                has_event = day in event_days
                is_today = date_value == today
                bg = THEME["primary"] if is_today else THEME["primary_soft"] if has_event else THEME["bg_panel"]
                fg = THEME["text_on_primary"] if is_today else THEME["primary"] if has_event else THEME["text_main"]
                cell = ctk.CTkButton(
                    grid,
                    text=str(day),
                    height=48,
                    fg_color=bg,
                    hover_color=THEME["bg_card_hover"],
                    text_color=fg,
                    border_width=1,
                    border_color=THEME["border"],
                    corner_radius=THEME["radius_sm"],
                    font=font(12, "bold"),
                    command=lambda dt=date_value: self._filter_specific_date(dt),
                )
                cell.grid(row=week_index, column=day_index, padx=3, pady=3, sticky="nsew")

    def _render_records(self, rows, start, end, timing):
        header = ctk.CTkFrame(self.records_card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkLabel(
            header,
            text="Event Records",
            font=font(15, "bold"),
            text_color=THEME["text_main"],
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="{} to {}".format(start or timing or "All", end or ""),
            font=font(11),
            text_color=THEME["text_sub"],
        ).pack(side="right")

        self._table_header(
            self.records_card,
            ["Date", "Time", "Event Name", "Location", "Status", ""],
            [1, 1, 2, 2, 1, 1],
        )
        if not rows:
            self._empty(self.records_card, "No events match the selected filter.")
            return
        scroll = ctk.CTkScrollableFrame(self.records_card, fg_color="transparent", height=360)
        scroll.pack(fill="both", expand=True, padx=1, pady=(0, 12))
        for idx, row in enumerate(rows):
            self._event_row(scroll, row, idx)

    def _open_event_modal(self, event_id=None):
        row = self.db.get_event_by_id(event_id) if event_id else None
        modal = ctk.CTkToplevel(self)
        modal.title("Edit Event" if row else "Create Event")
        modal.geometry("620x680")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])

        ctk.CTkLabel(
            modal,
            text="Edit Event" if row else "Create Event",
            font=font(18, "bold"),
            text_color=THEME["text_main"],
        ).pack(anchor="w", padx=24, pady=(22, 12))

        body = ctk.CTkScrollableFrame(modal, fg_color=THEME["bg_card"])
        body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        defaults = {
            "name": row[1] if row else "",
            "date": row[2] if row else datetime.date.today().isoformat(),
            "time": row[3] if row else "09:00",
            "end": row[4] if row and row[4] else "",
            "location": row[5] if row else "",
            "description": row[6] if row else "",
            "organizer": row[7] if row else "",
            "attendees": row[8] if row else "",
            "status": row[9] if row else "Upcoming",
            "recurring": row[10] if row else 0,
            "color": row[11] if row else "Blue",
        }

        name_wrap = create_labeled_entry(body, "Event Name", "Event name", defaults["name"])
        name_wrap.pack(fill="x", pady=(0, 10))
        name_entry = name_wrap.entry

        date_row = ctk.CTkFrame(body, fg_color="transparent")
        date_row.pack(fill="x", pady=(0, 10))
        date_row.grid_columnconfigure(0, weight=1)
        date_row.grid_columnconfigure(1, weight=1)

        start_col = ctk.CTkFrame(date_row, fg_color="transparent")
        start_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(start_col, text="Date", font=font(11, "bold"), text_color=THEME["text_sub"]).pack(anchor="w", pady=(0, 4))
        date_entry = DatePickerEntry(start_col, initial_date=defaults["date"])
        date_entry.pack(fill="x")

        time_wrap = create_labeled_entry(date_row, "Time", "HH:MM", defaults["time"])
        time_wrap.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        time_entry = time_wrap.entry

        location_wrap = create_labeled_entry(body, "Location", "Location", defaults["location"])
        location_wrap.pack(fill="x", pady=(0, 10))
        location_entry = location_wrap.entry

        desc_wrap = create_labeled_entry(body, "Description", "Description or notes", defaults["description"])
        desc_wrap.pack(fill="x", pady=(0, 10))
        desc_entry = desc_wrap.entry

        organizer_wrap = create_labeled_entry(body, "Organizer", "Organizer", defaults["organizer"])
        organizer_wrap.pack(fill="x", pady=(0, 10))
        organizer_entry = organizer_wrap.entry


        color_var = ctk.StringVar(value=defaults["color"] or "Blue")
        create_labeled_option(
            body,
            "Color",
            EVENT_COLORS,
            variable=color_var,
        ).pack(fill="x", pady=(0, 10))

        recurring_var = ctk.IntVar(value=int(defaults["recurring"] or 0))
        ctk.CTkCheckBox(
            body,
            text="Recurring annually",
            variable=recurring_var,
            onvalue=1,
            offvalue=0,
            text_color=THEME["text_main"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=font(12),
        ).pack(anchor="w", pady=(4, 12))

        status_label = ctk.CTkLabel(body, text="", font=font(11), text_color=THEME["danger"])
        status_label.pack(anchor="w", pady=(0, 8))

        def save():
            name = name_entry.get().strip()
            date_value = date_entry.get().strip()
            time_value = time_entry.get().strip()
            if not name:
                status_label.configure(text="Event name is required.")
                return
            try:
                datetime.datetime.strptime(date_value, "%Y-%m-%d")
                datetime.datetime.strptime(time_value, "%H:%M")
            except ValueError:
                status_label.configure(text="Use YYYY-MM-DD and 24-hour HH:MM time.")
                return

            if row:
                self.db.update_event(
                    event_id,
                    name,
                    date_value,
                    time_value,
                    location=location_entry.get().strip(),
                    description=desc_entry.get().strip(),
                    organizer=organizer_entry.get().strip(),
                    status="Upcoming",
                    recurring=recurring_var.get(),
                    color=color_var.get(),
                )
                self.db.log_action("admin", "UPDATE_EVENT", "Event ID {}".format(event_id))
            else:
                new_id = self.db.save_event(
                    name,
                    date_value,
                    time_value,
                    location=location_entry.get().strip(),
                    description=desc_entry.get().strip(),
                    organizer=organizer_entry.get().strip(),
                    status="Upcoming",
                    recurring=recurring_var.get(),
                    color=color_var.get(),
                )
                self.db.log_action("admin", "CREATE_EVENT", "Event ID {}".format(new_id))
            modal.destroy()
            self._refresh()

        ctk.CTkButton(
            body,
            text="Save Event",
            height=46,
            font=font(13, "bold"),
            command=save,
            **primary_button_style(THEME["radius_md"]),
        ).pack(fill="x", pady=(4, 10))

    def _delete_event(self, event_id):
        modal = ctk.CTkToplevel(self)
        modal.title("Delete Event")
        modal.geometry("360x190")
        modal.grab_set()
        modal.configure(fg_color=THEME["bg_card"])
        ctk.CTkLabel(
            modal,
            text="Delete this event?",
            font=font(16, "bold"),
            text_color=THEME["text_main"],
        ).pack(pady=(28, 8))
        ctk.CTkLabel(
            modal,
            text="This removes the event record from the calendar.",
            font=font(11),
            text_color=THEME["text_sub"],
        ).pack()
        row = ctk.CTkFrame(modal, fg_color="transparent")
        row.pack(pady=22)
        ctk.CTkButton(
            row,
            text="Cancel",
            width=100,
            command=modal.destroy,
            **secondary_button_style(THEME["radius_md"]),
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            row,
            text="Delete",
            width=100,
            fg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            text_color="#FFFFFF",
            corner_radius=THEME["radius_md"],
            command=lambda: self._do_delete(event_id, modal),
        ).pack(side="left", padx=6)

    def _do_delete(self, event_id, modal):
        self.db.delete_event(event_id)
        self.db.log_action("admin", "DELETE_EVENT", "Event ID {}".format(event_id))
        modal.destroy()
        self._refresh()

    def _filter_specific_date(self, date_value):
        self.filter_mode.set("Specific Date")
        self.from_date.set(date_value.isoformat())
        self._refresh()

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._refresh()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._refresh()

    def _month_end(self, year, month):
        return datetime.date(year, month, calendar.monthrange(year, month)[1])

    def _effective_status(self, date_value, status):
        if status == "Completed":
            return "Completed"
        try:
            event_date = datetime.datetime.strptime(str(date_value)[:10], "%Y-%m-%d").date()
            if event_date < datetime.date.today():
                return "Past"
        except Exception:
            pass
        return status or "Upcoming"

    def _table_header(self, parent, headers, weights):
        header = ctk.CTkFrame(parent, fg_color=THEME["table_header"])
        header.pack(fill="x", padx=1)

        minsizes = [100, 45, 100, 80, 70, 550]

        for col, (text, weight, min_w) in enumerate(zip(headers, weights, minsizes)):
            header.grid_columnconfigure(col, weight=weight, minsize=min_w)
            ctk.CTkLabel(
                header,
                text=text,
                font=font(11, "bold"),
                text_color=THEME["text_sub"],
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=6, pady=8)

    def _event_row(self, parent, row_data, idx):
        try:
            event_id = row_data[0]
            name = row_data[1] if len(row_data) > 1 else "Unnamed"
            start_date = row_data[2] if len(row_data) > 2 else ""
            event_time = row_data[3] if len(row_data) > 3 else "09:00"
            location = row_data[5] if len(row_data) > 5 else ""
            description = row_data[6] if len(row_data) > 6 else ""

            row = ctk.CTkFrame(
                parent,
                fg_color=THEME["input"] if idx % 2 == 0 else THEME["bg_card"],
            )
            row.pack(fill="x", padx=1)

            weights = [1, 1, 2, 2, 1]
            minsizes = [100, 45, 100, 80, 550]

            for col, (weight, min_w) in enumerate(zip(weights, minsizes)):
                row.grid_columnconfigure(col, weight=weight, minsize=min_w)

            clean_name = str(name)[:16] + "..." if len(str(name)) > 16 else str(name)
            raw_loc = str(location) if location else (str(description) if description else "-")
            clean_loc = raw_loc[:16] + "..." if len(raw_loc) > 16 else raw_loc

            values = [
                str(start_date) if start_date else "-",
                str(event_time) if event_time else "-",
                clean_name,
                clean_loc,
            ]

            for col, value in enumerate(values):
                ctk.CTkLabel(
                    row,
                    text=value,
                    font=font(11, "bold" if col in (1, 2) else "normal"),
                    text_color=THEME["primary"] if col == 1 else THEME["text_main"],
                    anchor="w",
                ).grid(row=0, column=col, sticky="ew", padx=6, pady=8)

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.grid(row=0, column=4, sticky="ew", padx=2, pady=6)

            ctk.CTkButton(
                actions,
                text="Edit",
                width=40,
                height=26,
                font=font(10, "bold"),
                command=lambda eid=event_id: self._open_event_modal(eid),
                **secondary_button_style(THEME["radius_sm"]),
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                actions,
                text="Del",
                width=40,
                height=26,
                font=font(10, "bold"),
                fg_color=THEME["danger_soft"],
                hover_color=THEME["danger"],
                text_color=THEME["danger"],
                border_width=1,
                border_color=THEME["danger_soft"],
                corner_radius=THEME["radius_sm"],
                command=lambda eid=event_id: self._delete_event(eid),
            ).pack(side="left")

        except Exception as e:
            print(f"Error loading row: {e}")

    def _empty(self, parent, message):
        ctk.CTkLabel(
            parent,
            text=message,
            font=font(12),
            text_color=THEME["text_sub"],
        ).pack(pady=24)
