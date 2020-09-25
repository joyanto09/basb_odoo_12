{
    'name':'Configure Menu',
    'summary':"""This module will show all the necessary menus in one page!""",
    'version':'1.0.0.0',
    'description':"""This module shows Pharmacy, Pharmacy Settings, Pharmacy Categories, Diseases, Beneficiaries Rank, District, BASB Offices in one particular page!
        
        By Md. Mehedi Hasan Akash""",
    'author':'Metamorphosis',
    'company':'Metamorphosis Ltd.',
    'website':'http://www.metamorphosis.com.bd',
    'category':'Extra Tools',
    'depends':['base', 'point_of_sale', 'meta_basb_contacts','contacts'],
    'licence':'OPL-1',
    'data':[
        'views/basb_menu_view.xml',
        'views/dasboard_views.xml',
        'data/data_home.xml',
    ],
    'demo':[],
    'application': True,
    'installable': True,
    'auto_install': False,
    'sequence': 1,
}