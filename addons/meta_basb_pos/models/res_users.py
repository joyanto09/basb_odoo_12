from odoo import models, api, fields
from datetime import datetime, date


class ResUsers(models.Model):
    _inherit = 'res.users'

    apply_pos = fields.Selection([('none','None'),('all','All'),('custom','Custom')], string="Assigned POS", default='none')
    pos_ids = fields.Many2many('pos.config', string="POS Name")


    @api.model
    def create(self, values):
        user = super(ResUsers, self).create(values)
        if user.apply_pos == 'none':
            all_pos = self.env['pos.config'].search([])
            for pos in all_pos:
                all_users = pos.pos_owner_ids.ids
                if user.id in all_users:
                    all_users.remove(user.id)
                    pos.pos_owner_ids = [[6,0,all_users]]

        elif user.apply_pos == 'all':
            all_pos = self.env['pos.config'].search([])
            for pos in all_pos:
                all_users = pos.pos_owner_ids.ids
                if user.id not in all_users:
                    all_users.append(user.id)
                    pos.pos_owner_ids = [[6,0,all_users]]

        else:
            all_pos = self.env['pos.config'].search([])
            for pos in all_pos:
                if pos.id in user.pos_ids.ids:
                    all_users = pos.pos_owner_ids.ids
                    if user.id not in all_users:
                        all_users.append(user.id)
                        pos.pos_owner_ids = [[6,0,all_users]]
                else:
                    all_users = pos.pos_owner_ids.ids
                    if user.id in all_users:
                        all_users.remove(user.id)
                        pos.pos_owner_ids = [[6,0,all_users]]

        return user

    @api.multi
    def write(self, values):
        res = super(ResUsers, self).write(values)
        if self.apply_pos == 'none':
            all_pos = self.env['pos.config'].search([])
            for pos in all_pos:
                all_users = pos.pos_owner_ids.ids
                if self.id in all_users:
                    all_users.remove(self.id)
                    pos.pos_owner_ids = [[6,0,all_users]]

        elif self.apply_pos == 'all':
            all_pos = self.env['pos.config'].search([])
            for pos in all_pos:
                all_users = pos.pos_owner_ids.ids
                if self.id not in all_users:
                    all_users.append(self.id)
                    pos.pos_owner_ids = [[6,0,all_users]]

        else:
            all_pos = self.env['pos.config'].search([])
            for pos in all_pos:
                if pos.id in self.pos_ids.ids:
                    all_users = pos.pos_owner_ids.ids
                    if self.id not in all_users:
                        all_users.append(self.id)
                        pos.pos_owner_ids = [[6,0,all_users]]
                else:
                    all_users = pos.pos_owner_ids.ids
                    if self.id in all_users:
                        all_users.remove(self.id)
                        pos.pos_owner_ids = [[6,0,all_users]]

        return res