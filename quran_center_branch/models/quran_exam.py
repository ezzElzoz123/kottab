from odoo import models, fields

class QuranExam(models.Model):
    _name = 'quran.exam'
    _description = 'Quran Memorization Exam'

    name = fields.Char(string="اسم الامتحان")
    student_id = fields.Many2one('quran.student', string="الطالب", required=True)
    teacher_id = fields.Many2one('quran.teacher', string="الشيخ", required=True)
    exam_date = fields.Date(string="تاريخ الامتحان", required=True)
    surah = fields.Char(string="السورة")
    juz = fields.Integer(string="الجزء")
    score = fields.Float(string="الدرجة")
    notes = fields.Text(string="ملاحظات")
