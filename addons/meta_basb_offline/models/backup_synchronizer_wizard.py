# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, except_orm, UserError
import requests
import json
import urllib2
import sys
reload(sys)
sys.setdefaultencoding('utf8')


base_url = 'http://127.0.0.1:8069/restapi/1.0'


class SynchronizerWizard(models.Model):
    
    _name = "synchronizer.wizard"
    _description = 'Synchronizer Wizard'


    sync_type = fields.Selection(
        string = 'Sync Type',
        selection = [
            ('all', 'All'),
            ('branch', 'Market(s)'),
            ('partner', 'Customer(s)'),
            ('user', 'User(s)'),
            ('product', 'Product(s)'),
            ('quotation', 'Quotation(s)'),
            ('sale_order', 'Sale Order(s)')
        ],
        default = 'all'
    )


    @api.multi
    def sync(self):
        internet_connectivity = self.check_internet_connectivity()
        if not internet_connectivity:
            raise UserError("There is no internet connection.")
        else:
            self.ensure_one()
            _company_id = self.env.user.company_id.id
            _currencyId = self.env.user.company_id.currency_id.id
            _sync_type = self.sync_type
            
            if _sync_type == "branch":
                self.sync_branch_push(True)
            elif _sync_type == "partner":
                self.sync_branch_push(False)
                self.sync_partners_push(True)
            elif _sync_type == "user":
                self.sync_branch_push(False)
                self.sync_partners_push(False)
                self.sync_users_push(True)
            elif _sync_type == "product":
                self.sync_products_push(True)
            elif _sync_type == "quotation":
                self.sync_quotations_pull(True)
            elif _sync_type == "sale_order":
                self.sync_sale_orders_push(True)
            else:
                self.sync_branch_push(False)
                self.sync_partners_push(False)
                self.sync_users_push(False)
                self.sync_products_push(False)
                self.sync_sale_orders_push(False)
                self.sync_quotations_pull(False)
                return {'type': 'ir.actions.client', 'tag': 'reload'}

    
    @api.multi
    def check_internet_connectivity(self):
        try:
            urllib2.urlopen('http://216.58.200.142', timeout=1)
            return True
        except urllib2.URLError as err:
            return False

    
    @api.multi
    def sync_partners_push(self, isReload):
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
        
        items = self.env['res.partner'].search([('web_ref_id','!=','Synced'),('customer','=',True),('active','=',True),('is_company','=',False)])
        if items:
            for item in items:
                ## Update 'trace_time'
                item.write({
                    'trace_time': datetime.now().replace(microsecond=0),
                })
                # item.trace_time = datetime.now().replace(microsecond=0) # here data actually stored in db

                ## Check Record is Update or Not & Add Clause/Condition
                condition = ""
                # _is_update = item['is_update'] if item['is_update'] else False
                _online_partner_id = item['online_partner_id'] if item['online_partner_id'] else ''
                if _online_partner_id: condition = "/" + str(_online_partner_id)

                ## Push to API
                _name = item['name'] if item['name'] else ''
                _street = item['street'] if item['street'] else ''
                _phone = item['phone'] if item['phone'] else ''
                _mobile = item['mobile'] if item['mobile'] else ''
                _customer = item['customer'] if item['customer'] else False
                _supplier = item['supplier'] if item['supplier'] else False
                _type = item['type'] if item['type'] else ''
                _notify_email = item['notify_email'] if item['notify_email'] else ''
                _branch_id = item['branch_id'].id if item['branch_id'] else "''" # May not need
                _trace_time = item['trace_time'] if item['trace_time'] else ''

                if _branch_id and _branch_id != "''": # May not need
                    # branch = self.env['res.branch'].browse(_branch_id)
                    # if branch: _branch_id = branch.online_branch_id
                    _branch_id = item.branch_id.online_branch_id
                
                url = base_url + str("/object/res.partner" + condition + "?vals={"
                    + "'name':'" + str(_name) + "'"
                    + ",'street':'" + str(_street) + "'"
                    + ",'phone':'" + str(_phone) + "'"
                    + ",'mobile':'" + str(_mobile) + "'"
                    + ",'customer':'" + str(_customer) + "'"
                    + ",'supplier':'" + str(_supplier) + "'"
                    + ",'type':'" + str(_type) + "'"
                    + ",'notify_email':'" + str(_notify_email) + "'"
                    + ",'branch_id':" + str(_branch_id)
                    + ",'trace_time':'" + str(_trace_time) + "'"
                    + "}"
                )
                response = ""
                if _online_partner_id:
                    response = requests.put(url, data="")
                else:
                    response = requests.post(url, data="")
                
                if response:
                    if response.status_code == 200 or response.status_code == 201:
                        _partner_id = json.loads(json.dumps(response.json()['res.partner']))[0]['id']
                        
                        ## Update 'web_ref_id'
                        # item.write({
                        #     'web_ref_id': 'Synced',
                        # })
                        query = """ UPDATE res_partner
                                    SET web_ref_id = 'Synced', online_partner_id = %s
                                    WHERE id = %s; """
                        #, is_update = 'False'
                        params = (str(_partner_id),str(item['id']),)
                        self.env.cr.execute(query, params)
                #     else:
                #         raise UserError(str(response) + "\nFailed to Sync Customer(s).")
                # else:
                #     raise UserError(str(response) + "\nFailed to Sync Customer(s).")
            
            if isReload:
                # msg = str(len(items)) + " item(s) synced successfully."
                return {'type': 'ir.actions.client', 'tag': 'reload'}
        else:
            if isReload:
                raise UserError("No data found to sync.")

    
    @api.multi
    def sync_products_push(self, isReload):
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
        
        items = self.env['product.template'].search([('web_ref_id','!=','Synced'),('sale_ok','=',True),('type','=','product')])
        if items:
            for item in items:
                ## Update 'trace_time'
                item.write({
                    'trace_time': datetime.now().replace(microsecond=0),
                })

                ## Check Record is Update or Not & Add Clause/Condition
                condition = ""
                # _is_update = item['is_update'] if item['is_update'] else False
                _online_product_template_id = item['online_product_template_id'] if item['online_product_template_id'] else ''
                if _online_product_template_id: condition = "/" + str(_online_product_template_id)

                ## Push to API
                _product_template_id = item['id'] if item['id'] else ''
                _name = item['name'] if item['name'] else ''
                _list_price = item['list_price'] if item['list_price'] else 0
                _company_id = item['company_id'].id if item['company_id'] else "''"
                _active = item['active'] if item['active'] else 'false'
                _uom_id = item['uom_id'].id if item['uom_id'] else "''"
                _uom_po_id = item['uom_po_id'].id if item['uom_po_id'] else "''"
                _categ_id = item['categ_id'].id if item['categ_id'] else "''"
                _type = item['type'] if item['type'] else ''
                _trace_time = item['trace_time'] if item['trace_time'] else ''
                
                url = base_url + str("/object/product.template" + condition + "?vals={"
                    + "'name':'" + str(_name) + "'"
                    + ",'list_price':" + str(_list_price)
                    + ",'company_id':" + str(_company_id)
                    + ",'active':'" + str(_active) + "'"
                    + ",'uom_id':" + str(_uom_id)
                    + ",'uom_po_id':" + str(_uom_po_id)
                    # + ",'categ_id':" + str(_categ_id)
                    + ",'type':'" + str(_type) + "'"
                    + ",'trace_time':'" + str(_trace_time) + "'"
                    + "}"
                )
                response = ""
                if _online_product_template_id:
                    response = requests.put(url, data="")
                else:
                    response = requests.post(url, data="")
                
                if response:
                    if response.status_code == 200 or response.status_code == 201:
                        product_template_id = json.loads(json.dumps(response.json()['product.template'][0]))['id']
                        url = base_url + "/object/product.product?domain=[('product_tmpl_id','='," + str(product_template_id) + ")]&fields=['id','name','display_name','trace_time']"
                        response = requests.get(url, data="")
                        data = json.loads(json.dumps(response.json()['product.product']))
                        __product_id = data[0]['id']
                        __display_name = data[0]['display_name'] # Not using now
                        
                        if response:
                            if response.status_code == 200 or response.status_code == 201:
                                subitems_local = self.env['product.product'].search([('product_tmpl_id','=',_product_template_id)])
                                if subitems_local:
                                    for subitem in subitems_local:
                                        _product_product_id = item['id'] if item['id'] else ''
                                        _memo_amount = subitem['memo_amount'] if subitem['memo_amount'] else 0
                                        _transport_expense = subitem['transport_expense'] if subitem['transport_expense'] else 0
                                        _bank_expense = subitem['bank_expense'] if subitem['bank_expense'] else 0
                                        _labour_expense = subitem['labour_expense'] if subitem['labour_expense'] else 0
                                        _other_expense = subitem['other_expense'] if subitem['other_expense'] else 0
                                        _net_amount = subitem['net_amount'] if subitem['net_amount'] else 0
                                        _profit_rate = subitem['profit_rate'] if subitem['profit_rate'] else 0
                                        _sale_price_box = subitem['sale_price_box'] if subitem['sale_price_box'] else 0
                                        _sale_price_pcs = subitem['sale_price_pcs'] if subitem['sale_price_pcs'] else 0
                                        _mrp_amount = subitem['mrp_amount'] if subitem['mrp_amount'] else 0
                                        _package_size = subitem['package_size'] if subitem['package_size'] else 1
                                        _free_description = subitem['free_description'] if subitem['free_description'] else ''

                                        record = subitem.write({
                                            'online_product_product_id': __product_id
                                        })

                                        suburl = base_url + str("/object/product.product/" + str(__product_id) + "?vals={"
                                            + "'name':'" + str(_name) + "'"
                                            + ",'memo_amount':" + str(_memo_amount)
                                            + ",'transport_expense':" + str(_transport_expense)
                                            + ",'bank_expense':" + str(_bank_expense)
                                            + ",'labour_expense':" + str(_labour_expense)
                                            + ",'other_expense':" + str(_other_expense)
                                            + ",'net_amount':" + str(_net_amount)
                                            + ",'profit_rate':" + str(_profit_rate)
                                            + ",'sale_price_box':" + str(_sale_price_box)
                                            + ",'sale_price_pcs':" + str(_sale_price_pcs)
                                            + ",'mrp_amount':" + str(_mrp_amount)
                                            + ",'package_size':" + str(_package_size)
                                            + ",'free_description':'" + str(_free_description) + "'"
                                            + "}"
                                        )
                                        subresponse = requests.put(suburl, data="")
                        #     else:
                        #         raise UserError(str(response) + "\nFailed to Sync Product(s) Costing.")
                        # else:
                        #     raise UserError(str(response) + "\nFailed to Sync Product(s) Costing.")
                                            
                        ## Update 'web_ref_id'
                        # item.write({
                        #     'web_ref_id': 'Synced',
                        # })
                        query = """ UPDATE product_template
                                    SET web_ref_id = 'Synced', online_product_template_id = %s
                                    WHERE id = %s; """
                        #, is_update = 'False'
                        params = (str(product_template_id),str(item['id']),)
                        self.env.cr.execute(query, params)
                #     else:
                #         raise UserError(str(response) + "\nFailed to Sync Product(s).")
                # else:
                #     raise UserError(str(response) + "\nFailed to Sync Product(s).")
            
            if isReload:
                # msg = str(len(items)) + " item(s) synced successfully."
                return {'type': 'ir.actions.client', 'tag': 'reload'}
        else:
            if isReload:
                raise UserError("No data found to sync.")

    
    @api.multi
    def sync_quotations_pull(self, isReload):
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
        
        url = base_url + "/object/sale.order?domain=[('state','=','draft'),('web_ref_id','!=','Synced')]&fields=['id','name','date_order','partner_id','amount_untaxed','amount_tax','amount_total','user_id','apps_ref_id','trace_time','note']&order='id'"
        response = requests.get(url, data="")

        if response:
            if response.status_code == 200 or response.status_code == 201:
                items = json.loads(json.dumps(response.json()['sale.order']))
                if items:
                    for item in items:
                        online_sale_order_id = item['id'] if item['id'] else ''
                        _name = item['name'] if item['name'] else ''
                        _date_order = item['date_order'] if item['date_order'] else ''
                        _partner_id = item['partner_id'][0] if item['partner_id'] else ''
                        _partner_name = item['partner_id'][1] if item['partner_id'] else ''
                        _amount_untaxed = item['amount_untaxed'] if item['amount_untaxed'] else 0
                        _amount_tax = item['amount_tax'] if item['amount_tax'] else 0
                        _amount_total = item['amount_total'] if item['amount_total'] else 0
                        _user_id = item['user_id'][0] if item['user_id'] else ''
                        # _apps_ref_id = item['apps_ref_id'] if item['apps_ref_id'] else ''
                        _trace_time = item['trace_time'] if item['trace_time'] else ''
                        _note = item['note'] if item['note'] else ''

                        if _user_id:
                            user = self.env['res.users'].search([('online_user_id','=',_user_id)])
                            if user: _user_id = user.id

                        if online_sale_order_id and _partner_id:
                            partner = self.env['res.partner'].search([('customer','=',True),('online_partner_id','=',_partner_id)])
                            if partner:
                                record = self.env['sale.order'].create({
                                    'name': _name,
                                    'date_order': _date_order,
                                    'partner_id': partner.id,
                                    'amount_untaxed': _amount_untaxed,
                                    'amount_tax': _amount_tax,
                                    'amount_total': _amount_total,
                                    'user_id': _user_id,
                                    # 'apps_ref_id': _apps_ref_id,
                                    'trace_time': _trace_time,
                                    'note': _note,
                                    'state': 'draft',
                                    'web_ref_id': 'Not Sync',
                                    'online_sale_order_id': online_sale_order_id
                                })

                                _order_id = record.id
                                
                                if _order_id:
                                    url = base_url + "/object/sale.order.line?domain=[('order_id','='," + str(online_sale_order_id) + ")]&fields=['id','name','order_id','product_id','product_uom','product_uom_qty','price_subtotal','order_partner_id','price_reduce','price_reduce_taxinc','price_total','salesman_id','box_quantity','pcs_quantity','mrp_amount','discount']"
                                    response = requests.get(url, data="")

                                    if response:
                                        if response.status_code == 200 or response.status_code == 201:
                                            subitems = json.loads(json.dumps(response.json()['sale.order.line']))
                                            if subitems:
                                                for subitem in subitems:
                                                    __id = subitem['id'] if subitem['id'] else ''
                                                    __name = subitem['name'] if subitem['name'] else ''
                                                    __product_id = subitem['product_id'][0] if subitem['product_id'] else "''"
                                                    __product_uom = subitem['product_uom'][0] if subitem['product_uom'] else "''"
                                                    __product_uom_qty = subitem['product_uom_qty'] if subitem['product_uom_qty'] else 0
                                                    __price_subtotal = subitem['price_subtotal'] if subitem['price_subtotal'] else 0
                                                    # __order_partner_id = subitem['order_partner_id'][0] if subitem['order_partner_id'] else "''"
                                                    __price_reduce = subitem['price_reduce'] if subitem['price_reduce'] else 0
                                                    __price_reduce_taxinc = subitem['price_reduce_taxinc'] if subitem['price_reduce_taxinc'] else 0
                                                    __price_total = subitem['price_total'] if subitem['price_total'] else ''
                                                    __salesman_id = subitem['salesman_id'][0] if subitem['salesman_id'] else ''
                                                    __box_quantity = subitem['box_quantity'] if subitem['box_quantity'] else 0
                                                    __pcs_quantity = subitem['pcs_quantity'] if subitem['pcs_quantity'] else 0
                                                    __mrp_amount = subitem['mrp_amount'] if subitem['mrp_amount'] else 0
                                                    __discount = subitem['discount'] if subitem['discount'] else 0

                                                    if __salesman_id:
                                                        user = self.env['res.users'].search([('online_user_id','=',__salesman_id)])
                                                        if user: __salesman_id = user.id

                                                    product = self.env['product.product'].search([('online_product_product_id','=',__product_id)])
                                                    if product:
                                                        subrecord = self.env['sale.order.line'].create({
                                                            'name': __name,
                                                            'product_id': product.id,
                                                            'product_uom': __product_uom,
                                                            'product_uom_qty': __product_uom_qty,
                                                            'price_subtotal': __price_subtotal,
                                                            # 'order_partner_id': __order_partner_id,
                                                            'price_reduce': __price_reduce,
                                                            'price_reduce_taxinc': __price_reduce_taxinc,
                                                            'price_total': __price_total,
                                                            'salesman_id': __salesman_id,
                                                            'box_quantity': __box_quantity,
                                                            'pcs_quantity': __pcs_quantity,
                                                            'mrp_amount': __mrp_amount,
                                                            'discount': __discount,
                                                            'online_sale_order_line_id': __id,
                                                            'order_id': _order_id
                                                        })
                                    #     else:
                                    #         raise UserError(str(response) + "\nFailed to Sync Quotation Line(s).")
                                    # else:
                                    #     raise UserError(str(response) + "\nFailed to Sync Quotation Line(s).")
                                
                                ## Update 'web_ref_id'
                                url_status = base_url + "/object/sale.order/" + str(online_sale_order_id) + "?vals={'web_ref_id':'Synced'}"
                                response_status = requests.put(url_status, data="")
                    
                    if isReload:
                        # msg = str(len(items)) + " item(s) synced successfully."
                        return {'type': 'ir.actions.client', 'tag': 'reload'}
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        #     else:
        #         raise UserError(str(response) + "\nFailed to Sync Quotation(s).")
        else:
            # raise UserError(str(response) + "\nFailed to Sync Quotation(s).")
            if isReload:
                raise UserError("No data found to sync.")

    
    @api.multi
    def sync_sale_orders_push(self, isReload):
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
        
        items = self.env['sale.order'].search([('web_ref_id','!=','Synced'),('state','=','sale'),('online_sale_order_id','!=','')])
        if items:
            for item in items:
                ## Update 'trace_time'
                item.write({
                    'trace_time': datetime.now().replace(microsecond=0),
                })

                ## Push to API
                _sale_order_id = item['id'] if item['id'] else ''
                _date_order = item['date_order'] if item['date_order'] else ''
                _total_amount = item['amount_untaxed'] if item['amount_untaxed'] else 0
                _tax_amount = item['amount_tax'] if item['amount_tax'] else 0
                _grand_total_amount = item['amount_total'] if item['amount_total'] else 0
                _confirmation_date = datetime.now().replace(microsecond=0)
                _online_sale_order_id = item['online_sale_order_id'] if item['online_sale_order_id'] else ''
                _trace_time = datetime.now().replace(microsecond=0)
                
                if _online_sale_order_id:
                    url = base_url + str("/object/sale.order/" + str(_online_sale_order_id) + "?vals={"
                        + "'state':'sale'"
                        + ",'date_order':'" + str(_date_order) + "'"
                        + ",'total_amount':" + str(_total_amount)
                        + ",'tax_amount':" + str(_tax_amount)
                        + ",'grand_total_amount':" + str(_grand_total_amount)
                        + ",'confirmation_date':'" + str(_confirmation_date) + "'"
                        + ",'trace_time':'" + str(_trace_time) + "'"
                        + "}"
                    )
                    response = requests.put(url, data="")
                    
                    if response:
                        if response.status_code == 200 or response.status_code == 201:
                            subitems = self.env['sale.order.line'].search([('order_id','=',_sale_order_id)])
                            if subitems:
                                for subitem in subitems:
                                    __online_sale_order_line_id = subitem['online_sale_order_line_id'] if subitem['online_sale_order_line_id'] else ''
                                    __box_quantity = subitem['box_quantity'] if subitem['box_quantity'] else 0
                                    __pcs_quantity = subitem['pcs_quantity'] if subitem['pcs_quantity'] else 0
                                    __product_uom_qty = subitem['product_uom_qty'] if subitem['product_uom_qty'] else 0
                                    __discount = subitem['discount'] if subitem['discount'] else 0
                                    __box_price = subitem['box_price'] if subitem['box_price'] else 0
                                    __mrp_amount = subitem['mrp_amount'] if subitem['mrp_amount'] else 0
                                    __price_unit = subitem['price_unit'] if subitem['price_unit'] else 0
                                    __price_reduce_taxexcl = subitem['price_reduce_taxexcl'] if subitem['price_reduce_taxexcl'] else 0
                                    __price_tax = subitem['price_tax'] if subitem['price_tax'] else 0
                                    __price_reduce = subitem['price_reduce'] if subitem['price_reduce'] else 0
                                    __price_reduce_taxinc = subitem['price_reduce_taxinc'] if subitem['price_reduce_taxinc'] else 0
                                    __price_subtotal = subitem['price_subtotal'] if subitem['price_subtotal'] else 0
                                    __price_total = subitem['price_total'] if subitem['price_total'] else 0
                                    __qty_to_invoice = subitem['qty_to_invoice'] if subitem['qty_to_invoice'] else 0
                                    __qty_delivered = subitem['qty_delivered'] if subitem['qty_delivered'] else 0
                                    __qty_invoiced = subitem['qty_invoiced'] if subitem['qty_invoiced'] else 0
                                    __state = subitem['state'] if subitem['state'] else ''

                                    suburl = base_url + str("/object/sale.order.line/" + str(__online_sale_order_line_id) + "?vals={"
                                        + "'box_quantity':" + str(__box_quantity)
                                        + ",'pcs_quantity':" + str(__pcs_quantity)
                                        + ",'product_uom_qty':" + str(__product_uom_qty)
                                        + ",'discount':" + str(__discount)
                                        + ",'box_price':" + str(__box_price)
                                        + ",'mrp_amount':" + str(__mrp_amount)
                                        + ",'price_unit':" + str(__price_unit)
                                        + ",'price_reduce_taxexcl':" + str(__price_reduce_taxexcl)
                                        + ",'price_tax':" + str(__price_tax)
                                        + ",'price_reduce':" + str(__price_reduce)
                                        + ",'price_reduce_taxinc':" + str(__price_reduce_taxinc)
                                        + ",'price_subtotal':" + str(__price_subtotal)
                                        + ",'price_subtotal_new':" + str(__price_subtotal)
                                        + ",'price_total':" + str(__price_total)
                                        + ",'price_total_new':" + str(__price_total)
                                        + ",'qty_to_invoice':" + str(__qty_to_invoice)
                                        + ",'qty_delivered':" + str(__qty_delivered)
                                        + ",'qty_invoiced':" + str(__qty_invoiced)
                                        + ",'state':'" + str(__state) + "'"
                                        + "}"
                                    )
                                    subresponse = requests.put(suburl, data="")

                                    # if subresponse:
                                    #     if subresponse.status_code == 200 or subresponse.status_code == 201:
                                    #         pass
                                    #     else:
                                    #         raise UserError(str(subresponse) + "\nFailed to Sync Sale Order Line(s).")
                                    # else:
                                    #     raise UserError(str(subresponse) + "\nFailed to Sync Sale Order Line(s).")

                            ## Update 'web_ref_id'
                            # item.write({
                            #     'web_ref_id': 'Synced',
                            # })
                            query = """ UPDATE sale_order
                                        SET web_ref_id = 'Synced'
                                        WHERE id = %s; """
                            params = (str(item['id']),)
                            self.env.cr.execute(query, params)
                    #     else:
                    #         raise UserError(str(response) + "\nFailed to Sync Sale Order(s).")
                    # else:
                    #     raise UserError(str(response) + "\nFailed to Sync Sale Order(s).")
            
            if isReload:
                # msg = str(len(items)) + " item(s) synced successfully."
                return {'type': 'ir.actions.client', 'tag': 'reload'}
        else:
            if isReload:
                raise UserError("No data found to sync.")


    @api.multi
    def sync_branch_push(self, isReload):
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
        
        url = base_url + "/object/res.company?fields=['id','name']&order='id'&limit=1"
        response = requests.get(url, data="")
        _company_id = 1
        if response.status_code == 200 or response.status_code == 201: _company_id = json.loads(json.dumps(response.json()['res.company']))[0]['id']

        items = self.env['res.branch'].search([('web_ref_id','!=','Synced')])
        if items:
            for item in items:
                ## Check Record is Update or Not & Add Clause/Condition
                condition = ""
                # _is_update = item['is_update'] if item['is_update'] else False
                _online_branch_id = item['online_branch_id'] if item['online_branch_id'] else ''
                if _online_branch_id: condition = "/" + str(_online_branch_id)

                ## Push to API
                _name = item['name'] if item['name'] else ''
                _address = item['address'] if item['address'] else ''
                _telephone_no = item['telephone_no'] if item['telephone_no'] else ''
                
                url = base_url + str("/object/res.branch" + condition + "?vals={"
                    + "'name':'" + _name + "'"
                    + ",'address':'" + str(_address) + "'"
                    + ",'telephone_no':'" + str(_telephone_no) + "'"
                    + ",'company_id':" + str(_company_id)
                    + "}"
                )
                response = ""
                if _online_branch_id:
                    response = requests.put(url, data="")
                else:
                    response = requests.post(url, data="")
                
                if response:
                    if response.status_code == 200 or response.status_code == 201:
                        _branch_id = json.loads(json.dumps(response.json()['res.branch']))[0]['id']
                        
                        ## Update 'web_ref_id'
                        # item.write({
                        #     'web_ref_id': 'Synced',
                        #     'online_branch_id': _branch_id,
                        # })
                        item.online_branch_id = _branch_id
                        query = """ UPDATE res_branch
                                    SET web_ref_id = 'Synced', is_update = 'False', online_branch_id = %s
                                    WHERE id = %s; """
                        params = (str(_branch_id),str(item['id']),)
                        self.env.cr.execute(query, params)
                #     else:
                #         raise UserError(str(response) + "\nFailed to Sync Market(s).")
                # else:
                #     raise UserError(str(response) + "\nFailed to Sync Market(s).")
            
            if isReload:
                # msg = str(len(items)) + " item(s) synced successfully."
                return {'type': 'ir.actions.client', 'tag': 'reload'}
        else:
            if isReload:
                raise UserError("No data found to sync.")


    @api.multi
    def sync_users_push(self, isReload):
        user_default_password = '123456'
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            user_default_password = synchronizer_configuration['user_default_password']
        
        url = base_url + "/object/res.company?fields=['id','name']&order='id'&limit=1"
        response = requests.get(url, data="")
        _company_id = 1
        if response.status_code == 200 or response.status_code == 201: _company_id = json.loads(json.dumps(response.json()['res.company']))[0]['id']
        
        items = self.env['res.users'].search([('web_ref_id','!=','Synced'),('active','=',True),('id','!=',1)])
        if items:
            for item in items:
                ## Check Record is Update or Not & Add Clause/Condition
                condition = ""
                # _is_update = item['is_update'] if item['is_update'] else False
                _online_user_id = item['online_user_id'] if item['online_user_id'] else ''
                if _online_user_id: condition = "/" + str(_online_user_id)

                ## Push to API
                _name = item['name'] if item['name'] else ''
                _login = item['login'] if item['login'] else ''
                _password = user_default_password
                _share = item['share'] if item['share'] else ''
                _signature = item['signature'] if item['signature'] else ''
                _pos_security_pin = item['pos_security_pin'] if item['pos_security_pin'] else ''
                _branch_id = item['branch_id'].id if item['branch_id'] else "''"
                _trace_time = item['trace_time'] if item['trace_time'] else ''

                if _branch_id and _branch_id != "''":
                    # branch = self.env['res.branch'].browse(_branch_id)
                    # if branch: _branch_id = branch.online_branch_id
                    _branch_id = item.branch_id.online_branch_id
                
                url = base_url + str("/object/res.users" + condition + "?vals={"
                    + "'name':'" + str(_name) + "'"
                    + ",'login':'" + str(_login) + "'"
                    + ",'password':'" + str(_password) + "'"
                    + ",'share':'" + str(_share) + "'"
                    + ",'signature':'" + str(_signature) + "'"
                    + ",'pos_security_pin':'" + str(_pos_security_pin) + "'"
                    + ",'company_id':" + str(_company_id)
                    + ",'branch_id':" + str(_branch_id)
                    + ",'trace_time':'" + str(_trace_time) + "'"
                    + "}"
                )
                response = ""
                if _online_user_id:
                    url = base_url + str("/object/res.users" + condition + "?vals={"
                        + "'name':'" + str(_name) + "'"
                        + ",'login':'" + str(_login) + "'"
                        + ",'share':'" + str(_share) + "'"
                        + ",'signature':'" + str(_signature) + "'"
                        + ",'pos_security_pin':'" + str(_pos_security_pin) + "'"
                        + ",'company_id':" + str(_company_id)
                        + ",'branch_id':" + str(_branch_id)
                        + ",'trace_time':'" + str(_trace_time) + "'"
                        + "}"
                    )
                    response = requests.put(url, data="")
                else:
                    response = requests.post(url, data="")
                
                if response:
                    if response.status_code == 200 or response.status_code == 201:
                        __user_id = json.loads(json.dumps(response.json()['res.users']))[0]['id']

                        ## Update 'web_ref_id'
                        # item.write({
                        #     'web_ref_id': 'Synced',
                        # })
                        query = """ UPDATE res_users
                                    SET web_ref_id = 'Synced', online_user_id = %s
                                    WHERE id = %s; """
                        #, is_update = 'False'
                        params = (str(__user_id),str(item['id']),)
                        self.env.cr.execute(query, params)
                #     else:
                #         raise UserError(str(response) + "\nFailed to Sync User(s).")
                # else:
                #     raise UserError(str(response) + "\nFailed to Sync User(s).")
            
            if isReload:
                # msg = str(len(items)) + " item(s) synced successfully."
                return {'type': 'ir.actions.client', 'tag': 'reload'}
        else:
            if isReload:
                raise UserError("No data found to sync.")

