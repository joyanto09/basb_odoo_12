from odoo import models, api, fields


class PosConfigInherited(models.Model):
    _inherit = 'pos.config'
    pos_image = fields.Binary(string='Dispensary Image')
    # pos_employees = fields.Many2many('hr.employee', string="POS Employees")
    pos_employee_secretary = fields.Many2one('hr.employee', string="POS Secretary")
    pos_employee_doctor = fields.Many2one('hr.employee', string="POS Doctor")
    pos_employee_dispensary_in_charge = fields.Many2one('hr.employee', string="POS Dispensary In-Charge")
    pos_employee_medical_assistant = fields.Many2one('hr.employee', string="POS Medical Assistant")