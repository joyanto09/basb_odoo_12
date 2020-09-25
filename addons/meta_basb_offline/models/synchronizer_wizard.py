# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, except_orm, UserError
from odoo.osv import expression
import requests
import json
import traceback
#import urllib2
import sys
#reload(sys)
#sys.setdefaultencoding('utf8')


base_url = 'http://127.0.0.1:8069/restapi/1.0'


class InventorySynchronizerWizard(models.Model):
    
    _name = "inventory.synchronizer.wizard"
    _description = 'Inventory Synchronizer Wizard'

    sync_type = fields.Selection(
        string = 'Sync Type',
        selection = [
            ('stock', 'Stock')
        ],
        default = 'stock'
    )
    
    dispensary = fields.Many2one("stock.warehouse", string="Dispensary", required=True)
    year = fields.Selection(
        string="Year",
        required=True,
        selection = [
            ('2019', '2019'),
            ('2020', '2020'),
            ('2021', '2021'),
            ('2022', '2022')
        ]
    )
    quarter = fields.Selection(
        string="Quarter",
        required=True,
        selection = [
            ('QE-March', 'QE-March'),
            ('QE-June', 'QE-June'),
            ('QE-September', 'QE-September'),
            ('QE-December', 'QE-December')
        ]
    )
   
    @api.multi
    def sync(self):
        internet_connectivity = True #self.check_internet_connectivity()
        if not internet_connectivity:
            raise UserError("There is no internet connection.")
        else:
            #self.ensure_one()
            _company_id = self.env.user.company_id.id
            _sync_type = self.sync_type
            
            if _sync_type == "stock":
                self.sync_stock_push(True)
            
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        
    @api.multi
    def sync_stock_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-medical-medicine-stock?dispensary=" + self.dispensary.name + "&quarter=" + self.quarter + "&year=" + self.year
        response = requests.get(url, data="", stream=True, timeout=300 )

        if response:
            if response.status_code == 200 or response.status_code == 201:
                
                count = json.loads(json.dumps(response.json()['count']))                      
                items = json.loads(json.dumps(response.json()['data']))         
                _sync_ref_id = json.loads(json.dumps(response.json()['requisition_id']))
                _transfer_date = json.loads(json.dumps(response.json()['created_at']))
            
                operation_barcode = self.dispensary.code + '-RECEIPTS'
                _operation_type = self.env['stock.picking.type'].search([('barcode','=',operation_barcode),('warehouse_id','=',self.dispensary.id)])                  
                if not _operation_type: raise UserError("No operation type found to sync.")
                        
                _location_id = self.env['stock.location'].search([('usage','=','supplier')])
                if not _location_id: raise UserError("No source location found to sync.")
                
                destination_barcode = self.dispensary.code + '-STOCK'
                _location_dest_id = self.env['stock.location'].search([('barcode','=',destination_barcode)])
                if not _location_dest_id: raise UserError("No destination location found to sync.")
                
                _product_uom_id = self.env['uom.uom'].search([('name','=','Unit(s)')])
                if not _product_uom_id: raise UserError("No product unit found to sync.")
                
                if not _transfer_date: _transfer_date = None  
                else: _transfer_date = datetime.datetime.strptime(_transfer_date, '%Y-%m-%d %H:%M:%S')
                
                if count > 0:
                    
                    update_record = self.env['stock.picking'].search([('sync_ref_id','=',_sync_ref_id)])

                    if not update_record:
                        
                        record = self.env['stock.picking'].create({
                            'name': self.dispensary.code + '/' + self.year + '/' + self.quarter,
                            'picking_type_id': _operation_type.id,
                            'location_id': _location_id.id,
                            'location_dest_id': _location_dest_id.id,
                            'sync_ref_id': str(_sync_ref_id),
                            'transfer_date': _transfer_date
                        })
                        
                        for item in items:
                            
                            _stock_qty = item['receive_amount'] if item['receive_amount'] else ''

                            product_sync_ref_id = item['medicine_id'] if item['medicine_id'] else ''
                            _product_id = self.env['product.template'].search([('sync_ref_id','=',product_sync_ref_id)])
                            if not _product_id: raise UserError("No product found to sync.") 
                                    
                            self.env['stock.move'].create({
                                'picking_id': record.id,
                                'name': _product_id.name,
                                'product_id': _product_id.product_variant_id.id,
                                'product_uom_qty': _stock_qty,
                                'product_uom': _product_uom_id.id,
                                'location_id': _location_id.id,
                                'location_dest_id': _location_dest_id.id,
                                'date_expected': _transfer_date
                            })   
                            
                        # mark to do
                        record.action_confirm()        

                        # validate
                        #record.button_validate()
                                 
                        if isReload:
                            return {'type': 'ir.actions.client', 'tag': 'reload'}
                        
                    else:
                        if isReload:
                            raise UserError("No data found to sync or already synced.")
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")     


