{
    'name': 'Stock Consumtion Report',
    'version': '12.0.1.0.0',
    'description': """The module enable you to print Inventory Consumtion Report""",
    'author': 'Metamorphosis Ltd.',
    'company': 'Metamorphosis Ltd.',
    'category': 'Inventory',
    'depends': [ 'base'],
    'data': [
        'report/stock_consumption_report.xml',
        'wizard/stock_consumption_view.xml', 
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 1
}