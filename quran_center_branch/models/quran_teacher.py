from odoo import models, fields, api

class QuranTeacher(models.Model):
    _name = "quran.teacher"
    _description = "Quran Teacher"

    name = fields.Char("Teacher Name", required=True)
    branch_id = fields.Many2one("quran.branch", string="Branch", required=True)
    join_date = fields.Date("Join Date", required=True)
    leave_date = fields.Date("Leave Date")
    salary = fields.Float("Monthly Salary")
    active = fields.Boolean("Active", compute="_compute_active", store=True)
    phone = fields.Char()
    address = fields.Char()


    @api.depends("join_date", "leave_date")
    def _compute_active(self):
        today = fields.Date.today()
        for rec in self:
            if rec.join_date and (not rec.leave_date or rec.leave_date >= today):
                rec.active = True
            else:
                rec.active = False
