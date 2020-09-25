
from odoo import models, api, fields
from datetime import datetime, date

class Configuration(models.Model):
    """In this class the model pos.config is inherited
    to add a new boolean field in the settings of
    point of sale which is used to make enable/disable
    multiple order note in pos interface"""

    _inherit = 'pos.config'


    pos_owner_ids = fields.Many2many('res.users', string="POS Owner")
    note_config = fields.Boolean(string='Order Line Note',
                                 help='Allow to write internal note in POS interface',
                                 default=True)
    iface_orderline_notes = fields.Boolean(string='Orderline Notes',
                                           help='Allow custom notes on Orderlines.',
                                           default=False, compute='_compute_iface_orderline_notes',
                                           readonly=False)

    @api.multi
    def _compute_iface_orderline_notes(self):
        """This is the compute function to disable
        the existing single order note facility
        in the point of sale interface"""
        if self.note_config:
            self.iface_orderline_notes = False

    @api.onchange('note_config')
    @api.depends('note_config')
    def _onchange_note_config(self):
        """This is the onchange function to disable/enable
        the existing single order note facility
            in the point of sale interface"""
        if self.note_config:
            self.iface_orderline_notes = False
        if not self.note_config:
            self.iface_orderline_notes = True

    @api.model
    def create(self, values):
        res = super(Configuration, self).create(values)
        res.module_account = True
        return res


class DiseasePurchaseDate(models.Model):
    _name = 'disease.purchase.date'

    last_purchase_date = fields.Date(string='Last Purchase Date')
    disease_id = fields.Many2one('res.partner.category', string="Disease")
    partner_id = fields.Many2one('res.partner', string="Partner")


class ProductPurchaseDate(models.Model):
    _name = 'product.purchase.date'

    last_purchase_date = fields.Date(string='Last Purchase Date')
    product_id = fields.Many2one('product.product', string="Product")
    partner_id = fields.Many2one('res.partner', string="Partner")


class POSOrderLine(models.Model):
    _inherit = 'pos.order.line'

    note = fields.Char(string="Chronic Disease")


class POSOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self, values):
        order = super(POSOrder, self).create(values)
        order.partner_id.last_purchase_date = date.today()
        diseases_list = list()
        diseases = ""
        for line in order.lines:
            if line.note:
                line_note = str(line.note)
                notes = line_note.split(', ')
                print (notes)
                for note in notes:
                    if note not in diseases_list:
                        if len(diseases_list)>0:
                            diseases = diseases + ", "
                        diseases_list.append(note)
                        diseases = diseases + note

                        dis_id = self.env['res.partner.category'].search([('name','ilike',note)])
                        existing_record_id = self.env['disease.purchase.date'].search([
                            ('partner_id','=',order.partner_id.id),
                            ('disease_id','=',dis_id.id)])
                        if existing_record_id:
                            existing_record_id.last_purchase_date = date.today()
                        else:
                            self.env['disease.purchase.date'].create({
                                'last_purchase_date': date.today(),
                                'partner_id': order.partner_id.id,
                                'disease_id': dis_id.id,
                            })
            else:
                existing_record_id = self.env['product.purchase.date'].search([
                    ('partner_id','=',order.partner_id.id),
                    ('product_id','=',line.product_id.id)])
                if existing_record_id:
                    existing_record_id.last_purchase_date = date.today()
                else:
                    self.env['product.purchase.date'].create({
                        'last_purchase_date': date.today(),
                        'partner_id': order.partner_id.id,
                        'product_id': line.product_id.id,
                    })

        order.partner_id.last_purchase_diseases = diseases
        order.partner_id.special_access_for_purchase = False
        order.partner_id.password_invisible = False

        return order



    
    