class SynchronizerWizard(models.Model):
    
    _name = "synchronizer.wizard"
    _description = 'Synchronizer Wizard'

    sync_type = fields.Selection(
        string = 'Sync Type',
        selection = [
            ('all', 'Serviceman'),
            ('serviceman_family', 'Serviceman Family'),
            ('medicine', 'Medicines') #('stock', 'Stock')
        ],
        default = 'all'
    )
    
    dispensary = fields.Many2one("stock.warehouse", string="Dispensary")
    year = fields.Selection(
        string="Year",
        selection = [
            ('2019', '2019'),
            ('2020', '2020'),
            ('2021', '2021'),
            ('2022', '2022')
        ]
    )
    quarter = fields.Selection(
        string="Quarter",
        selection = [
            ('QE-March', 'QE-March'),
            ('QE-June', 'QE-June'),
            ('QE-September', 'QE-September'),
            ('QE-December', 'QE-December')
        ]
    )
   

    @api.multi
    def sync(self):
        internet_connectivity = True #self.check_internet_connectivity()
        if not internet_connectivity:
            raise UserError("There is no internet connection.")
        else:
            #self.ensure_one()
            _company_id = self.env.user.company_id.id
            _sync_type = self.sync_type
        
            if _sync_type == "all":
                self.sync_dasb_push(False)
                self.sync_rank_push(False)
                self.sync_service_push(False)
                self.sync_district_push(False)
                self.sync_serviceman_push(False)
            elif _sync_type == "serviceman_family":
                self.sync_relation_push(False)
                self.sync_serviceman_family_push(False)
            elif _sync_type == "medicine":
                self.sync_product_push(False)
            elif _sync_type == "stock":
                self.sync_stock_push(False)

            return {'type': 'ir.actions.client', 'tag': 'reload'}


    @api.multi
    def serviceman_sync(self):
        self.sync_dasb_push(False)
        self.sync_rank_push(False)
        self.sync_service_push(False)
        self.sync_district_push(False)
        self.sync_serviceman_push(False)         
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    @api.multi
    def servicemanfamily_sync(self):
        self.sync_relation_push(False)
        self.sync_serviceman_family_push(False)       
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    @api.multi
    def product_sync(self):
        self.sync_product_push(True)      
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    # @api.multi
    # def check_internet_connectivity(self):
    #     try:
    #         urllib2.urlopen('http://216.58.200.142', timeout=1)
    #         return True
    #     except urllib2.URLError as err:
    #         return False

            
    @api.multi
    def sync_dasb_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-offices/type?office_type=dasb"
        response = requests.get(url, data="")

        if response:
            if response.status_code == 200 or response.status_code == 201:
                items = json.loads(json.dumps(response.json()['data']))
                if items:
                    for item in items:
                        
                        _sync_ref_id = item['id'] if item['id'] else ''
                        _name = item['name'] if item['name'] else ''

                        if _sync_ref_id:
                            is_exist = self.env['basb.dasb'].search([('sync_ref_id','=',_sync_ref_id)])
                            
                            if is_exist:
                                query = """ UPDATE basb_dasb
                                        SET name=%s 
                                        WHERE sync_ref_id=%s; """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)
                            else:
                                query = """ INSERT INTO basb_dasb
                                        (name, sync_ref_id)
                                        VALUES(%s, %s) """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)

                    if isReload:
                        return {'type': 'ir.actions.client', 'tag': 'reload'}
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")
            
            
    @api.multi
    def sync_rank_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-ranks"
        response = requests.get(url, data="")

        if response:
            if response.status_code == 200 or response.status_code == 201:
                items = json.loads(json.dumps(response.json()['data']))
                if items:
                    for item in items:
                        
                        _sync_ref_id = item['id'] if item['id'] else ''
                        _name = item['bn_name'] if item['bn_name'] else ''

                        if _sync_ref_id:
                            is_exist = self.env['basb.rank'].search([('sync_ref_id','=',_sync_ref_id)])
                            
                            if is_exist:
                                query = """ UPDATE basb_rank
                                        SET name=%s 
                                        WHERE sync_ref_id=%s; """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)
                            else:
                                query = """ INSERT INTO basb_rank
                                        (name, sync_ref_id)
                                        VALUES(%s, %s) """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)

                    if isReload:
                        return {'type': 'ir.actions.client', 'tag': 'reload'}
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")
            
    
    @api.multi
    def sync_service_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-services"
        response = requests.get(url, data="")

        if response:
            if response.status_code == 200 or response.status_code == 201:
                items = json.loads(json.dumps(response.json()['data']))
                if items:
                    for item in items:
                        
                        _sync_ref_id = item['id'] if item['id'] else ''
                        _name = item['bn_name'] if item['bn_name'] else ''

                        if _sync_ref_id:
                            is_exist = self.env['basb.service'].search([('sync_ref_id','=',_sync_ref_id)])
                            
                            if is_exist:
                                query = """ UPDATE basb_service
                                        SET name=%s 
                                        WHERE sync_ref_id=%s; """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)
                            else:
                                query = """ INSERT INTO basb_service
                                        (name, sync_ref_id)
                                        VALUES(%s, %s) """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)

                    if isReload:
                        return {'type': 'ir.actions.client', 'tag': 'reload'}
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")
            
            
    @api.multi
    def sync_district_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-districts"
        response = requests.get(url, data="")

        if response:
            if response.status_code == 200 or response.status_code == 201:
                items = json.loads(json.dumps(response.json()['data']))
                if items:
                    for item in items:
                        
                        _sync_ref_id = item['id'] if item['id'] else ''
                        _name = item['bn_name'] if item['bn_name'] else ''

                        if _sync_ref_id:
                            is_exist = self.env['basb.district'].search([('sync_ref_id','=',_sync_ref_id)])
                            
                            if is_exist:
                                query = """ UPDATE basb_district
                                        SET name=%s 
                                        WHERE sync_ref_id=%s; """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)
                            else:
                                query = """ INSERT INTO basb_district
                                        (name, sync_ref_id)
                                        VALUES(%s, %s) """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)

                    if isReload:
                        return {'type': 'ir.actions.client', 'tag': 'reload'}
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")


    @api.multi
    def sync_relation_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-relations"
        response = requests.get(url, data="")

        if response:
            if response.status_code == 200 or response.status_code == 201:
                items = json.loads(json.dumps(response.json()['data']))
                if items:
                    for item in items:
                        
                        _sync_ref_id = item['id'] if item['id'] else ''
                        _name = item['bn_name'] if item['bn_name'] else ''

                        if _sync_ref_id:
                            is_exist = self.env['basb.relation'].search([('sync_ref_id','=',_sync_ref_id)])
                            
                            if is_exist:
                                query = """ UPDATE basb_relation
                                        SET name=%s 
                                        WHERE sync_ref_id=%s; """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)
                            else:
                                query = """ INSERT INTO basb_relation
                                        (name, sync_ref_id)
                                        VALUES(%s, %s) """
                                params = (_name, str(_sync_ref_id),)
                                self.env.cr.execute(query, params)

                    if isReload:
                        return {'type': 'ir.actions.client', 'tag': 'reload'}
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")


    @api.multi
    def sync_serviceman_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-ex-serviceman"
        response = requests.get(url, data="")

        if response:
            if response.status_code == 200 or response.status_code == 201:
                items = json.loads(json.dumps(response.json()['data']))
                if items:
                    i = 0 
                    for item in items:
                        
                        _sync_ref_id = item['id'] if item['id'] else ''
                        _name = item['name'] if item['name'] else 'N/A'
                        _phone = item['mobile_number'] if item['mobile_number'] else ''
                        _email = item['email'] if item['email'] else ''
                        _blood_group = item['blood_group'] if item['blood_group'] else ''
                        _personal_number = item['identity_number'] if item['identity_number'] else ''
                        
                        dasb_sync_ref_id = item['dasb_id'] if item['dasb_id'] else ''
                        _dasb_id = self.env['basb.dasb'].search([('sync_ref_id','=',dasb_sync_ref_id)]).id
                        if _dasb_id == False: _dasb_id = None 
                    
                        rank_sync_ref_id = item['rank_id'] if item['rank_id'] else ''
                        _rank_id = self.env['basb.rank'].search([('sync_ref_id','=',rank_sync_ref_id)]).id
                        if _rank_id == False: _rank_id = None 
                        
                        service_sync_ref_id = item['service_id'] if item['service_id'] else ''
                        _service_id = self.env['basb.service'].search([('sync_ref_id','=',service_sync_ref_id)]).id
                        if _service_id == False: _service_id = None 
                        
                        district_sync_ref_id = item['district_id'] if item['district_id'] else ''
                        _district_id = self.env['basb.district'].search([('sync_ref_id','=',district_sync_ref_id)]).id
                        if _district_id == False: _district_id = None 

                        _date_of_birth = None
                        try:
                            _date_of_birth = item['date_of_birth'] if item['date_of_birth'] else ''
                            if not _date_of_birth: _date_of_birth = None  
                            else: _date_of_birth = datetime.datetime.strptime(_date_of_birth, '%Y-%M-%d')
                        except Exception:
                            _date_of_birth = None
                            
                        _date_of_joining = None
                        try:
                            _date_of_joining = item['date_of_joining'] if item['date_of_joining'] else ''
                            if not _date_of_joining: _date_of_joining = None  
                            else: _date_of_joining = datetime.datetime.strptime(_date_of_joining, '%Y-%M-%d')
                        except Exception:
                            _date_of_joining = None
                            
                        _date_of_retirement = None
                        try:
                            _date_of_retirement = item['date_of_retirement'] if item['date_of_retirement'] else ''
                            if not _date_of_retirement: _date_of_retirement = None  
                            else: _date_of_retirement = datetime.datetime.strptime(_date_of_retirement, '%Y-%M-%d')
                        except Exception:
                            _date_of_retirement = None
                
                        dead = item['dead'] if item['dead'] else ''
                        _status = 'alive'
                        _active = True
                        _customer = True
                        if dead == 1: 
                            _status = 'dead' 
                            _active = True
                            _customer = False
                              
                        sex = item['gender_id'] if item['gender_id'] else '' 
                        _sex_status = ''
                        if sex == 'Male':
                            _sex_status = 'male'
                        elif sex == 'Female':
                            _sex_status = 'female'
                        
                            
                        if _sync_ref_id:
                            
                            '''
                               
                            update_record = self.env['res.partner'].search([('sync_ref_id','=',_sync_ref_id)])      
                                                                
                            if update_record:
                                update_record.write({
                                    'name': _name,
                                    'rank_id': _rank_id,
                                    'service': _service_id,
                                    'permanent_address': _district_id,
                                    'phone': _phone,
                                    'email': _email,
                                    'blood_group': _blood_group,
                                    'personal_number': _personal_number,
                                    'date_of_birth': _date_of_birth,
                                    'date_of_joining': _date_of_joining,
                                    'date_of_retirement': _date_of_retirement,
                                    'living_status': _status
                                })
                            else:
                                record = self.env['res.partner'].create({
                                    'name': _name,
                                    'sync_ref_id': str(_sync_ref_id),
                                    'dasb': _dasb_id,
                                    'rank_id': _rank_id,
                                    'service': _service_id,
                                    'permanent_address': _district_id,
                                    'phone': _phone,
                                    'email': _email,
                                    'blood_group': _blood_group,
                                    'personal_number': _personal_number,
                                    'date_of_birth': _date_of_birth,
                                    'date_of_joining': _date_of_joining,
                                    'date_of_retirement': _date_of_retirement,
                                    'living_status': _status,
                                    'customer': True, 
                                    'active': True
                                })
                            
                            '''
                            
                            is_exist = self.env['res.partner'].search([('sync_ref_id','=',_sync_ref_id)])

                            if is_exist:
                                try:
                                    query = """ UPDATE res_partner
                                                SET name=%s,
                                                display_name=%s,
                                                rank_id=%s, 
                                                service=%s, 
                                                permanent_address=%s, 
                                                phone=%s, 
                                                email=%s, 
                                                personal_number=%s,
                                                date_of_birth=%s,
                                                date_of_joining=%s, 
                                                date_of_retirement=%s,
                                                living_status=%s,
                                                gander_status=%s,
                                                dasb=%s,
                                                customer=%s,
                                                active=%s
                                                WHERE sync_ref_id=%s """
                                    params = (_name, _name, _rank_id, _service_id, _district_id, _phone, _email, _personal_number, _date_of_birth, _date_of_joining, _date_of_retirement, _status, _sex_status, _dasb_id, _customer, _active, str(_sync_ref_id), )  
                                    self.env.cr.execute(query, params)
                                except Exception:
                                    print("Catch Exception ID: " + str(_sync_ref_id))
                            else:                            # put else
                                try:
                                    query = """ INSERT INTO res_partner
                                            (name, display_name, sync_ref_id, dasb, rank_id, service, permanent_address, phone, email, blood_group, personal_number, date_of_birth, date_of_joining, date_of_retirement, living_status, gander_status, customer, active)
                                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
                                    params = (_name, _name, str(_sync_ref_id), _dasb_id, _rank_id, _service_id, _district_id, _phone, _email, _blood_group, _personal_number, _date_of_birth, _date_of_joining, _date_of_retirement, _status, _sex_status, _customer, _active, )
                                    self.env.cr.execute(query, params)
                                except Exception:
                                    print("Catch Exception ID: " + str(_sync_ref_id))
                                    
                    if isReload:
                        return {'type': 'ir.actions.client', 'tag': 'reload'}
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")
                

    @api.multi
    def sync_serviceman_family_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-ex-serviceman/family"
        response = requests.get(url, data="")

        if response:
            if response.status_code == 200 or response.status_code == 201:
                items = json.loads(json.dumps(response.json()['data']))
                if items:
                    counter = 0
                    for item in items:
                        
                        _sync_ref_id = 'family-' + str(item['id']) if item['id'] else '' 
                        _name = item['name'] if item['name'] else 'N/A'
                        _phone = item['mobile_number'] if item['mobile_number'] else ''
                        _nid = item['nid'] if item['nid'] else ''
                        _occupation = item['occupation'] if item['occupation'] else ''
                        
                        relation_sync_ref_id = item['relation_id'] if item['relation_id'] else ''
                        _relation_id = self.env['basb.relation'].search([('sync_ref_id','=',relation_sync_ref_id)]).id
                        if _relation_id == False: _relation_id = None 
                        
                        serviceman_sync_ref_id = item['serviceman_id'] if item['serviceman_id'] else ''
                        parent = self.env['res.partner'].search([('sync_ref_id','=',serviceman_sync_ref_id)])
                        
                        try:
                            _parent_id = parent.id or False
                        except:
                            _parent_id = parent[0].id or False


                        if _parent_id == False: _parent_id = None 
                        
                        _dasb_id = None 
                        try:
                            _dasb_id = parent.dasb.id or False
                        except:
                            _dasb_id = parent[0].dasb.id or False

                        if _dasb_id == False: _dasb_id = None 

                        _date_of_birth = None
                        try:
                            _date_of_birth = item['date_of_birth'] if item['date_of_birth'] else ''
                            if not _date_of_birth: _date_of_birth = None  
                            else: _date_of_birth = datetime.datetime.strptime(_date_of_birth, '%Y-%M-%d')
                        except Exception:
                            _date_of_birth = None 
                            
                        # dead = item['dead'] if item['dead'] else ''
                        # _status = 'alive'
                        _active = True
                        # if dead == 1: 
                        #     _status = 'dead' 
                        #     _active = False       
                        
                        if _sync_ref_id:
                            
                            '''
                            update_record = self.env['res.partner'].search([('sync_ref_id','=',_sync_ref_id)])      
                            
                            if update_record:
                                update_record.write({
                                    'name': _name,
                                    'phone': _phone,
                                    'national_identification': _nid,
                                    'function': _occupation,
                                    'date_of_birth': _date_of_birth,
                                    'relation': _relation_id,
                                    'parent_id': _parent_id
                                })
                            else:
                                record = self.env['res.partner'].create({
                                    'name': _name,
                                    'sync_ref_id': str(_sync_ref_id),
                                    'phone': _phone,
                                    'national_identification': _nid,
                                    'function': _occupation,
                                    'date_of_birth': _date_of_birth,
                                    'relation': _relation_id,
                                    'parent_id': _parent_id,
                                    'customer': True, 
                                    'active': True, 
                                    'type': 'contact'
                                })
                            
                            '''
                            
                            is_exist = self.env['res.partner'].search([('sync_ref_id','=',_sync_ref_id)])

                            if is_exist:
                                try: 
                                    query = """ UPDATE res_partner
                                                SET name=%s,
                                                display_name=%s,
                                                dasb=%s,
                                                phone=%s, 
                                                national_identification=%s,
                                                function=%s,
                                                date_of_birth=%s,
                                                relation=%s,
                                                parent_id=%s, 
                                                commercial_partner_id=%s
                                                WHERE sync_ref_id=%s """
                                    params = (_name, _name, _dasb_id, _phone, _nid, _occupation, _date_of_birth, _relation_id, _parent_id, _parent_id, str(_sync_ref_id), )  
                                    self.env.cr.execute(query, params)
                                except Exception:
                                    print("Catch Exception ID: " + str(_sync_ref_id))
                            else:
                                try:  
                                    if _sync_ref_id is not None:
                                        query = """ INSERT INTO res_partner
                                                (name, display_name, sync_ref_id, dasb, phone, national_identification, function, date_of_birth, relation, parent_id, commercial_partner_id, customer, active, type)
                                                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, True, %s, 'contact') """
                                        params = (_name, _name, str(_sync_ref_id), _dasb_id, _phone, _nid, _occupation, _date_of_birth, _relation_id, _parent_id, _parent_id, _active, )
                                        self.env.cr.execute(query, params)
                                except Exception:
                                    print("Catch Exception ID: " + str(_sync_ref_id))
                
                    if isReload:
                        return {'type': 'ir.actions.client', 'tag': 'reload'}
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")
            
            
    @api.multi
    def sync_product_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-medical-medicine"
        response = requests.get(url, data="", stream=True, timeout=300)

        if response:
            if response.status_code == 200 or response.status_code == 201:
                items = json.loads(json.dumps(response.json()['data']))
                if items:
                    for item in items:
                        
                        _sync_ref_id = item['id'] if item['id'] else ''
                        _name = item['name'] if item['name'] else ''
                        _code = item['code'] if item['code'] else ''
                                
                        if _sync_ref_id:   
                                                   
                            update_record = self.env['product.template'].search([('sync_ref_id','=',_sync_ref_id)])      
                            
                            if update_record:
                                update_record.write({
                                    'name': _name,
                                    'default_code': _code
                                })
                            else:
                                record = self.env['product.template'].create({
                                    'name': _name,
                                    'default_code': _code,
                                    'sync_ref_id': str(_sync_ref_id),
                                    'type': 'product',
                                    'available_in_pos': True
                                })

                    if isReload:
                        return {'type': 'ir.actions.client', 'tag': 'reload'}
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")
            
    @api.multi
    def sync_stock_push(self, isReload):
        
        synchronizer_configuration = self.env['synchronizer.configuration'].search([('id','=',1)])
        if synchronizer_configuration:
            base_url = synchronizer_configuration['base_url']
            
        url = base_url + "/get-medical-medicine-stock?dispensary=" + self.dispensary.name + "&quarter=" + self.quarter + "&year=" + self.year
        response = requests.get(url, data="")

        if response:
            if response.status_code == 200 or response.status_code == 201:
                
                count = json.loads(json.dumps(response.json()['count']))                      
                items = json.loads(json.dumps(response.json()['data']))         
                _sync_ref_id = json.loads(json.dumps(response.json()['requisition_id']))
                _transfer_date = json.loads(json.dumps(response.json()['created_at']))
            
                _operation_type = self.env['stock.picking.type'].search([('name','=','Receipts'),('warehouse_id','=',self.dispensary.id)])                  
                if not _operation_type: raise UserError("No operation type found to sync.")
                        
                _location_id = self.env['stock.location'].search([('usage','=','supplier')])
                if not _location_id: raise UserError("No source location found to sync.")
                
                _location_dest_id = self.env['stock.location'].search([('name','=',self.dispensary.name)])
                if not _location_dest_id: raise UserError("No destination location found to sync.")
                
                _product_uom_id = self.env['uom.uom'].search([('name','=','Unit(s)')])
                if not _product_uom_id: raise UserError("No product unit found to sync.")
                
                if not _transfer_date: _transfer_date = None  
                else: _transfer_date = datetime.datetime.strptime(_transfer_date, '%Y-%m-%d %H:%M:%S')
                
                if count > 0:
                    
                    update_record = self.env['stock.picking'].search([('sync_ref_id','=',_sync_ref_id)])

                    if not update_record:
                        
                        record = self.env['stock.picking'].create({
                            'name': self.dispensary.code + '/' + self.year + '/' + self.quarter,
                            'picking_type_id': _operation_type.id,
                            'location_id': _location_id.id,
                            'location_dest_id': _location_dest_id.id,
                            'sync_ref_id': str(_sync_ref_id),
                            'transfer_date': _transfer_date
                        })
                        
                        for item in items:
                            
                            _stock_qty = item['receive_amount'] if item['receive_amount'] else ''

                            product_sync_ref_id = item['medicine_id'] if item['medicine_id'] else ''
                            _product_id = self.env['product.template'].search([('sync_ref_id','=',product_sync_ref_id)])
                            if not _product_id: raise UserError("No product found to sync.") 
                                    
                            self.env['stock.move'].create({
                                'picking_id': record.id,
                                'name': _product_id.name,
                                'product_id': _product_id.product_variant_id.id,
                                'product_uom_qty': _stock_qty,
                                'product_uom': _product_uom_id.id,
                                'location_id': _location_id.id,
                                'location_dest_id': _location_dest_id.id
                            })   
                            
                        # mark to do
                        record.action_confirm()        

                        # validate
                        #record.button_validate()
                                 
                        if isReload:
                            return {'type': 'ir.actions.client', 'tag': 'reload'}
                        
                    else:
                        if isReload:
                            raise UserError("No data found to sync or already synced.")
                else:
                    if isReload:
                        raise UserError("No data found to sync.")
        else:
            if isReload:
                raise UserError("No data found to sync.")     
            
            
            
