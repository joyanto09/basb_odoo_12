from odoo import api, models, fields, _
from odoo.exceptions import UserError
import datetime
from dateutil import parser
from passlib.context import CryptContext
from  datetime import datetime
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    personal_number = fields.Char('Personal Number')
    national_identification = fields.Char('NID')

    date_of_birth = fields.Date("Date of Birth")
    date_of_birth_string = fields.Char("Date of Birth")
    date_of_joining = fields.Date("Date of Joining")
    date_of_retirement = fields.Date("Date of Retirement")
    age = fields.Char(string="Age", compute="_compute_age")
    
    living_status = fields.Selection([
        ('alive', 'জীবিত'),
        ('dead', 'মৃত'),
    ], 'Status',  default='alive')
    
    # sex_status = fields.Selection([
    #     ('male', 'Male'),
    #     ('female', 'Female'),
    # ], 'Sex')
    gander_status = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], 'Gender', default='')
    
    special_child = fields.Boolean(string="Special Child")
    user_password = fields.Char(string="Password")
    special_access_for_purchase = fields.Boolean(string="Allow Access for Purchase")
    password_invisible = fields.Boolean(string="status password")
    blood_group = fields.Char(string="Blood Group")
    
    # Sync fields
    dasb = fields.Many2one('basb.dasb', string='DASB', default=False)
    rank_id = fields.Many2one('basb.rank', string='Rank', default=False)
    service = fields.Many2one('basb.service', string='Service', default=False)
    permanent_address = fields.Many2one('basb.district', string='District', default=False)  
    relation = fields.Many2one('basb.relation', string='Relation', default=False)
    sync_ref_id = fields.Char('Sync Ref ID')

    beneficiary_number = fields.Char(string='Beneficiary Of', related='parent_id.personal_number')
    
    

    @api.model
    def create(self,values):
        
        res = super(ResPartner,self).create(values)
        
        if 'relation' in values.keys() or 'parent_id' in values.keys():
            
            if res.relation.sync_ref_id in ['Spouse']:
                is_exist = self.env['res.partner'].search([('relation.sync_ref_id','in',['Spouse']),('parent_id','=',res.parent_id.id)])
                if len(is_exist) > 1:
                    raise UserError(_(str(res.parent_id.name) + " can have only one Spouse as dependent."))
            
            if res.relation.sync_ref_id in ['Son','Daughter']:
                is_exist = self.env['res.partner'].search([('relation.sync_ref_id','in',['Son','Daughter']),('parent_id','=',res.parent_id.id)])
                if len(is_exist) > 3:
                    raise UserError(_(str(res.parent_id.name) + " can have only 3 child as dependent."))
        return res
    

    @api.multi
    def write(self,values):
        
        if 'living_status' in values.keys() and values['living_status'] == 'dead':
            values['active'] = False
        
        res = super(ResPartner,self).write(values)
        
        if 'relation' in values.keys() or 'parent_id' in values.keys():
            
            if self.relation.sync_ref_id in ['Spouse']:
                is_exist = self.env['res.partner'].search([('relation.sync_ref_id','in',['Spouse']),('parent_id','=',self.parent_id.id)])
                if len(is_exist) > 1:
                    raise UserError(_(str(self.parent_id.name) + " can have only one Spouse as dependent."))
            
            if self.relation.sync_ref_id in ['Son','Daughter']:
                is_exist = self.env['res.partner'].search([('relation.sync_ref_id','in',['Son','Daughter']),('parent_id','=',self.parent_id.id)])
                if len(is_exist) > 3:
                    raise UserError(_(str(self.parent_id.name) + " can have only 3 child as dependent."))
        
        return res


    @api.multi
    def update_contact_information(self):
        all_contacts = self.env['res.partner'].search([('relation.sync_ref_id','in',['Son','Daughter']),('special_child','=',False)])
        for contact in all_contacts:
            today = fields.date.today()
            dtob = contact.date_of_birth
            age = today.year - dtob.year - ((today.month, today.day) < (dtob.month, dtob.day))
            if age>18:
                contact.active = False


    @api.onchange('special_access_for_purchase')
    def onchange_special_access_for_purchase(self):
        self.password_invisible = self.special_access_for_purchase


    @api.multi
    def allow_special_purchase(self):
        if self.user_password:
            self.env.cr.execute(
                "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                [self.env.user.id]
            )
            [hashed] = self.env.cr.fetchone()
            valid, replacement = self.env.user._crypt_context()\
                .verify_and_update(self.user_password, hashed)

            if not valid:
                self.special_access_for_purchase = False
                self.password_invisible = False
                self.user_password = ""
            else:
                self.password_invisible = False
                self.user_password = ""
        else:
            raise UserError("Please Enter Your password.")
        pass
    
    #Calculate Age
    @api.multi
    @api.depends('date_of_birth')
    def _compute_age(self):
        for emp in self:
            age = relativedelta(datetime.now().date(), fields.Datetime.from_string(emp.date_of_birth)).years
            emp.age = str(age) + " Years"



    # age = fields.Char(string="Age", compute="_compute_age")