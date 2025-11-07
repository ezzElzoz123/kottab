from odoo import models, fields, api

class QuranStudent(models.Model):
    _name = "quran.student"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quran Student"

    name = fields.Char("Student Name", required=True, tracking=True)
    branch_id = fields.Many2one("quran.branch", string="Branch", required=True, tracking=True)
    teacher_id = fields.Many2one("quran.teacher", string="Teacher", tracking=True)
    join_date = fields.Date("Join Date", required=True, tracking=True)
    leave_date = fields.Date("Leave Date", tracking=True)
    is_paying = fields.Boolean("Pays Monthly?", default=True, tracking=True)
    monthly_fee = fields.Float("Monthly Fee", tracking=True)
    payment_ids = fields.One2many("quran.payment", "student_id", string="Payments", tracking=True)
    total_paid = fields.Float(compute="_compute_total_paid", string="Total Paid", tracking=True)
    active = fields.Boolean("Active", compute="_compute_active", store=True)
    student_type = fields.Selection(
        [('ejaza', 'Ejaza'),
         ('talqen', 'Talqen'),
         ('normal', 'Normal'),
         ],
        default='normal',
    )
    is_hafiz = fields.Boolean(tracking=True)
    current_surah = fields.Char(tracking=True)
    current_juz = fields.Integer(tracking=True)
    reward_ids = fields.One2many('quran.reward', 'student_id', tracking=True)
    exam_ids = fields.One2many('quran.exam', 'student_id', tracking=True)
    schedule_id = fields.Many2one('quran.schedule', tracking=True)

    @api.onchange('is_hafiz')
    def _onchange_is_hafiz(self):
        if self.is_hafiz:
            self.current_surah = False
            self.current_juz = False

    @api.depends("join_date", "leave_date")
    def _compute_active(self):
        today = fields.Date.today()
        for rec in self:
            if rec.join_date and (not rec.leave_date or rec.leave_date >= today):
                rec.active = True
            else:
                rec.active = False

    @api.depends('payment_ids.amount')
    def _compute_total_paid(self):
        for rec in self:
            rec.total_paid = sum(rec.payment_ids.mapped('amount'))
