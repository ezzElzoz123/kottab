from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning

class QuranDonation(models.Model):
    _name = "quran.donation"
    _description = "Donations"

    donor_name = fields.Char("Donor Name")
    branch_id = fields.Many2one("quran.branch", string="Branch")
    date = fields.Date(default=fields.Date.today)
    amount = fields.Float("Amount")
    note = fields.Text("Notes")
