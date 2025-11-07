from odoo import models, fields, api, _
import io
import base64
from datetime import datetime
from io import BytesIO
from xlsxwriter import Workbook
from odoo.tools import date_utils


class QuranBranchReportWizard(models.TransientModel):
    _name = 'quran.branch.report.wizard'
    _description = 'Monthly Branch Financial Report Wizard'

    month = fields.Selection([
        ('01', 'يناير'), ('02', 'فبراير'), ('03', 'مارس'), ('04', 'ابريل'),
        ('05', 'مايو'), ('06', 'يونيو'), ('07', 'يوليو'), ('08', 'اغسطس'),
        ('09', 'سبتمبر'), ('10', 'اكتوبر'), ('11', 'نوفمبر'), ('12', 'ديسمبر')
    ], string="Month", required=True)

    year = fields.Char(string="Year", default=lambda self: str(datetime.now().year))
    branch_ids = fields.Many2many('quran.branch', string="الفرع")
    file_name = fields.Char("File Name", readonly=True)
    file_data = fields.Binary("Excel File", readonly=True)
    printed_time = fields.Datetime("تاريخ الطباعة")

    def action_generate_report(self):
        # ========== إعداد التاريخ والطباعة ==========
        self.printed_time = fields.Datetime.now()

        output = io.BytesIO()
        workbook = Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Branch Monthly Report')
        worksheet.right_to_left()

        # ========== 🎨 تنسيقات عامة ==========
        header_format = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#4F81BD', 'font_color': 'white', 'text_wrap': True,
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        number_format = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'num_format': '#,##0.00'
        })
        title_format = workbook.add_format({
            'font_name': 'Arial', 'bold': True, 'border': 1, 'font_size': 14,
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#ABAFB1',
        })
        total_format = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#FFD966',
        })

        worksheet.set_column('B:H', 20)
        worksheet.freeze_panes(10, 1)

        # ========== 🧾 Header Section ==========
        row = 1
        worksheet.write(row + 1, 1, _("تاريخ الطباعة"), header_format)
        worksheet.write(row + 1, 2, str(self.printed_time), cell_format)
        worksheet.write(row + 2, 1, _("المستخدم"), header_format)
        worksheet.write(row + 2, 2, self.env.user.name, cell_format)
        worksheet.write(row + 3, 1, _("الشهر"), header_format)
        worksheet.write(row + 3, 2, f"{self.month}-{self.year}", cell_format)

        if self.env.company and self.env.company.logo:
            buf_image = BytesIO(base64.b64decode(self.env.company.logo))
            worksheet.insert_image('G1', 'logo.png', {'image_data': buf_image, 'x_scale': 0.8, 'y_scale': 0.8})

        # ========== 📋 عنوان التقرير ==========
        row = 8
        worksheet.merge_range(row, 1, row, 7, _("Monthly Branch Financial Report"), title_format)
        row = 9

        # ========== 🧱 الأعمدة ==========
        headers = [
            _("م"), _("الفرع"), _("المبلغ المدفوغ"), _("مبلغ التبرع"),
            _("المرتب"), _("المصروفات"), _("صافي الدخل")
        ]
        for col, header in enumerate(headers):
            worksheet.write(row, col + 1, header, header_format)

        worksheet.autofilter(row, 1, row, len(headers))

        # ========== 🧮 الحسابات ==========
        month = int(self.month)
        year = int(self.year)
        start_date = datetime(year, month, 1)
        end_date = date_utils.end_of(start_date, 'month')

        branches = self.branch_ids or self.env['quran.branch'].search([])
        row += 1
        color_toggle = False

        total_payments = total_donations = total_salaries = total_expenses = total_net = 0.0

        for i, branch in enumerate(branches, start=1):
            payments = self.env['quran.payment'].search([
                ('branch_id', '=', branch.id),
                ('date', '>=', start_date.date()),
                ('date', '<=', end_date.date())
            ])
            donations = self.env['quran.donation'].search([
                ('branch_id', '=', branch.id),
                ('date', '>=', start_date.date()),
                ('date', '<=', end_date.date())
            ])
            expenses = self.env['quran.expense'].search([
                ('branch_id', '=', branch.id),
                ('date', '>=', start_date.date()),
                ('date', '<=', end_date.date())
            ])
            teachers = self.env['quran.teacher'].search([('branch_id', '=', branch.id)])

            pay_total = sum(payments.mapped('amount'))
            don_total = sum(donations.mapped('amount'))
            exp_total = sum(expenses.mapped('amount'))
            sal_total = sum(teachers.mapped('salary'))
            net = (pay_total + don_total) - (sal_total + exp_total)

            bg_color = '#DCE6F1' if color_toggle else '#FFFFFF'
            alt_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': bg_color})
            num_alt_format = workbook.add_format({
                'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': bg_color, 'num_format': '#,##0.00'
            })

            worksheet.write(row, 1, i, alt_format)
            worksheet.write(row, 2, branch.name, alt_format)
            worksheet.write(row, 3, pay_total, num_alt_format)
            worksheet.write(row, 4, don_total, num_alt_format)
            worksheet.write(row, 5, sal_total, num_alt_format)
            worksheet.write(row, 6, exp_total, num_alt_format)
            worksheet.write(row, 7, net, num_alt_format)

            total_payments += pay_total
            total_donations += don_total
            total_salaries += sal_total
            total_expenses += exp_total
            total_net += net
            row += 1
            color_toggle = not color_toggle

        # ========== ✅ Totals ==========
        worksheet.merge_range(row, 1, row, 2, _("Totals"), title_format)
        worksheet.write(row, 3, total_payments, title_format)
        worksheet.write(row, 4, total_donations, title_format)
        worksheet.write(row, 5, total_salaries, title_format)
        worksheet.write(row, 6, total_expenses, title_format)
        worksheet.write(row, 7, total_net, title_format)

        # ========== 🧾 حفظ التقرير ==========
        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        file_name = f"Branch_Financial_Report_{self.month}_{self.year}.xlsx"

        self.write({'file_name': file_name, 'file_data': file_data})

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'new',
        }
