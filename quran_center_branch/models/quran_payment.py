from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning

class QuranPayment(models.Model):
    _name = "quran.payment"
    _description = "Student Payments"

    student_id = fields.Many2one("quran.student", string="Student", required=True)
    branch_id = fields.Many2one(related="student_id.branch_id", store=True)
    date = fields.Date(default=fields.Date.today)
    amount = fields.Float("Amount", required=True)
    note = fields.Char("Note")
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string="Month", required=True)