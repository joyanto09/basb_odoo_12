from odoo import models, api, fields, _
from datetime import datetime, date

class ProductCategories(models.Model):
    _inherit = 'product.category'

    critical_product_categories = fields.Boolean("Is Critical Stock Category")



class StockQuant(models.Model):
    _inherit = 'stock.quant'


    @api.multi
    def pos_location_stock_filter(self):
        pos_ids = self.env.user.pos_ids
        locations = list()
        for pos_id in pos_ids:
            locations.append(pos_id.stock_location_id.id)
        context = {'search_default_internal_loc': 1, 'group_by': ['product_id', 'location_id']}
        return{
            'name': _('Stock'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form,pivot,graph',
            'res_model': 'stock.quant',
            'domain': [('location_id', 'in', locations)],
            'context': context,
        }
        pass

    
    @api.multi
    def pos_location_critical_stock_filter(self):
        pos_ids = self.env.user.pos_ids
        locations = list()
        for pos_id in pos_ids:
            locations.append(pos_id.stock_location_id.id)
        
        all_products = self.env['product.product'].search([])
        products = list()
        for product_id in all_products:
            if (product_id.categ_id.critical_product_categories):
                products.append(product_id.id)


        context = {'search_default_internal_loc': 1, 'group_by': ['product_id', 'location_id']}
        return{
            'name': _('Critical Stock'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form,pivot,graph',
            'res_model': 'stock.quant',
            'domain': [('location_id', 'in', locations),('product_id', 'in', products)],
            'context': context,
        }
        pass