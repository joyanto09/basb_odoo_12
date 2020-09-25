# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

#https://medium.com/@hendrasj/how-to-create-a-custom-report-on-odoo-12-53ca68238d64

class StockConsumptionWizard(models.TransientModel):

    _name = 'stock.consumption.wizard'

    warehouse = fields.Many2one("stock.warehouse", string="Dispensary", required=True)
    date_start = fields.Date('Date Start', required=True, default=fields.Date.today)
    date_end = fields.Date('Date End', required=True, default=fields.Date.today)
    
    @api.multi
    def print_report(self):
        
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
                'location_id': self.warehouse.lot_stock_id.id,
                'warehouse_name': self.warehouse.name,
            },
        }
        
        # use `module_name.report_id` as reference.
        # `report_action()` will call `_get_report_values()` and pass `data` automatically.
        return self.env.ref('meta_stock_consumption.stock_consumption_report').report_action(self, data=data)

class StockConsumptionData(models.AbstractModel): 
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.meta_stock_consumption.stock_consumption_report_view'
    
    @api.multi
    def get_opening_qty_total(self, filter_date_start, product_id, location_id):
   
        location_id = int(location_id)
        product_id = int(product_id)
        stock_lines = self.env['stock.move'].search(
            [
                '&', 
                '&', '&',
                ('state','=','done'),
                ('date_expected', '<', filter_date_start),
                ('product_id', '=', product_id),
                '|', 
                ('location_id', '=', location_id),
                ('location_dest_id', '=', location_id),
            ]
        ) 
        
        opening_qty_total = 0
        for stock in stock_lines:    
            
            #split issue and adjust
            issue_qty = stock.product_qty
            adjust_qty = 0
            if stock.location_dest_id.id != location_id:
                issue_qty = 0
                adjust_qty = stock.product_qty
                
            opening_qty_total = opening_qty_total + issue_qty - adjust_qty 

        return opening_qty_total
    
    @api.model
    def _get_report_values(self, docids, data=None):
        
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        location_id = data['form']['location_id']
        warehouse_name = data['form']['warehouse_name']
        date_start_obj = datetime.datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.datetime.strptime(date_end, DATE_FORMAT)
        
        stock_lines = self.env['stock.move'].search(
            [
                '&', 
                '&', '&', 
                ('state','=','done'),
                ('date_expected', '>=', date_start),
                ('date_expected', '<=', date_end), 
                '|', 
                ('location_id', '=', location_id),
                ('location_dest_id', '=', location_id),
            ], 
            order='product_id asc, date_expected asc',
        ) 
            
        #get partner_location/customer
        customer_location = self.env['stock.location'].search([('usage','=','customer')])
        customer_location_id = customer_location.id
        
        docs = []
        for stock in stock_lines:                          
                
            #seperation of issue, adjust and consumption qauntities
            issue_qty = stock.product_qty
            adjust_qty = 0
            consumption_qty = 0
            if stock.location_dest_id.id == customer_location_id:
                issue_qty = 0
                consumption_qty = stock.product_qty
            elif stock.location_dest_id.id != location_id:
                issue_qty = 0
                adjust_qty = stock.product_qty
               
            docs.append({
                'product_id': stock.product_id.id,
                'product_name': stock.product_id.name,
                'transfer_date': datetime.datetime.strptime(str(stock.date_expected), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y'),
                'issue_qty': issue_qty,
                'adjust_qty': adjust_qty,
                'consumption_qty': consumption_qty,
            })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': docs,
            'filter_date_start': date_start,
            'filter_date_end': date_end,
            'location_id': location_id,
            'get_opening_qty_total': self.get_opening_qty_total,
            'warehouse_name': warehouse_name,
            'date_start_range': datetime.datetime.strptime(date_start, '%Y-%m-%d').strftime('%d/%m/%Y'),
            'date_end_range': datetime.datetime.strptime(date_end, '%Y-%m-%d').strftime('%d/%m/%Y'),
        } 
        