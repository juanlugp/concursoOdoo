# -*- coding: utf-8 -*-
{
    'name': "Concursos de Pantoja",

    'summary': """
        Modulo para la creación y gestión de concursos""",

    'description': """
        Desde este módulo podras crear concursos, gestionarlos, asignar participantes, etc.
        Est módulo permite a los usuarios acceder a los concursos en los que puede participar
    """,

    'author': "Gabriel Castejon para I+D+i de Grupo pantoja",
    'website': "http://www.grupopantoja.com",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
}
