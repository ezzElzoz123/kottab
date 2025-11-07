from odoo import models, fields, api, _
import io , pytz
import base64
from datetime import datetime
from xlsxwriter import Workbook
from io import BytesIO


class TeacherFinanceReportWizard(models.TransientModel):
    _name = 'quran.teacher.finance.report.wizard'
    _description = 'Teacher Finance Report Wizard'

    branch_ids = fields.Many2many('quran.branch', string="Branches")
    teacher_ids = fields.Many2many('quran.teacher', string="Teachers")
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string="Month", required=True)
    file_name = fields.Char("File Name", readonly=True)
    file_data = fields.Binary("Excel File", readonly=True)
    printed_time = fields.Datetime("Printed Time")

    def _convert_dt_to_user_tz(self, dt):
        user_tz = pytz.timezone(self.env.user.tz)
        user_time = dt.astimezone(user_tz)
        user_date = user_time.date()
        return user_date

    def action_generate_report(self):
        date_now = fields.Datetime.now()
        self.printed_time = self._convert_dt_to_user_tz(date_now)

        output = io.BytesIO()
        workbook = Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Teacher Finance Report')
        worksheet.right_to_left()

        # ===================== 🎨 Formatting =====================
        header_format = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#4F81BD', 'font_color': 'white', 'text_wrap': True,
        })
        cell_format = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
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

        worksheet.set_column('B:Z', 20)
        worksheet.freeze_panes(10, 1)

        row = 1
        worksheet.write(row + 1, 1, _("تاريخ الطباعة"), header_format)
        worksheet.write(row + 1, 2, str(self.printed_time), cell_format)
        worksheet.write(row + 2, 1, _("المستخدم"), header_format)
        worksheet.write(row + 2, 2, self.env.user.name, cell_format)

        if self.env.company and self.env.company.logo:
            buf_image = BytesIO(base64.b64decode(self.env.company.logo))
            worksheet.insert_image('G1', 'logo.png', {'image_data': buf_image, 'x_scale': 0.8, 'y_scale': 0.8})

        # ===================== 📊 Table Header =====================
        row =8
        worksheet.merge_range(row, 1, row, 8, _("Teacher Finance Report"), title_format)
        row = 9
        headers = [
            _("م"), _("المعلم"), _("الفرع"), _("عدد التلاميذ"),
            _("التلاميذ القادرين على الدفع"), _("اجمالي المدفوع"), _("المرتب"), _("صافي الدخل")
        ]
        for col, header in enumerate(headers):
            worksheet.write(row, col + 1, header, header_format)

        worksheet.autofilter(row, 1, row, len(headers))

        teachers = self.env['quran.teacher'].search([
            ('branch_id', 'in', self.branch_ids.ids) if self.branch_ids else (1, '=', 1),
            ('id', 'in', self.teacher_ids.ids) if self.teacher_ids else (1, '=', 1),
        ])

        total_income = total_salary = total_net = 0.0
        row += 1
        color_toggle = False  # alternating colors

        for i, teacher in enumerate(teachers, start=1):
            students = self.env['quran.student'].search([('teacher_id', '=', teacher.id)])
            paying_students = students.filtered(lambda s: s.is_paying)
            month_payments = self.env['quran.payment'].search([
                ('student_id', 'in', students.ids),
                ('month', '=', self.month)
            ])
            income = sum(month_payments.mapped('amount'))
            net = income - teacher.salary

            bg_color = '#DCE6F1' if color_toggle else '#FFFFFF'
            alt_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': bg_color})
            num_alt_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': bg_color, 'num_format': '#,##0.00'})

            worksheet.write(row, 1, i, alt_format)
            worksheet.write(row, 2, teacher.name, alt_format)
            worksheet.write(row, 3, teacher.branch_id.name, alt_format)
            worksheet.write(row, 4, len(students), alt_format)
            worksheet.write(row, 5, len(paying_students), alt_format)
            worksheet.write(row, 6, income, num_alt_format)
            worksheet.write(row, 7, teacher.salary, num_alt_format)
            worksheet.write(row, 8, net, num_alt_format)

            total_income += income
            total_salary += teacher.salary
            total_net += net
            row += 1
            color_toggle = not color_toggle

        worksheet.merge_range(row, 1, row, 5, _("Totals"), title_format)
        worksheet.write(row, 6, total_income, title_format)
        worksheet.write(row, 7, total_salary, title_format)
        worksheet.write(row, 8, total_net, title_format)

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        file_name = f"Teacher_Finance_Report_{self.month}.xlsx"

        self.write({'file_name': file_name, 'file_data': file_data})

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'new',
        }
