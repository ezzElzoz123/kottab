from odoo import models, fields, _
import io
import base64
from datetime import datetime
from io import BytesIO
from xlsxwriter import Workbook


class QuranStudentPaymentReportWizard(models.TransientModel):
    _name = 'quran.student.payment.report.wizard'
    _description = 'Student Payment Report Wizard'

    branch_ids = fields.Many2many('quran.branch', string="Branches")
    month = fields.Selection([
        ('01', 'يناير'), ('02', 'فبراير'), ('03', 'مارس'), ('04', 'ابريل'),
        ('05', 'مايو'), ('06', 'يونيو'), ('07', 'يوليو'), ('08', 'اغسطس'),
        ('09', 'سبتمبر'), ('10', 'اكتوبر'), ('11', 'نوفمبر'), ('12', 'ديسمبر')
    ], string="Month")

    file_name = fields.Char("File Name", readonly=True)
    file_data = fields.Binary("Excel File", readonly=True)
    printed_time = fields.Datetime("Printed Time")

    def action_generate_report(self):
        self.printed_time = fields.Datetime.now()

        output = io.BytesIO()
        workbook = Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Student Payments Report')
        worksheet.right_to_left()

        # ====== 🎨 Formats ======
        header_format = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#4F81BD', 'font_color': 'white', 'text_wrap': True,
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        money_format = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'num_format': '#,##0.00'
        })
        title_format = workbook.add_format({
            'font_name': 'Arial', 'bold': True, 'border': 1, 'font_size': 14,
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#ABAFB1',
        })
        paid_format = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#C6EFCE'
        })
        unpaid_format = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFC7CE'
        })
        total_format = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#FFD966',
        })

        worksheet.set_column('B:J', 22)
        worksheet.freeze_panes(10, 1)

        # ====== Header Info ======
        row = 1
        worksheet.write(row + 1, 1, _("تاريخ الطباعة"), header_format)
        worksheet.write(row + 1, 2, str(self.printed_time), cell_format)
        worksheet.write(row + 2, 1, _("المستخدم"), header_format)
        worksheet.write(row + 2, 2, self.env.user.name, cell_format)
        if self.month:
            worksheet.write(row + 3, 1, _("شهر"), header_format)
            worksheet.write(row + 3, 2, dict(self._fields['month'].selection).get(self.month), cell_format)

        # ====== Company Logo ======
        if self.env.company and self.env.company.logo:
            buf_image = BytesIO(base64.b64decode(self.env.company.logo))
            worksheet.insert_image('G1', 'logo.png', {'image_data': buf_image, 'x_scale': 0.8, 'y_scale': 0.8})

        # ====== Title ======
        row = 8
        worksheet.merge_range(row, 1, row, 9, _("Monthly Student Payments Report"), title_format)
        row = 9

        # ====== Columns ======
        headers = [
            _("م"), _("التلميذ"), _("الفرع"), _("المعلم"),
            _("الشهر"), _("لديه القدرة على الدفع"), _("المبلغ المدفوع"), _("تاريخ الدفع"),
            _("المتبقي"), _("الحالة")
        ]
        for col, header in enumerate(headers):
            worksheet.write(row, col + 1, header, header_format)
        worksheet.autofilter(row, 1, row, len(headers))
        row += 1

        # ====== Students Data ======
        student_domain = []
        if self.branch_ids:
            student_domain.append(('branch_id', 'in', self.branch_ids.ids))
        students = self.env['quran.student'].search(student_domain)

        total_should = total_paid = 0.0

        color_toggle = False
        for i, student in enumerate(students, start=1):
            bg_color = '#DCE6F1' if color_toggle else '#FFFFFF'
            dynamic_money_format = workbook.add_format({
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'num_format': '#,##0.00', 'bg_color': bg_color
            })
            alt_format = workbook.add_format(
                {'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': bg_color})
            num_alt_format = workbook.add_format({
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'bg_color': bg_color, 'num_format': '#,##0.00'
            })
            # نجيب الفرع والمدرس والمفروض يدفع كام
            branch = student.branch_id
            teacher = student.teacher_id
            should_pay = getattr(student, 'monthly_fee', 0.0)

            # نجيب المدفوعات الخاصة بالشهر
            pay_domain = [('student_id', '=', student.id)]
            if self.month:
                pay_domain.append(('month', '=', self.month))
            payment = self.env['quran.payment'].search(pay_domain, limit=1)

            paid_amount = payment.amount if payment else 0.0
            payment_date = payment.date if payment else ''
            remaining = should_pay - paid_amount
            total_should += should_pay
            total_paid += paid_amount

            status_format = paid_format if paid_amount >= should_pay else unpaid_format
            status_text = _("Paid") if paid_amount > should_pay else _("Not Paid")
            # 🔹 منطق تحديد الحالة
            if should_pay == 0:
                status_text = _("Exempt")
                status_format = paid_format
            elif paid_amount > 0:
                status_text = _("Paid")
                status_format = paid_format
            else:
                status_text = _("Not Paid")
                status_format = unpaid_format

            worksheet.write(row, 1, i, alt_format)
            worksheet.write(row, 2, student.name or '', alt_format)
            worksheet.write(row, 3, branch.name or '', alt_format)
            worksheet.write(row, 4, teacher.name if teacher else '', alt_format)
            worksheet.write(row, 5, dict(self._fields['month'].selection).get(self.month, ''), alt_format)
            worksheet.write(row, 6, should_pay, dynamic_money_format)
            worksheet.write(row, 7, paid_amount, dynamic_money_format)
            worksheet.write(row, 8, str(payment_date), alt_format)
            worksheet.write(row, 9, remaining, dynamic_money_format)
            worksheet.write(row, 10, status_text, status_format)

            color_toggle = not color_toggle
            row += 1

        # ====== Totals ======
        worksheet.merge_range(row, 1, row, 5, _("Total"), title_format)
        worksheet.write(row, 6, total_should, title_format)
        worksheet.write(row, 7, total_paid, title_format)
        worksheet.merge_range(row, 8, row, 10, '', title_format)

        # ====== Save ======
        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        file_name = f"Student_Payment_Report_{self.month or 'All'}.xlsx"

        self.write({'file_name': file_name, 'file_data': file_data})

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'new',
        }
