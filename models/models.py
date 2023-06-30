# -*- coding: utf-8 -*-

from operator import truediv
from odoo import models, fields, api, _ #_ es para incluir las traducciones
from odoo.exceptions import UserError
from odoo import tools
from datetime import date 
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug('Can not `import queue_job`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory


def calculate_response(entrada):
      
    if entrada.get('question_type') == 'bool':
        if not 'response_bool' in entrada.keys():
            salida = "Error"
        elif entrada.get('response_bool'): 
            salida="Verdadero"
        else: 
            salida = "Falso"

    elif entrada.get('question_type') == 'num':
        salida = str(entrada.get('response_int'))

    elif entrada.get('question_type') == 'text':
        salida = entrada.get('response_text')

    elif entrada.get('question_type') == 'list':
        salida = str(entrada.get('response_list').name)
        
    else:
        salida = False
    return salida


class concursos(models.Model):    
    _name = 'concursos'
    _description = 'listado de concursos'
    # Herecencia necesaria para enviar mensajes
    _inherit = ['mail.thread', 'mail.activity.mixin']


                #_('xx') siendo xx lo que se va a traducir
    name = fields.Char(string=_('Name'), tracking=True)
    description = fields.Text(string=_('Description'), tracking=True)
    date_start = fields.Date(string=_('Date start'), tracking=True)
    date_end = fields.Date(string=_('Date end'), tracking=True)
    image = fields.Binary(string='Image')
    state = fields.Boolean(string='State')
    estado = fields.Selection(string='State', selection=[('no_iniciado', 'Not Started'), ('iniciado', 'Started'), ('finalizado', 'Finish')], default="no_iniciado", tracking=True)
    partner_ids = fields.Many2many(comodel_name='res.partner', string='Partners', relation='concursos_partner_rel', column1='concursos_id', column2='partner_id')
    questions_ids = fields.Many2many(comodel_name='questions', string='Questions', relation='concursos_questions_rel', column1='concursos_id', column2='questions_id') 
    time_min = fields.Integer(string='Minimum time')
    time_max = fields.Integer(string='Maximum time')
    estimation = fields.Integer(string='Estimation')
    impact = fields.Integer(string='Impact')
    # started = fields.Boolean(compute='_get_iniciado', string='Started')
    # end = fields.Boolean(string='End')
    
    def write (self, vals):
        # if vals.get('estado') == "no_iniciado":
            # raise UserError ('No se puede volver a No iniciado un concurso')
        if vals.get('estado') == "iniciado":
            _logger.warning('Write concursos ' + str(vals))
            self.with_delay(False).inciarparticipacionInt()    
        res = super(concursos, self).write(vals)
        if vals.get('estado') == "finalizado":
            self.finalizarparticipacionInt()
        
        return res

        # def _get_iniciado(self):
    #     for record in self:
    #         dominio=[['concurso_id','=',record.id], 
    #                  ['partner_id','=',record.env.user.partner_id.id]]
    #         record.started=record.env['participation'].search (dominio)
    # def _get_finalizado(self):
    #     if self.estado == False: estado='no_iniciado'
    #     end = False
        # for record in self:
        #     end=(record.date_end >= datetime.today())

    def finalizarparticipacion (self):  
        self.estado="finalizado"

    def finalizarparticipacionInt (self):
        if self.estado == "no_iniciado":
            raise UserError ('No se ha iniciado el concurso')
        if self.estado == "finalizado":
            raise UserError ('El concurso ya está finalizado')
        
        for record in self:
            id_participacion =record.env['participation'].search([['concurso_id','=',record.id],['partner_id','=',self.env.user.partner_id.id],['state', '!=', 'fi']], limit=1) 

            # ahora hay que evaluar si as respuestas son correctas o no
        # self.estado="finalizado"    # Se se deja haría un bucle infinito porque toda función llama a write

    def validarconcurso (self):
        pr =self.env['participation_response'].search([('participation_id.concurso_id.id','=',self.id)]) 
        pr.validarresponse ()
        
    
    def iniciarConcursos (self):
        self.write({'estado':'iniciado'})

    # @job
    def inciarparticipacionInt (self):
        _logger.warning('entra en iniciarparticipacionInt')
        self.ensure_one()
        if self.estado == "iniciado":
            raise UserError ('Ya tiene participaciones para este concurso')

        participaciones = []     
        for record in self.partner_ids:
            part={
                'concurso_id':self.id,
                'partner_id':record.id,
                'name': self.name + ' ' + record.name,
                'participation_response_ids':[(0,0,{'question_id': q.id}) for q in self.questions_ids]
                }
            participaciones.append(part)
        
        _logger.warning('Antes del for ' + str(participaciones))   
        partCreate = self.env['participation'].create(participaciones)
        template = self.env['mail.template'].browse(8)
        _logger.warning('antes del for de envio de correo ' + str(partCreate))
        for record in partCreate:
            template.send_mail(record.id)
        return True

    # def inciarparticipacion (self):
    #     lis=[('concurso_id','=',self.id),('partner_id', '=',self.env.user.partner_id.id)]
    #     participaciones=self.env['participation'].search(lis, limit=1)
    #     return {
    #             "type": "ir.actions.act_window",
    #             "res_model": "participation",
    #             "views": [[False, "form"]],
    #             "res_id":participaciones.id
    #             } # Con esto se abre el formulario de la participación creada


    def iniciarwizard(self):
        hoy = fields.Date.today()

        inicio=self.date_start
        # raise UserError(str(type(inicio)) + str(type(hoy)))
        if self.estado == "no_iniciado":
            raise UserError ('No se ha iniciado el concurso')
        if (inicio!=False and inicio <= hoy):
            raise UserError ('El concurso aún no se puede realizar')
        if self.estado == "finalizado":
            raise UserError ('El concurso ya ha expirado')
        
        id_participacion =self.env['participation'].search([['concurso_id','=',self.id],['partner_id','=',self.env.user.partner_id.id],['state', '!=', 'fi']], limit=1) 
        # self.env['participation_response'].search(['participation_id', '=', id_participacion])
        respuestasSinContestar = id_participacion.participation_response_ids.filtered(lambda x: not x.is_contestada)
        if respuestasSinContestar:
            wiz={
                    'question_id': respuestasSinContestar[0].question_id.id,
                    'participation_id':respuestasSinContestar[0].participation_id.id,
                    'participation_response_id':respuestasSinContestar[0].id,           
            }
            res=self.env['response_wizard'].create(wiz)            
            return {
                    "type": "ir.actions.act_window",
                    "res_model": "response_wizard",
                    "views": [[False, "form"]],
                    "res_id":res.id,
                    "context":{'form_view_initial_mode':'edit'}
                    } # Con esto se abre el formulario de la participación creada
        else:
            date=id_participacion.date
            if date == False:
                self.impact=self.impact+1 # Sólo si no se ha sumado ya
                id_participacion.date=datetime.today()
            return {
                "type": "ir.actions.act_window",
                "res_model": "participation",
                "views": [[False, "form"]],
                "res_id":id_participacion.id,
                "context":{}
            }
            
    # def generarparticipaciones (self):
    #     for concurso in self:
    #         for participacion in concurso.partner_ids:
    #             part={
    #                 'concurso_id':concurso.id,
    #                 'partner_id':participacion.id,
    #                 'participation_response_ids':[(0,0,{'question_id': q.id}) for q in concurso.questions_ids]
    #                 }
    #             self.env['participation'].create(part)
                            
    #             # for u in l:
	#             #     if u.es_bueno:
	# 	        #     lista.append(u.id)
    #             # esto se resume como: lista = [u.id for u in l if u.es_bueno]
                
    #             # part = {}
    #             # part['concurso_id'] = concurso.id
    #             # part['partner_id']=participacion.id
    #     return True

    def estimation_plus(self):
        unit = self.env.context.get('unit')
        max = self.env.context.get('max')
        # min = self.env.context.get('min')
        for record in self:
            record.estimation = record.estimation + unit
            if record.estimation>max:
                record.estimation=max

    def estimation_minus(self):                
        unit = self.env.context.get('unit')
        min = self.env.context.get('min')
        # min = self.env.context.get('min')
        for record in self:
            record.estimation = record.estimation - unit
            if record.estimation<min:
                record.estimation=min
        
    def estimation_clear(self):                
        for record in self:
            record.estimation=0

class questions(models.Model):
    _name = 'questions'
    _description = 'listado de preguntas'
    _order = 'sequence, id'

    name = fields.Char(string='Name')
    question_type = fields.Selection(string='Type', selection=[('num', 'Number'), ('text', 'Text'), ('list', 'List'),  ('bool', 'Boolean')])
    response_bool = fields.Boolean(string='Response bool')
    response_int = fields.Float(string='Response number')
    response_text = fields.Text(string='Response text')
    response_list = fields.One2many(comodel_name='response_options', inverse_name='question_id', string='Response list')
    time_min = fields.Integer(string='Minimum time')
    time_max = fields.Integer(string='Maximum time')
    response = fields.Text(compute='_get_response', string='Response')
    sequence = fields.Integer(string='sequence', default=10)
    
    

    @api.depends('question_type', 'response_bool',  'response_int', 'response_text', 'response_list', 'response_list.question_ok')
    def _get_response(self):
        
        for record in self:
            diccionario = {'question_type': record.question_type, 'response_int': record.response_int, 'response_bool': record.response_bool, 'response_text': record.response_text, 'response_list': False}
            for respuesta_correcta_lista in record.response_list:
                if respuesta_correcta_lista.question_ok:
                    diccionario['response_list'] = respuesta_correcta_lista

            if record.question_type == 'list' and not diccionario['response_list'] :
                record.response= 'No hay opciones correctas'
            else:             
                record.response = calculate_response(diccionario)
  
    

                    
                    
                
        
# hacer response_list

class participation(models.Model):
    _name = 'participation'
    _description = 'participaciones de los concursantes'

    name = fields.Char(string='name')    
    date = fields.Date(string='Date end')
    participation_response_ids = fields.One2many(comodel_name='participation_response', inverse_name='participation_id', string='Participation response')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    concurso_id = fields.Many2one(comodel_name='concursos', string='Concurso')
    state = fields.Selection(selection=[('si', 'Sin Inicia'), ('in', 'Iniciada'), ('fi', 'Finalizado') ], string='Estado')

    def validar_participacion(self):
        for record in self:
            record.participation_response_ids.validarresponse()
    

class participation_response(models.Model):
    _name = 'participation_response'
    _description = 'respuestas de los concursantes'
    _order = "sequence, id"

    question_id = fields.Many2one(comodel_name='questions', string='Question')
    sequence = fields.Integer(string='sequence', related='question_id.sequence', store=True)
    response_int = fields.Float(string='Response number')    
    response_text = fields.Text(string='Response text')
    response_bool = fields.Boolean(string='Response bool')
    response_list = fields.Many2one(comodel_name='response_options', string='Response list')
    response = fields.Text(compute='_get_response', string='Response')
    response_ok = fields.Boolean(string='Response ok')
    is_contestada = fields.Boolean(string='Ya contestada')
    participation_id = fields.Many2one(comodel_name='participation', string='Participation')
    question_type = fields.Selection(string='type', related='question_id.question_type')
    
    def  validarresponse(self):
        for registro in self:
            registro.response_ok = (registro.response == registro.question_id.response)

    @api.depends('response_bool',  'response_int', 'response_text', 'response_list')
    # entrada = {'question_type': False, 'response_int': 0, 'response_bool': False, 'response_text': '', 'response_list': False}
    def _get_response(self):
        for record in self:
            diccionario = {'question_type': record.question_type, 'response_int': record.response_int, 'response_bool': record.response_bool, 'response_text': record.response_text, 'response_list': record.response_list}
            record.response = calculate_response (diccionario)
        
        
    #     for record in self:
    #         if record.is_contestada:
    #             if record.question_type == 'bool':
    #                 record.response = record.response_bool and "Verdero" or "Falso"
    #             elif record.question_type == 'num':
    #                 record.response = str(record.response_int)
    #             elif record.question_type == 'text':
    #                 record.response = record.response_text
    #             elif record.question_type == 'list':
    #                 record.response = record.response_list.name
    #             else:
    #                 record.response = False
    #         else:
    #             record.response = False
            
    
class response_options(models.Model):
    _name = 'response_options'
    _description = 'opciones de las respuestas'

    name = fields.Char(string='Name')
    question_id = fields.Many2one(comodel_name='questions', string='Question')
    question_ok = fields.Boolean(string='Question ok')

class response_report(models.Model):    
    _name = 'response_report'
    _description = 'informe'
    _auto= False # no toca las tablas 

    question_id = fields.Many2one(comodel_name='questions', string='Question')
    response_int = fields.Float(string='Response number')    
    response_text = fields.Text(string='Response text')
    response_bool = fields.Boolean(string='Response bool')
    response_list = fields.Many2one(comodel_name='response_options', string='Response list')
    response_ok = fields.Boolean(string='Response ok')
    participation_id = fields.Many2one(comodel_name='participation', string='Participation')

    
    

    def init(self):
        # self._table = sale_report
        query= """select id, create_uid, create_date, write_uid, write_date, question_id, response_int, response_text, response_bool, response_list, response_ok, participation_id 
        from participation_response"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, query)) 


class response_wizard(models.TransientModel):
    _name= 'response_wizard'

    question_id = fields.Many2one(comodel_name='questions', string='Question')
    response_int = fields.Float(string='Response number')    
    response_text = fields.Text(string='Response text')
    response_bool = fields.Boolean(string='Response bool')
    response_bool_options_id = fields.Many2one(comodel_name='response_wizard_bool', string='Bool Options')
    response_list = fields.Many2one(comodel_name='response_options', string='Response list')
    response_ok = fields.Boolean(string='Response ok')
    participation_id = fields.Many2one(comodel_name='participation', string='Participation')
    texto_question =fields.Char(related='question_id.name')
    question_type = fields.Selection(related ='question_id.question_type')
    participation_response_id = fields.Many2one(comodel_name='participation_response', string='response')
    total_questions = fields.Integer(string='Total Questions', compute="totalquestions")
    question_number = fields.Integer(string='Question Number', compute="totalquestions")
    progress = fields.Char(string='Progress', compute="totalquestions")
    
    
    
    
    @api.model
    def create(self, vals):
        res = super(response_wizard, self).create(vals)
        if len(self.env['response_wizard_bool'].search([])) != 2:
            self.env['response_wizard_bool'].search([]).unlink()
            self.env['response_wizard_bool'].create([{'name':'Verdadero'},{'name':'Falso'}])
        return res


    def siguientepregunta(self):
        self.participation_response_id.is_contestada = True   
        if self.question_type == 'bool':
            self.participation_response_id.response_bool = self.response_bool_options_id and self.response_bool_options_id.name == 'Verdadero'
        elif self.question_type == 'num':
            self.participation_response_id.response_int = self.response_int
        elif self.question_type == 'text':
            self.participation_response_id.response_text = self.response_text
        elif self.question_type == 'list':
            self.participation_response_id.response_list = self.response_list


        return self.participation_response_id.participation_id.concurso_id.iniciarwizard()
    
    @api.depends('participation_id.participation_response_ids', 'participation_response_id')
    def totalquestions(self):        
        for reg in self:
            responses = reg.participation_id.participation_response_ids
            total = len(responses)
            number = list(responses).index(reg.participation_response_id) + 1
            reg.total_questions = total 
            reg.question_number = number
            reg.progress = str(number) + " / " + str(total)

    
        


class ResponseWizardBool(models.TransientModel):
    _name = 'response_wizard_bool'
    _description = 'Modelo para los campos boleanos'

    name = fields.Char(string='name')
    


      