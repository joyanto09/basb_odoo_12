# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class res_branch(models.Model):
    _name = 'res.branch'
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)
    sync_ref_id = fields.Char('Sync Ref ID')
    
class BasbDasb(models.Model):
    _name = 'basb.dasb'
    name = fields.Char('Name', required=True)
    sync_ref_id = fields.Char('Sync Ref ID')
    
class BasbRank(models.Model):
    _name = 'basb.rank'
    name = fields.Char('Name', required=True)
    sync_ref_id = fields.Char('Sync Ref ID')
    
class BasbService(models.Model):
    _name = 'basb.service'
    name = fields.Char('Name', required=True)
    sync_ref_id = fields.Char('Sync Ref ID')
    
class BasbDistrict(models.Model):
    _name = 'basb.district'
    name = fields.Char('Name', required=True)
    sync_ref_id = fields.Char('Sync Ref ID')
    
class BasbRelation(models.Model):
    _name = 'basb.relation'
    name = fields.Char('Name', required=True)
    sync_ref_id = fields.Char('Sync Ref ID')
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    sync_ref_id = fields.Char('Sync Ref ID')
    
class ProductProduct(models.Model):
    _inherit = 'product.product'
    sync_ref_id = fields.Char('Sync Ref ID')
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    sync_ref_id = fields.Char('Sync Ref ID')
    transfer_date = fields.Datetime('Transfer Date')    
    
