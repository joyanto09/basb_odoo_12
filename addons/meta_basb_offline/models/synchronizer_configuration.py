# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, except_orm, UserError
import calendar
import math
import re


class SynchronizerConfiguration(models.Model):
    _name = "synchronizer.configuration"
    _description = 'Synchronizer Configuration'
    
    name = fields.Char(string='Name', default='Synchronizer Settings')
    user_default_password = fields.Char(string='User Default Password', required=True, default='123456')
    base_url = fields.Char(string='Base URL', required=True, default='http://127.0.0.1:8069/restapi/1.0')


    @api.multi
    def save(self):
        pass

