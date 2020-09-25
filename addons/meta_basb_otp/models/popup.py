
from odoo import api, models, fields

class PosPopup(models.Model):
    _name = 'pos.popup'

    pin = fields.Char('PIN', size=6, required=True)
