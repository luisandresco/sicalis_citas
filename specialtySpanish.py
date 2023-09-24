from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.wsgi import app
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.utils import redirect
from werkzeug.routing import Rule
import json
database_name = 'consultorio_alcaravan'
CONTEXT = {'active_test': False}

# diccionario de especialidades traducidas en español
@app.route('/traslateSpanish', methods=['GET'])
def update_specialty_names(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        Specialty = Pool().get('gnuhealth.specialty')
        especialidades_traducidas = {
    1: "Anatomía",
    2: "Andrología",
    3: "Medicina alternativa",
    4: "Anestesiología",
    5: "Bioquímica",
    6: "Cardiología",
    7: "Cirugía cardiovascular",
    8: "Ciencias del laboratorio clínico",
    9: "Neurofisiología Clínica",
    10: "Dermatología",
    11: "Nutrición",
    12: "Embriología",
    13: "Medicina de emergencia",
    14: "Endocrinología",
    15: "Medicina familiar",
    16: "Medicina Forense",
    17: "Gastroenterología",
    18: "Cirugía general",
    19: "Genética",
    20: "Geriatría",
    21: "Ginecología",
    22: "Hematología",
    23: "Hepatología",
    24: "Histología",
    25: "Inmunología",
    26: "Enfermedad infecciosa",
    27: "Medicina de cuidados intensivos",
    28: "Cirugía maxilofacial",
    29: "Nefrología",
    30: "Neurología",
    31: "Neurocirugía",
    32: "Enfermería",
    33: "Obstetricia y ginecología",
    34: "Oncología",
    35: "Oftalmología",
    36: "Cirugía ortopédica",
    37: "Otorrinolaringología - ORL",
    38: "Cuidados paliativos",
    39: "Patología",
    40: "Pediatría",
    41: "Cirugía pediátrica",
    42: "Farmacología",
    43: "Medicina física y rehabilitación",
    44: "Cirugía plástica",
    45: "Proctología",
    46: "Psiquiatría",
    47: "Neumología",
    48: "Radiología",
    49: "Reumatología",
    50: "Estomatología",
    51: "Oncología quirúrgica",
    52: "Cirugía torácica",
    53: "Toxicología",
    54: "Cirugía de trasplante",
    55: "Cirugía de trauma",
    56: "Medicina de Atención Urgente",
    57: "Urología",
    58: "Cirugía vascular",
    59: "Médico general",
    60: "Medicina Interna",
    61: "Terapia del habla / Fonoaudiología",
    62: "Psicología",
    63: "Medicina para el dolor",
    64: "Medicina Integrativa",
    65: "Neonatología",
    66: "Cirugía cardiotorácica",
    67: "Obstetricia",
    68: "Atención Primaria",
    69: "Planificación Familiar (Atención Primaria)",
    70: "Servicios Sociales",
    71: "Medicina Oral (Atención Primaria)",
    72: "Salud Infantil (Atención Primaria)",
    73: "Salud de la Mujer (Atención Primaria)"
}
        # iterar sobre todos los registros en la tabla
        especialidades = Specialty.search([])
        for especialidad in especialidades:
            # obtener la traducción correspondiente desde el diccionario
            nombre_traducido = especialidades_traducidas.get(especialidad.id)
            if nombre_traducido:
                # actualizar el valor de 'nameSpanish' con la traducción
                especialidad.nameSpanish = nombre_traducido
                especialidad.save()
    json_response = json.dumps({'mensaje': 'Traduccion completada.'})
    return Response(json_response, mimetype='application/json', status=200)
