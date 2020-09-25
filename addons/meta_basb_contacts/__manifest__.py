{
    'name': 'Contact Customization',
    'category': 'Tools',
    'summary': 'meta customization for Concact',
    'description': """
This module gives you a quick view of your contacts directory, accessible from your home page.
You can track your vendors, customers and other contacts.
""",
    'depends': ['base','contacts','stock','account','point_of_sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/inventory_adjustment.xml',
        'views/customer_views.xml',
        'data/access_right.xml',
        'data/scheduled_action.xml',
        'views/contact_button_hide.xml'
    ],
    'application': True,
    'sequence': 1,
}
