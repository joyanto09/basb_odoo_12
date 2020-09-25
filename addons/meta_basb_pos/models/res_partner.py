from odoo import models, api, fields
from datetime import datetime, date


class ResPartner(models.Model):
    _inherit = 'res.partner'

    last_purchase_date = fields.Date('Last Purchase Date')
    last_purchase_diseases = fields.Char('Last Purchase Diseases')

    disease_purchase_id = fields.One2many('disease.purchase.date', 'partner_id', string="Diseases")

    relation_string = fields.Many2one('relation_string') #, compute="get_relation_string")
    #relation_string = fields.Char('relation_string') #, compute="get_relation_string")

    @api.multi
    def get_relation_string(self):
        for item in self:
            key_value_list = item._fields['relation'] #.selection
            key_value_dict = dict()
            for kv in key_value_list:
                print (kv)
                key_value_dict[kv[0]]=kv[1]
            if item.relation:
                item.relation_string = key_value_dict[item.relation]