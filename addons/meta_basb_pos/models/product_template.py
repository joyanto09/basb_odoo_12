from odoo import models, api, fields
from datetime import datetime, date


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    generic_code = fields.Char('Generec Code')