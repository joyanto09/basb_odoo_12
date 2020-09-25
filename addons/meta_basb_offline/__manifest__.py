# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Basb Offline',
    'summary': """BASB Data Sync Module""",
    'version': '10.0.1.0',
    'author': 'Metamorphosis',
    'company': 'Metamorphosis Limited',
    'website': 'metamorphosis.com.bd',
    'category': 'Tools',
    'sequence': 1,
    'depends': ['base', 'contacts', 'stock'],
    'data': [
        'data/synchronizer_configuration.xml',
        'views/synchronizer_configuration_view.xml',
        'views/synchronizer_wizard_view.xml',
        'views/synchronizer_dependency_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'icon': "/meta_basb_offline/static/description/icon.png",
    "images": ["/static/description/banner.png"],
}
