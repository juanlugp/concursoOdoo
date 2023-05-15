# -*- coding: utf-8 -*-
# from odoo import http


# class Concursos(http.Controller):
#     @http.route('/concursos/concursos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/concursos/concursos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('concursos.listing', {
#             'root': '/concursos/concursos',
#             'objects': http.request.env['concursos.concursos'].search([]),
#         })

#     @http.route('/concursos/concursos/objects/<model("concursos.concursos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('concursos.object', {
#             'object': obj
#         })
