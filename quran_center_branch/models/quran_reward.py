from odoo import models, fields, api, _

class QuranReward(models.Model):
    _name = 'quran.reward'
    _description = 'Student Rewards'

    name = fields.Char(string="اسم المكافأة")
    student_id = fields.Many2one('quran.student', string="الطالب", required=True)
    date = fields.Date(string="تاريخ المكافأة", default=fields.Date.today)
    amount = fields.Float(string="المبلغ", required=True)
    notes = fields.Text(string="ملاحظات")

    @api.model
    def create(self, vals):
        reward = super(QuranReward, self).create(vals)
        self.env['quran.expense'].create({
            'name': f"مكافأة {reward.student_id.name}",
            'branch_id': reward.student_id.branch_id.id,
            'amount': reward.amount,
            'date': reward.date,
            'type': 'reward',
        })
        return reward
