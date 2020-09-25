{
    'name': 'Web Tours Disabled',
    'summary': 'Hide the animations of the Odoo Web Tours',
    'license': 'AGPL-3',
    'author': 'Metamorphosis',
    'company': 'Metamorphosis Ltd.',
    'maintainer': 'Md. Mehedi Hasan Akash',
    'category': 'Web',
    'version': '1.0.0.0',
    'depends': [
        'web',
        'web_tour',
    ],
    'data': [
        'views/tour_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 1,
}