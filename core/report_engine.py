import datetime
import os
import re

from fpdf import FPDF


class ReportEngine:

    def __init__(self, db_manager):
        self.db = db_manager

    def generate_summary_report(
        self,
        start_date: str,
        end_date: str,
        parish_name: str = "St. Joseph Parish",
        generated_by: str = "ChurchTrack",
        generated_role: str = "System",
        filters: str = "",
    ) -> str:
        return self.generate_custom_report(
            "Financial Summary",
            start_date,
            end_date,
            parish_name,
            generated_by,
            generated_role,
            filters or "Report Type: Financial Summary",
        )

    def generate_detailed_report(
        self,
        start_date: str,
        end_date: str,
        parish_name: str = "St. Joseph Parish",
        generated_by: str = "ChurchTrack",
        generated_role: str = "System",
        filters: str = "",
    ) -> str:
        return self.generate_custom_report(
            "Donation Report",
            start_date,
            end_date,
            parish_name,
            generated_by,
            generated_role,
            filters or "Report Type: Donation Report",
        )

    def generate_custom_report(
        self,
        report_type: str,
        start_date: str = None,
        end_date: str = None,
        parish_name: str = "St. Joseph Parish",
        generated_by: str = "admin",
        generated_role: str = "admin",
        filters: str = "",
    ) -> str:
        orientation = "L" if report_type in (
            "Expense Report",
            "Event Report",
            "Audit Report",
            "Staff Activity Report",
        ) else "P"
        pdf = ChurchPDF(
            parish_name=parish_name,
            report_type=report_type,
            generated_by=generated_by,
            generated_role=generated_role,
            orientation=orientation,
            unit="mm",
            format="A4",
        )
        pdf.set_auto_page_break(auto=True, margin=14)
        pdf.add_page()

        usable_width = pdf.w - 20
        self._title(pdf, report_type, start_date, end_date)
        self._metadata(pdf, generated_by, generated_role, filters)

        if report_type == "Financial Summary":
            self._financial_summary(pdf, start_date, end_date, usable_width)
        elif report_type == "Donation Report":
            rows = self.db.get_filtered_donations(start_date, end_date)
            self._records_table(
                pdf,
                ["Date", "Donor Entry", "Category", "Amount", "Notes"],
                [26, 48, 42, 28, 46],
                [
                    [r[0], r[1] or "Anonymous", r[2], self._money(r[3]), r[4] or ""]
                    for r in rows
                ],
            )
        elif report_type == "Expense Report":
            rows = self.db.get_expenses_filtered(start_date, end_date)
            self._records_table(
                pdf,
                ["ID", "Date", "Category", "Amount", "Description", "Status", "Submitted", "Approved"],
                [14, 24, 36, 26, 70, 26, 34, 34],
                [
                    [r[0], r[1], r[2], self._money(r[3]), r[4], r[5], r[6] or "", r[7] or ""]
                    for r in rows
                ],
            )
        elif report_type == "Event Report":
            rows = self.db.get_events_filtered(start_date, end_date)
            self._records_table(
                pdf,
                ["ID", "Date", "Time", "Event", "Location", "Description", "Status"],
                [14, 26, 20, 52, 48, 76, 26],
                [
                    [r[0], r[2], r[3], r[1], r[5] or "", r[6] or "", r[9] or ""]
                    for r in rows
                ],
            )
        elif report_type == "Audit Report":
            rows = self.db.get_audit_trail(start_date, end_date, limit=500)
            self._records_table(
                pdf,
                ["ID", "User", "Action", "Timestamp", "Details"],
                [18, 36, 56, 48, 104],
                [[r[0], r[1], r[2], str(r[3]).replace("T", " ")[:19], r[4] or ""] for r in rows],
            )
        elif report_type == "Staff Activity Report":
            rows = self.db.get_staff_activity(start_date=start_date, end_date=end_date, limit=500)
            self._records_table(
                pdf,
                ["ID", "Staff", "Action", "Affected Record", "Date/Time", "Status"],
                [16, 42, 56, 72, 48, 28],
                [[r[0], r[1], r[2], r[3] or "", str(r[4]).replace("T", " ")[:19], r[5]] for r in rows],
            )
        else:
            self._paragraph(pdf, "No report template found for this report type.")

        filename = self._save_path(report_type, start_date, end_date)
        pdf.output(filename)
        return filename

    def _title(self, pdf, report_type, start_date, end_date):
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(0, 8, self._clean(report_type), ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(95, 105, 122)
        period = "{} to {}".format(start_date or "All records", end_date or "All records")
        pdf.cell(0, 6, self._clean("Period: " + period), ln=True, align="C")
        pdf.ln(5)

    def _metadata(self, pdf, generated_by, generated_role, filters):
        pdf.set_fill_color(245, 247, 251)
        pdf.set_text_color(35, 45, 63)
        pdf.set_font("Helvetica", "", 9)
        generated_at = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
        lines = [
            "Generated by: {} ({})".format(generated_by, generated_role),
            "Generated at: {}".format(generated_at),
            "Filters used: {}".format(filters or "None"),
        ]
        for line in lines:
            pdf.cell(0, 6, self._clean(line), ln=True, fill=True)
        pdf.ln(5)

    def _financial_summary(self, pdf, start_date, end_date, usable_width):
        query_start = start_date or "0001-01-01"
        query_end = end_date or "9999-12-31"
        income_summary = self.db.get_summary_by_range(query_start, query_end)
        expense_summary = self.db.get_expense_summary_by_range(query_start, query_end)
        income_total = sum(row[1] for row in income_summary)
        expense_total = sum(row[1] for row in expense_summary)
        net = income_total - expense_total

        self._section_header(pdf, "Financial Totals")
        self._records_table(
            pdf,
            ["Metric", "Amount"],
            [usable_width - 50, 50],
            [
                ["Total Donations", self._money(income_total)],
                ["Approved Expenses", self._money(expense_total)],
                ["Net Balance", self._money(net)],
            ],
        )
        pdf.ln(4)

        self._section_header(pdf, "Donation Categories")
        self._records_table(
            pdf,
            ["Category", "Total"],
            [usable_width - 50, 50],
            [[row[0], self._money(row[1])] for row in income_summary],
        )
        pdf.ln(4)

        self._section_header(pdf, "Expense Categories")
        self._records_table(
            pdf,
            ["Category", "Total"],
            [usable_width - 50, 50],
            [[row[0], self._money(row[1])] for row in expense_summary],
        )

    def _records_table(self, pdf, headers, widths, rows):
        if not rows:
            self._paragraph(pdf, "No records found for the selected filters.")
            return

        self._table_header(pdf, headers, widths)
        pdf.set_font("Helvetica", "", 8)
        fill = False
        for row in rows:
            if pdf.get_y() > pdf.h - 24:
                pdf.add_page()
                self._table_header(pdf, headers, widths)
                pdf.set_font("Helvetica", "", 8)
            pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(35, 45, 63)
            for index, (value, width) in enumerate(zip(row, widths)):
                text = self._clean(value)
                align = "R" if "P " in text and index > 0 else "L"
                pdf.cell(width, 6, text[: max(8, int(width * 0.62))], border=0, fill=True, align=align)
            pdf.ln()
            fill = not fill

    def _table_header(self, pdf, headers, widths):
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(232, 240, 255)
        pdf.set_text_color(30, 42, 58)
        for header, width in zip(headers, widths):
            pdf.cell(width, 7, self._clean(header), border=0, fill=True)
        pdf.ln()

    def _section_header(self, pdf, text):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 42, 58)
        pdf.cell(0, 7, self._clean(text), ln=True)
        pdf.set_draw_color(37, 99, 235)
        pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
        pdf.ln(3)

    def _paragraph(self, pdf, text):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(95, 105, 122)
        pdf.multi_cell(0, 6, self._clean(text))
        pdf.ln(3)

    def _money(self, value):
        try:
            value = float(value or 0)
        except (TypeError, ValueError):
            value = 0
        return "P {:,.2f}".format(value)

    def _clean(self, value):
        text = "" if value is None else str(value)
        text = text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text.encode("latin-1", "ignore").decode("latin-1")

    def _save_path(self, report_type, start_date, end_date):
        os.makedirs("reports", exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "_", report_type.lower()).strip("_")
        start = start_date or "all"
        end = end_date or "all"
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return "reports/churchtrack_{}_{}_to_{}_{}.pdf".format(
            slug, start, end, stamp
        )


class ChurchPDF(FPDF):

    def __init__(self, parish_name="St. Joseph Parish",
                 report_type="Report", generated_by="ChurchTrack",
                 generated_role="System", **kwargs):
        super().__init__(**kwargs)
        self.parish_name = parish_name
        self.report_type = report_type
        self.generated_by = generated_by
        self.generated_role = generated_role

    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 42, 58)
        self.cell(0, 8, self._clean(self.parish_name), ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 110, 128)
        self.cell(0, 5, self._clean("Official ChurchTrack Report"), ln=True, align="C")
        self.set_draw_color(37, 99, 235)
        self.set_line_width(0.6)
        self.line(10, self.get_y() + 1, self.w - 10, self.get_y() + 1)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 140, 155)
        generated = "Generated by {} ({}) on {}".format(
            self.generated_by,
            self.generated_role,
            datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        )
        self.cell(0, 5, self._clean(generated), align="C", ln=True)
        self.cell(0, 5, "Page " + str(self.page_no()), align="C")

    def _clean(self, value):
        return str(value).encode("latin-1", "ignore").decode("latin-1")
