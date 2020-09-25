#####################################
from odoo import models, api, fields
from odoo.exceptions import UserError


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    dasb_id = fields.Many2one('basb.dasb', 'DASB') 
    day_limit = fields.Integer('Order Day Limit')
    
    def apply_day_limit_to_all_session(self):
        record_ids = self.env['pos.config'].search([('id','>',0)])     
        for record in record_ids:    
            record.write({'day_limit': self.day_limit})