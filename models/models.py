# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ #_ es para incluir las traducciones
from odoo.exceptions import UserError
from odoo import tools


class concursos(models.Model):
    _name = 'concursos'
    _description = 'listado de concursos'
                #_('xx') siendo xx lo que se va a traducir
    name = fields.Char(string=_('Name'))
    description = fields.Text(string=_('Description'))
    date_start = fields.Date(string=_('Date start'))
    date_end = fields.Date(string=_('Date end'))
    image = fields.Binary(string='Image')
    state = fields.Boolean(string='State')
    partner_ids = fields.Many2many(comodel_name='res.partner', string='Partners', relation='concursos_partner_rel', column1='concursos_id', column2='partner_id')
    questions_ids = fields.Many2many(comodel_name='questions', string='Questions', relation='concursos_questions_rel', column1='concursos_id', column2='questions_id') 
    time_min = fields.Integer(string='Minimum time')
    time_max = fields.Integer(string='Maximum time')
    estimation = fields.Integer(string='Estimation')
    impact = fields.Integer(string='Impact')




    def iniciarwizard(self):
        id_participacion =self.env['participation'].search([['concurso_id','=',self.id],['partner_id','=',self.env.user.partner_id.id],['state', '!=', 'fi']], limit=1) 
        # self.env['participation_response'].search(['participation_id', '=', id_participacion])
        respuestasSinContestar = id_participacion.participation_response_ids.filtered(lambda x: not x.response)
        if respuestasSinContestar :  
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
            return {
                "type": "ir.actions.act_window",
                "res_model": "participation",
                "views": [[False, "form"]],
                "res_id":id_participacion.id,
                "context":{}
            }


    def inciarparticipacion (self):
        self.ensure_one()
        dominio=[['concurso_id','=',self.id], 
                 ['partner_id','=',self.env.user.partner_id.id]]
        panticipacionesanteriores=self.env['participation'].search (dominio)
        if panticipacionesanteriores:
            return {
                    "type": "ir.actions.act_window",
                    "res_model": "participation",
                    "views": [[False, "tree"]],
                    "domain": [["id", "in", panticipacionesanteriores.ids]],
                    } #Con esto se abre mi lista de patcicipaciones del concurso
            # raise UserError ('Ya tiene participaciones para este concurso')
      

        if self.env.user.partner_id.id in self.partner_ids.ids:
            part={
                'concurso_id':self.id,
                'partner_id':self.env.user.partner_id.id,
                'name': self.name + ' ' + self.env.user.partner_id.name,
                'participation_response_ids':[(0,0,{'question_id': q.id}) for q in self.questions_ids]
                }
            res=self.env['participation'].create(part)            
            return {
                    "type": "ir.actions.act_window",
                    "res_model": "participation",
                    "views": [[False, "form"]],
                    "res_id":res.id
                    } # Con esto se abre el formulario de la participación creada
        else:
            raise UserError ('No pertenece al concurso')


    def generarparticipaciones (self):
        for concurso in self:
            for participacion in concurso.partner_ids:
                part={
                    'concurso_id':concurso.id,
                    'partner_id':participacion.id,
                    'participation_response_ids':[(0,0,{'question_id': q.id}) for q in concurso.questions_ids]
                    }
                self.env['participation'].create(part)
                            
                # for u in l:
	            #     if u.es_bueno:
		        #     lista.append(u.id)
                # esto se resume como: lista = [u.id for u in l if u.es_bueno]
                
                # part = {}
                # part['concurso_id'] = concurso.id
                # part['partner_id']=participacion.id
        return True


class questions(models.Model):
    _name = 'questions'
    _description = 'listado de preguntas'
    _order = 'sequence, id'

    name = fields.Char(string='Name')
    type = fields.Selection(string='Type', selection=[('num', 'Number'), ('text', 'Text'), ('list', 'List'),  ('bool', 'Boolean')])
    response_bool = fields.Boolean(string='Response bool')
    response_int = fields.Float(string='Response number')
    response_text = fields.Text(string='Response text')
    response_list = fields.One2many(comodel_name='response_options', inverse_name='question_id', string='Response list')
    time_min = fields.Integer(string='Minimum time')
    time_max = fields.Integer(string='Maximum time')
    response = fields.Text(compute='_get_response', string='Response')
    sequence = fields.Integer(string='sequence', default=10)
    
    

    @api.depends('type', 'response_bool',  'response_int', 'response_text', 'response_list')
    def _get_response(self):
        for record in self:
            record.response = "Hola mundo"

class participation(models.Model):
    _name = 'participation'
    _description = 'participaciones de los concursantes'

    name = fields.Char(string='name')    
    date = fields.Date(string='Date end')
    participation_response_ids = fields.One2many(comodel_name='participation_response', inverse_name='participation_id', string='Participation response')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    concurso_id = fields.Many2one(comodel_name='concursos', string='Concurso')
    state = fields.Selection(selection=[('si', 'Sin Inicia'), ('in', 'Iniciada'), ('fi', 'Finalizado') ], string='Estado')
    

    @api.depends('response_bool',  'response_int', 'response_text', 'response_list')
    def _get_response(self):
        for record in self:
            record.response = "Hola mundo"

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
    question_type = fields.Selection(string='type', related='question_id.type')
    
    

    @api.depends('response_bool',  'response_int', 'response_text', 'response_list')
    def _get_response(self):
        for record in self:
            if record.is_contestada:
                if record.question_type == 'bool':
                    record.response = record.response_bool and "Verdero" or "Falso"
                elif record.question_type == 'num':
                    record.response = str(record.response_int)
                elif record.question_type == 'text':
                    record.response = record.response_text
                elif record.question_type == 'list':
                    record.response = record.response_list.name
                else:
                    record.response = False
            else:
                record.response = False
            
    
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
    question_type = fields.Selection(related ='question_id.type')
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
            self.participation_response_id.response_bool = self.response_bool
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
    


      