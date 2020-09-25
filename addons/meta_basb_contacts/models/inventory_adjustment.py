from odoo import api, models, fields, _
from odoo.exceptions import UserError
import datetime


class StockInventory(models.Model):
    _inherit = 'stock.inventory'


    meta_year = fields.Char("Year")
    meta_quarter = fields.Selection([('qem','QE-March'),('qej','QE-June'),('qes','QE-September'),('qed','QE-December')], string="Quarter")