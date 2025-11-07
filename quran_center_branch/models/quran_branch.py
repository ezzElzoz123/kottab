from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class QuranBranch(models.Model):
    _name = "quran.branch"
    _description = "Quran Memorization Branch"

    name = fields.Char("Branch Name", required=True)
    manager_id = fields.Many2one("res.users", string="Branch Manager")
    address = fields.Char("Address")
    phone = fields.Char("Phone")
    students_count = fields.Integer(compute="_compute_counts")
    teachers_count = fields.Integer(compute="_compute_counts")
    schedule_ids = fields.One2many('quran.schedule', 'branch_id')

    def _compute_counts(self):
        for rec in self:
            rec.students_count = self.env["quran.student"].search_count([("branch_id", "=", rec.id)])
            rec.teachers_count = self.env["quran.teacher"].search_count([("branch_id", "=", rec.id)])
