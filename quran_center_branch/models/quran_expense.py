from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning

class QuranExpense(models.Model):
    _name = "quran.expense"
    _description = "Operating Expenses"

    name = fields.Char("Expense Name", required=True)
    branch_id = fields.Many2one("quran.branch", string="Branch")
    date = fields.Date(default=fields.Date.today)
    amount = fields.Float("Amount")
    type = fields.Selection([
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('rent', 'Rent'),
        ('supplies', 'Supplies'),
        ('reward', 'Reward'),
        ('other', 'Other'),
    ], string="Expense Type")
