from odoo import _, api, fields, models

class QuranSchedule(models.Model):
    _name = "quran.schedule"
    _description = "Schedules"

    name = fields.Char(required=1)
    branch_id = fields.Many2one('quran.branch')