{
    'name': 'OTP Verification',
    'summary': """Send PIN to verify Customer.""",
    'version': '12.0.1.0.0',
    'author': 'Sayed Hassan',
    'company': 'Metamorphosis Ltd.',
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale'],
    'license': 'AGPL-3',
    'data': [
        'views/popup_view.xml',
    ],
    'qweb': ['static/src/xml/popup.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 1,
}