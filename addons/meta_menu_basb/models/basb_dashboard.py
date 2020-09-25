from odoo import models, api, fields
from datetime import datetime, date
from odoo.exceptions import UserError

class BasbDashboardMenu(models.Model):
    _name="basb.dashboard.menu"

    name = fields.Char("name")
    header = fields.Char("Header")
    action = fields.Char("Action")
    menu = fields.Char("Menu")
    model = fields.Char("model")
    view = fields.Char("View")

    @api.multi
    def open_ui(self):
        """ open the pos interface """
        self.ensure_one()
        action = self.env.ref(self.action)
        menu = self.env.ref(self.menu)
        url = "/web#action="+str(action.id)+"&amp;model="+self.model+"&amp;view_type="+self.view+"&amp;menu_id="+str(menu.id)
        # raise UserError(url)
        return {
            'type': 'ir.actions.act_url',
            'url':   url,
            'target': 'self',
        }
    
    @api.multi
    def open_ui_from_menu(self, values):
        """ open the pos interface """
        record = self.env['basb.dashboard.menu'].search([('name','=',values)])
        # raise UserError(values)
        action = self.env.ref(record.action)
        menu = self.env.ref(record.menu)
        url = "/web#action="+str(action.id)+"&amp;model="+record.model+"&amp;view_type="+record.view+"&amp;menu_id="+str(menu.id)
        # raise UserError(url)
        return {
            'type': 'ir.actions.act_url',
            'url':   url,
            'target': 'self',
        }