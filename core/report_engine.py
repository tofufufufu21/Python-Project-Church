import os
import datetime
from fpdf import FPDF


class ReportEngine:

    def __init__(self, db_manager):
        self.db = db_manager

    def generate_summary_report(
        self, start_date: str, end_date: str,
        parish_name: str = "St. Joseph Parish"
    ) -> str:
        transactions  = self.db.get_transactions_by_range(
            start_date, end_date
        )
        income_summary  = self.db.get_summary_by_range(
            start_date, end_date
        )
        expense_summary = self.db.get_expense_summary_by_range(
            start_date, end_date
        )

        pdf = ChurchPDF(
            parish_name=parish_name,
            orientation="P", unit="mm", format="A4"
        )
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(79, 134, 247)
        pdf.cell(0, 8, "Financial Summary Report",
                 ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0, 6, "Period: " + start_date + " to " + end_date,
            ln=True, align="C"
        )
        pdf.ln(6)

        # Income summary
        self._section_header(pdf, "Revenue by Category", 200)
        col_w = [120, 60]
        self._table_header(pdf, ["Category", "Total Amount"], col_w)

        grand_income = 0
        fill = False
        pdf.set_font("Helvetica", "", 10)
        for cat, total in income_summary:
            grand_income += total
            pdf.set_fill_color(248, 249, 250) if fill \
                else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(col_w[0], 7, str(cat),
                     border=0, fill=True, align="L")
            pdf.cell(col_w[1], 7, "P {:,.2f}".format(total),
                     border=0, fill=True, align="R", ln=True)
            fill = not fill

        self._total_row(pdf, "TOTAL INCOME", grand_income, col_w)
        pdf.ln(6)

        # Expense summary
        self._section_header(pdf, "Expenses by Category", 200)
        self._table_header(pdf, ["Category", "Total Amount"], col_w)

        grand_expense = 0
        fill = False
        pdf.set_font("Helvetica", "", 10)
        for cat, total in expense_summary:
            grand_expense += total
            pdf.set_fill_color(253, 236, 234) if fill \
                else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(col_w[0], 7, str(cat),
                     border=0, fill=True, align="L")
            pdf.cell(col_w[1], 7, "P {:,.2f}".format(total),
                     border=0, fill=True, align="R", ln=True)
            fill = not fill

        self._total_row(
            pdf, "TOTAL EXPENSES", grand_expense, col_w,
            color=(220, 53, 69)
        )
        pdf.ln(4)

        # Net balance
        net = grand_income - grand_expense
        net_color = (40, 167, 69) if net >= 0 else (220, 53, 69)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(*net_color)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(col_w[0], 10, "NET BALANCE",
                 border=0, fill=True, align="L")
        pdf.cell(col_w[1], 10, "P {:,.2f}".format(net),
                 border=0, fill=True, align="R", ln=True)
        pdf.ln(8)

        # Transaction details
        self._section_header(pdf, "Transaction Details", 200)
        col_widths = [28, 55, 38, 35, 34]
        headers    = ["Date", "Donor", "Category",
                      "Amount", "Remarks"]
        self._table_header(pdf, headers, col_widths)

        pdf.set_font("Helvetica", "", 8)
        fill = False
        for row in transactions:
            date, donor, cat, amount, remarks = row
            pdf.set_fill_color(248, 249, 250) if fill \
                else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(col_widths[0], 6, str(date),
                     fill=True, align="L")
            pdf.cell(col_widths[1], 6, str(donor or "")[:28],
                     fill=True, align="L")
            pdf.cell(col_widths[2], 6, str(cat)[:18],
                     fill=True, align="L")
            pdf.cell(col_widths[3], 6,
                     "P {:,.0f}".format(amount),
                     fill=True, align="R")
            pdf.cell(col_widths[4], 6, str(remarks or "")[:18],
                     fill=True, align="L", ln=True)
            fill = not fill

        filename = self._save_path("summary", start_date, end_date)
        pdf.output(filename)
        return filename

    def generate_detailed_report(
        self, start_date: str, end_date: str,
        parish_name: str = "St. Joseph Parish"
    ) -> str:
        transactions    = self.db.get_transactions_by_range(
            start_date, end_date
        )
        income_summary  = self.db.get_summary_by_range(
            start_date, end_date
        )
        expense_summary = self.db.get_expense_summary_by_range(
            start_date, end_date
        )

        pdf = ChurchPDF(
            parish_name=parish_name,
            orientation="L", unit="mm", format="A4"
        )
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(79, 134, 247)
        pdf.cell(0, 8, "Detailed Financial Report",
                 ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0, 6, "Period: " + start_date + " to " + end_date,
            ln=True, align="C"
        )
        pdf.ln(6)

        grand_income  = sum(t[1] for t in income_summary)
        grand_expense = sum(t[1] for t in expense_summary)
        net           = grand_income - grand_expense

        # Income summary
        col_w = [140, 70, 67]
        self._section_header(pdf, "Revenue Summary", 277)
        self._table_header(
            pdf, ["Category", "Total", "% of Income"], col_w
        )

        pdf.set_font("Helvetica", "", 10)
        fill = False
        for cat, total in income_summary:
            pct = round(total / grand_income * 100, 1) \
                if grand_income else 0
            pdf.set_fill_color(248, 249, 250) if fill \
                else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(col_w[0], 7, str(cat), fill=True)
            pdf.cell(col_w[1], 7, "P {:,.2f}".format(total),
                     fill=True, align="R")
            pdf.cell(col_w[2], 7, str(pct) + "%",
                     fill=True, align="R", ln=True)
            fill = not fill

        self._total_row(
            pdf, "TOTAL INCOME", grand_income, col_w
        )
        pdf.ln(6)

        # Expense summary
        self._section_header(pdf, "Expense Summary", 277)
        self._table_header(
            pdf, ["Category", "Total", "% of Expenses"], col_w
        )

        pdf.set_font("Helvetica", "", 10)
        fill = False
        for cat, total in expense_summary:
            pct = round(total / grand_expense * 100, 1) \
                if grand_expense else 0
            pdf.set_fill_color(253, 236, 234) if fill \
                else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(col_w[0], 7, str(cat), fill=True)
            pdf.cell(col_w[1], 7, "P {:,.2f}".format(total),
                     fill=True, align="R")
            pdf.cell(col_w[2], 7, str(pct) + "%",
                     fill=True, align="R", ln=True)
            fill = not fill

        self._total_row(
            pdf, "TOTAL EXPENSES", grand_expense, col_w,
            color=(220, 53, 69)
        )
        pdf.ln(4)

        # Net balance
        net_color = (40, 167, 69) if net >= 0 else (220, 53, 69)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(*net_color)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(col_w[0], 10, "NET BALANCE",
                 border=0, fill=True, align="L")
        pdf.cell(col_w[1], 10, "P {:,.2f}".format(net),
                 border=0, fill=True, align="R")
        pdf.cell(col_w[2], 10, "",
                 border=0, fill=True, ln=True)
        pdf.ln(8)

        # Full transaction list
        self._section_header(pdf, "Full Transaction List", 277)
        col_widths = [30, 80, 50, 40, 77]
        headers    = ["Date", "Donor", "Category",
                      "Amount", "Remarks"]
        self._table_header(pdf, headers, col_widths)

        pdf.set_font("Helvetica", "", 8)
        fill = False
        for row in transactions:
            date, donor, cat, amount, remarks = row
            pdf.set_fill_color(248, 249, 250) if fill \
                else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(col_widths[0], 6, str(date), fill=True)
            pdf.cell(col_widths[1], 6, str(donor or "")[:40],
                     fill=True)
            pdf.cell(col_widths[2], 6, str(cat)[:22], fill=True)
            pdf.cell(col_widths[3], 6,
                     "P {:,.0f}".format(amount),
                     fill=True, align="R")
            pdf.cell(col_widths[4], 6, str(remarks or "")[:38],
                     fill=True, ln=True)
            fill = not fill

        filename = self._save_path("detailed", start_date, end_date)
        pdf.output(filename)
        return filename

    # ─── HELPERS ──────────────────────────────────────

    def _section_header(self, pdf, text, line_width):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 8, text, ln=True)
        pdf.set_draw_color(79, 134, 247)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), line_width, pdf.get_y())
        pdf.ln(3)

    def _table_header(self, pdf, headers, col_widths):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(235, 242, 255)
        pdf.set_text_color(50, 50, 50)
        for h, w in zip(headers, col_widths):
            pdf.cell(w, 8, h, border=0, fill=True, align="L")
        pdf.ln()

    def _total_row(self, pdf, label, total, col_w,
                   color=(79, 134, 247)):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(col_w[0], 9, label,
                 border=0, fill=True, align="L")
        pdf.cell(col_w[1], 9, "P {:,.2f}".format(total),
                 border=0, fill=True, align="R", ln=True)

    def _save_path(self, report_type, start_date, end_date):
        os.makedirs("reports", exist_ok=True)
        return (
            "reports/churchtrack_" + report_type +
            "_" + start_date + "_to_" + end_date + ".pdf"
        )


class ChurchPDF(FPDF):

    def __init__(self, parish_name="St. Joseph Parish", **kwargs):
        super().__init__(**kwargs)
        self.parish_name = parish_name

    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 42, 58)
        self.cell(0, 8, self.parish_name, ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "Official Financial Report",
                  ln=True, align="C")
        self.set_draw_color(79, 134, 247)
        self.set_line_width(0.8)
        self.line(
            10, self.get_y() + 1,
            self.w - 10, self.get_y() + 1
        )
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        generated = (
            "Generated by ChurchTrack AI on " +
            datetime.datetime.now().strftime(
                "%B %d, %Y at %I:%M %p"
            )
        )
        self.cell(0, 5, generated, align="C", ln=True)
        self.cell(
            0, 5, "Page " + str(self.page_no()), align="C"
        )
