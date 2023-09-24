import os
import secrets
import smtplib
import json
import random
import string
from datetime import date, datetime
from email.mime.text import MIMEText
from pytz import timezone
import pytz
import math

from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.utils import redirect
from werkzeug.routing import Rule

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.wsgi import app
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta

database_name = 'consultorio_alcaravan'
CONTEXT = {'active_test': False}

def convert_to_caracas_time(utc_time):
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    caracas_tz = timezone('America/Caracas')
    caracas_time = utc_time.astimezone(caracas_tz)
    return caracas_time

# Calcula la edad.
def calcular_edad(fecha_nac):
    hoy = date.today()
    fecha_nac = date.fromisoformat(fecha_nac)
    edad = hoy.year - fecha_nac.year - \
        ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
    return edad

# Traduce el campo "Estado" en las citas.
def translate_state(state):
    translation_dict = {
        'confirmed': 'Confirmado',
        'checked_in': 'Registrado',
        'done': 'Hecho',
        'user_cancelled': 'Cancelado por el usuario',
        'center_cancelled': 'Cancelado por el centro de salud',
        'no_show': 'No asistió'
    }
    return translation_dict.get(state, state)

# Redenderiza las imagenes.
def serve_static_file(file_path, content_type):
    dir_path = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(dir_path, file_path), 'rb') as f:
            file_content = f.read()
        return Response(file_content, status=200, content_type=content_type)
    except FileNotFoundError:
        return Response("Archivo no encontrado", status=404)

# Redenderiza los HTML-CSS.
def build_response(html_file:str, css_file:str):
    dir_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dir_path, html_file), 'r') as f:
        html = f.read()
    with open(os.path.join(dir_path, css_file), 'r') as f:
        css = f.read()
    return Response(html + css, status=200, content_type='text/html')

# Envia los códigos de acceso al correo
def sendEmail(to_email,token):
    # Configuración
    smtp_server = '10.250.4.168'  #Servidor Exim
    smtp_port = 25  # Puerto SMTP
    from_email = 'Sicalis@alcaravan.com.ve' #Correo electrónico
    subject = 'Sicalis'
    message = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mensaje de Sicalis</title>
    <!-- CSS de Bootstrap 5 -->
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/5.0.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
    body {{
    background-color: #f8f9fa;
    transition: background-color 0.5s;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    }}
    .card {{
    border-radius: 15px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    max-width: 400px;
    width: 100%;
    }}
    .card-header {{
    background-color: #007bff;
    color: white;
    font-size: 24px;
    font-weight: bold;
    text-align: center;
    padding: 20px;
    border-top-left-radius: 15px;
    border-top-right-radius: 15px;
    }}
    .card-body {{
    padding: 20px;
    }}
    .card-text {{
    font-size: 18px;
    line-height: 1.5;
    margin-bottom: 15px;
    }}
    .token {{
    font-size: 20px;
    font-weight: bold;
    color: #007bff;
    }}
    </style>
    </head>
    <body>
    <div class="card">
    <div class="card-header">
    Sicalis
    </div>
    <div class="card-body">
    <p class="card-text">Hola, tu clave de acceso al sistema Sicalis es: <span class="token">{token}</span></p>
    <p class="card-text">Recuerda que este código te fue asignado para acceder al sistema permanentemente, debes guardarlo y no lo compartas con nadie.</p>
    <p class="card-text">Si no solicitaste una clave de acceso, ignora este mensaje.</p>
    </div>
    </div>
    <!-- JS de Bootstrap 5 -->
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/5.0.2/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    # Crear el mensaje
    msg = MIMEText(message, 'html')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    # Enviar el correo
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.sendmail(from_email, to_email, msg.as_string())
        return True
    except Exception as e:
        return False

# Envia los ID de cita al correo
def sendEmailId(token,name,apell,ced,eda,healthproV,specialty,fechas,horaV,tipoide,cedul):
        tercero = Pool().get('party.party')
        cedulaTercero = tercero.search([('ref', '=', cedul)])
        for correo in cedulaTercero:
            correoTercero = correo.partyEmail
        to_email = correoTercero
        # Configuración
        smtp_server = '10.250.4.168'  #Servidor Exim
        smtp_port = 25  # Puerto SMTP
        from_email = 'Sicalis@alcaravan.com.ve' #Correo electrónico
        subject = 'Sicalis'
        message = f"""
<!DOCTYPE html>
<html>
<head>

</head>
<body>
    <div style="width: 60%; max-width: 800px; min-width: 300px; margin: 0 auto;">
        <div style="display: flex; margin-bottom: 1rem;">
            
            <div style="width: 100%; text-align: right;">
                <label for="codigoCita" style="display: inline-block; margin-bottom: .5rem; font-size: 20px; color: #222222;">Código de Cita: </label> <p style="color: #0c6c82ff; display: inline-block; margin-bottom: .5rem; font-size: 20px;">{token}</p>
            </div>
        </div>
        <div style="margin: 1rem 0; padding: .5rem 1rem; border: 1px solid #dee2e6; border-radius: .25rem;">
            <div style="padding: .75rem 1.25rem; background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; text-align: center;">
                <h2 style="margin: 8px;">Resumen de Cita</h2>
            </div>
            <div style="padding: 1.25rem;">
                <table style="width: 100%; text-align: left; color: #222222;">
                    <tr>
                        <td style="width:50%; vertical-align: top;">
                            <p style="font-size: 16px; color: #222222;"><strong>Datos del Paciente</strong></p>
                            <p style="font-size:16px; color: #222222;">Nombre: {name}</p>
                            <p style="font-size:16px; color: #222222;">Apellido: {apell}</p>
                            <p style="font-size:16px; color: #222222;">Cédula: {ced}</p>
                            <p style="font-size:16px; color: #222222;">Edad: {eda}</p>
                        </td>
                        <td style="width:50%; vertical-align: top; color: #222222">
                            <p style="font-size: 16px; color: #222222;"><strong>Datos de la Cita</strong></p>
                            <p style="font-size:16px; color: #222222;">Doctor: {healthproV}</p>
                            <p style="font-size:16px; color: #222222;">Especialidad: {specialty}</p>
                            <p style="font-size:16px; color: #222222;">Fecha: {fechas}</p>
                            <p style="font-size:16px; color: #222222;">Hora: {horaV}</p>
                            <p style="font-size:16px; color: #222222;">Tipo: {tipoide}</p>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""
        # Crear el mensaje
        msg = MIMEText(message, 'html')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        # Enviar el correo
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.sendmail(from_email, to_email, msg.as_string())
            return Response(status=200)
        except Exception as e:
            return Response(status=500)
# rutas de vistas.

@app.route('/favicon.ico')
def serve_img(request):
    return serve_static_file(f'static/img/favicon.ico', content_type ='image/svg')

@app.route('/static/img/image.jpg')
def serve_img(request):
    return serve_static_file(f'static/img/image.jpg', content_type ='image/jpg')

@app.route('/static/img/image2.jpg')
def serve_img(request):
    return serve_static_file(f'static/img/image2.png', content_type ='image/jpg')

@app.route('/static/img/SICALIS.png')
def serve_img(request):
    return serve_static_file(f'static/img/SICALIS.png', content_type='image/jpg')

@app.route('/Sicalis-login')
def func1(request):
    return build_response('view/principal.html', 'static/css/principal.css')

@app.route('/Sicalis-register-email')
def func2(request):
    return build_response('view/email.html', 'static/css/email.css')

@app.route('/Sicalis-register-Appointment_confirmation_status_patient')
def func3(request):
    return build_response('view/cita.html', 'static/css/cita.css')

@app.route('/Sicalis-login-registered-HOME-patient-confirmed')
def func4(request):
    return build_response('view/home.html', 'static/css/home.css')

@app.route('/Sicalis-login-user-registered-session')
def func5(request):
    return build_response('view/iniciarSesion.html', 'static/css/iniciarSesion.css')

@app.route('/Sicalis-login-user-history')
def func5(request):
    return build_response('view/historial.html', 'static/css/historial.css')

@app.route('/Sicalis-exit-session')
def func6(self):
    return build_response('view/salir.html', 'static/css/salir.css')

# Verifica si el tercero tiene un token registrado.
def handle_token_response(cedulaSearch):
    for cedulas in cedulaSearch:
        token = cedulas.token
    if token == None:
        response_dict = {'url': '/Sicalis-register-email'}
        json_response = json.dumps(response_dict)
        return Response(json_response, mimetype='application/json', status=200)
    else:
        response_dict = {'url': '/Sicalis-login-user-registered-session'}
        json_response = json.dumps(response_dict)
        return Response(json_response, mimetype='application/json', status=200)

# Hace las validaciones pertinentes en la vista del login y las acciones en consecuencia.
@app.route('/ConsultaF', methods=['POST'])
def get_terceros(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        cedula = request.form.get('cedula')
        cedulaFederation = 'TIT_{}'.format(cedula)
        tercero = Pool().get('party.party')
        patient = Pool().get('gnuhealth.patient')
        contacMechanism = Pool().get('party.contact_mechanism')
        cedulaSearch = tercero.search([('ref', '=', cedula)])
        patientSearch = patient.search([('name', '=', cedula)])
        contacMechanismSearch = contacMechanism.search(
            [('party', '=', cedula)])
        cedulaFederationSearch = tercero.search(
            [('federation_account', '=', cedulaFederation)])

        if not cedula:
            json_response = json.dumps({'error': 'Debe completar el campo de cédula antes de continuar. Por favor, asegúrese de llenarlo correctamente.'})
            return Response(json_response, mimetype='application/json', status=404)
        elif not cedulaSearch:
            json_response = json.dumps({'error': 'Usuario no encontrado, por favor comuníquese con el personal de talento humano para solventar este inconveniente'})
            return Response(json_response, mimetype='application/json', status=404)
        elif not cedulaFederationSearch:
            json_response = json.dumps({'error': 'La cédula ingresada no corresponde a un usuario establecido como titular, por favor comuníquese con el personal de talento humano para solventar este inconveniente.'})
            return Response(json_response, mimetype='application/json', status=404)
        elif not contacMechanismSearch:
            json_response = json.dumps({'error': 'Este usuario no cuenta con mecanismos de contacto registrados, por favor comuníquese con el personal de talento humano para solventar este inconveniente.'})
            return Response(json_response, mimetype='application/json', status=404)
        if not patientSearch:
            for terceros in cedulaSearch:
                id = terceros.id
                tercero.write([terceros], {'is_patient': True})
                # Si no hay paciente asociado, crear uno nuevo en la tabla gnuhealth_patient
                name = id
                vals = {
                    'name': name,
                    'active': True,
                }
                patient.create([vals])[0]
                
            return handle_token_response(cedulaSearch)
        else:
            return handle_token_response(cedulaSearch)

# Obtiene y envia los correos registrados del tercero.
@app.route('/emails', methods=['POST'])
def get_email(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        party = Pool().get('party.contact_mechanism')
        cedula = request.form.get('cedula').strip('"')
        terceros = party.search([('party', '=', cedula)])
        response_dict = {'correos': []}
        for tercero in terceros:
            response_dict['correos'].append({'correo': tercero.value})
        json_response = json.dumps(response_dict)
        return Response(json_response, mimetype='application/json', status=200)

# Recibe y envia el correo electronico.
@app.route('/send-email', methods=['POST'])
def send_email_cliente(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        # Eliminar comillas dobles de la cadena
        cedula = request.form.get('cedula').strip('"')
        Party = Pool().get('party.party')
        cedulaSearch = Party.search([('ref', '=', cedula)])
        party_record = cedulaSearch[0]
        # Caracteres válidos: letras y números
        alphabet = string.ascii_letters + string.digits
        # Generar una cadena aleatoria de 6 caracteres combinando letras y números
        token = ''.join(secrets.choice(alphabet) for i in range(6))
        to_email = request.form.get('email')
        if sendEmail(to_email,token):
            party_record.token = token
            party_record.partyEmail = to_email
            party_record.save()
            return Response(status=200)
        else:
            return Response(status=500)

# Obtiene y envia al titular y sus beneficiarios. Si estos ultimos no son pacientes los crea como tal.
@app.route('/crear_citas', methods=['POST'])
def crear_citas(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        party = Pool().get('party.party')
        party2 = Pool().get('gnuhealth.patient')
        cedula = request.form.get('cedula').strip('"')

        # Buscar los terceros correspondientes
        terceros = party.search([('ref', '=', cedula)])
        id_fed_titular = f"TIT_{cedula}"
        id_fed_beneficiarios = [f'TIT_{cedula}']
        for i in range(1, 10):
            id_fed_beneficiarios.append(f'BEN_{cedula}_{i}')
            id_fed_beneficiarios.append(f'BEN_{cedula}')
        titular = party.search([('federation_account', '=', id_fed_titular)], limit=1)[0]
        beneficiarios = party.search([('federation_account', 'in', id_fed_beneficiarios)])
        response_dict = {'pacientes': []}
        for benefico in beneficiarios:
            idCedula = benefico.id
            terceros2 = party2.search([('name', '=', idCedula)])
            saveid = None
            if benefico.is_patient == False or not terceros2:
                party.write([benefico], {'is_patient': True})
            # Si no hay paciente asociado, crear uno nuevo en la tabla gnuhealth_patient
                name = idCedula
                vals = {
                    'name': name,
                    'active': True,
                }
                new_patient = party2.create([vals])[0]
                saveid = new_patient.id

            else:
                saveid = terceros2[0].id

            # Actualizar el ID del paciente en el registro correspondiente
            response_dict['pacientes'].append({
                'nombre': benefico.name,
                'apellido': benefico.lastname,
                'idfederation': benefico.federation_account,
                'idpaciente': saveid,
            })
        json_response = json.dumps(response_dict)
        return Response(json_response, mimetype='application/json', status=200)

# Verifica si el token ingresado es correcto para ese tercero.
@app.route('/verification-token', methods=['POST'])
def verification(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        party = Pool().get('party.party')
        token = request.form.get('token').strip('"')
        cedula = request.form.get('cedula').strip('"')
        tokenSearch = party.search([('ref', '=', cedula)])
        for tokens in tokenSearch:
            code = tokens.token
        if code == token:
            response_dict = {'url': '/Sicalis-login-registered-HOME-patient-confirmed'}
            json_response = json.dumps(response_dict)
            return Response(json_response, mimetype='application/json', status=200)
        elif not token:
            json_response = json.dumps(
                {'error': 'Debe ingresar la clave de acceso antes de continuar. Por favor, asegúrese de llenarlo correctamente.'})
            return Response(json_response, mimetype='application/json', status=404)
        else:
            json_response = json.dumps(
                {'error': 'La clave de acceso que ha ingresado no es válida. Por favor, revise y vuelva a intentarlo.'})
            return Response(json_response, mimetype='application/json', status=404)


@app.route('/selected-autocomplete-name', methods=['POST'])
def selectedAutocomplete(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        party = Pool().get('party.party')
        cedula = request.form.get('cedula').strip('"')
        terceros = party.search([('ref', '=', cedula)])
        prueba = []
        response_dict = {'terceroS': []}
        for tercero in terceros:
            response_dict['terceroS'].append({
                'nombre': tercero.name, 'apellido': tercero.lastname})
        json_response = json.dumps(response_dict)
        return Response(json_response, mimetype='application/json', status=200)
    
# Obtiene los datos del titular y los beneficiarios para precargarlos en el select.
@app.route('/selected-autocomplete', methods=['POST'])
def selectedAutocomplete(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        party = Pool().get('party.party')
        federation = request.form.get('federation').strip('"')
        terceros = party.search([('federation_account', '=', federation)])
        prueba = []
        for tercero in terceros:
            fechaNacimiento = (tercero.dob)
        response_dict = {'terceroS': []}
        for tercero in terceros:
            response_dict['terceroS'].append({
                'nombre': tercero.name, 'apellido': tercero.lastname, 'cedula': tercero.ref, 'edad': calcular_edad(str(fechaNacimiento))})
        json_response = json.dumps(response_dict)
        return Response(json_response, mimetype='application/json', status=200)

# Obtiene las especialidades para precargarlas en el select.
@app.route('/selected-autocomplete-specialty', methods=['POST'])
def selectedAutocompleteSpecialty(reques):
    with Transaction().start(database_name, 1, context=CONTEXT):
        party = Pool().get('gnuhealth.hp_specialty')
        terceros = party.search([])
        nombres = set()
        ids = set()
        response_dict = {'especialidades': []}
        for tercero in terceros:
            nombre = tercero.specialty.nameSpanish
            id_ = tercero.specialty.id
            if nombre not in nombres and id_ not in ids:
                nombres.add(nombre)
                ids.add(id_)
                response_dict['especialidades'].append(
                    {'nombre': nombre, 'id': id_})
        json_response = json.dumps(response_dict)
        return Response(json_response, mimetype='application/json', status=200)

# Obtiene los especialistas de la salud según la especialidad.
@app.route('/selected-autocomplete-healthprof', methods=['POST'])
def selectedAutocomplete(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        party = Pool().get('gnuhealth.hp_specialty')
        # Eliminar comillas dobles de la cadena
        specialty = request.form.get('specialty')
        terceros = party.search([('specialty.id', '=', specialty)])
        response_dict = {'healthprof': []}
        for tercero in terceros:
            response_dict['healthprof'].append({
                'nombre': tercero.name.name.name, 'apellido': tercero.name.name.lastname, 'id': tercero.name.id})
        json_response = json.dumps(response_dict)
        return Response(json_response, mimetype='application/json', status=200)

@app.route('/selected-autocomplete-schedule', methods=['POST'])
def selectedAutocomplete(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        party = Pool().get('gnuhealth.appointment')
        especialidadId = int(request.form.get('esp').strip('"'))
        healthProf = int(request.form.get('hp').strip('"'))
        state = 'free'.strip('"')
        
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d")
        formatted_time = now.strftime("%H:%M:%S")
        hourDate = formatted_date + " " + formatted_time
        horarios = party.search([('healthprof', '=', healthProf), ('speciality', '=', especialidadId), ('state', '=', state), ('appointment_date', '>=', hourDate)])
        horariosAntiguos = party.search([('healthprof', '=', healthProf), ('speciality', '=', especialidadId), ('state', '=', state), ('appointment_date', '<=', hourDate)])
        print("aqui: ", horariosAntiguos)
        if not horarios:
            if horariosAntiguos:
                json_response = json.dumps({'error': 'Disculpe, los horarios de trabajo de este especialista están vencidos. Comuníquese con el personal de talento humano.'})
                return Response(json_response, mimetype='application/json', status=404)
            else:
                json_response = json.dumps({'error': 'Disculpe, este especialista no tiene horarios disponibles. Comuníquese con el personal de talento humano'})
                return Response(json_response, mimetype='application/json', status=404)
        else:
            response_dict = {'fechas': [], 'horarios': {}}
            date_dict = {}
            for horario in horarios:
                caracas_time = convert_to_caracas_time(horario.appointment_date)
                formatted_date2 = caracas_time.strftime('%d-%m-%Y')
                formatted_date3 = caracas_time.strftime('%H:%M')

                if formatted_date2 not in date_dict:
                    date_dict[formatted_date2] = [{'hora': formatted_date3, 'id': horario.id}]
                else:
                    date_dict[formatted_date2].append({'hora': formatted_date3, 'id': horario.id})

            for fecha, horas in date_dict.items():
                response_dict['fechas'].append(fecha)
                response_dict['horarios'][fecha] = horas
            json_response = json.dumps(response_dict)
            return Response(json_response, mimetype='application/json', status=200)

@app.route('/create-appointment', methods=['POST'])
def selectedAutocomplete(request):
    with Transaction().start(database_name, 1, context=CONTEXT):
        party = Pool().get('gnuhealth.appointment')
        citaID = request.form.get('citaID').strip('"')
        tipoVisita = request.form.get('tipoVisita').strip('"')
        idpaciente = request.form.get('idpaciente').strip('"')
        name = request.form.get('name').strip('"')
        apell = request.form.get('apell').strip('"')
        ced = request.form.get('ced').strip('"')
        eda = request.form.get('eda').strip('"')
        healthproV = request.form.get('healthproV').strip('"')
        specialty = request.form.get('specialty').strip('"')
        fechas = request.form.get('fechas').strip('"')
        horaV = request.form.get('horaV').strip('"')
        tipoide = request.form.get('tipoide').strip('"')
        cedul = request.form.get('cedul').strip('"')
        espID = request.form.get('espID').strip('"')
        anio_actual = datetime.now().strftime('%Y')
        num_aleatorio = random.randint(1, 100)
        idcita = f"APP {anio_actual}/{num_aleatorio}"
        state = 'confirmed'.strip('"')
        state2 = 'checked_in'.strip('"')
        state3 = 'free'.strip('"')
        citas = party.search([('patient', 'in', [idpaciente]),('speciality', 'in', [espID])])
        for cita in citas:
            if str(cita.state) in [str(state), str(state2)] and str(cita.speciality.id) == str(espID):
                response_data = {"mensaje": "Disculpe, usted ya cuenta con una cita activa para esta especialidad"}
                json_response = json.dumps(response_data)
                return Response(json_response, mimetype='application/json', status=206)
        appointment = party.search([('id', '=', citaID)])
        for appointment_record in appointment:
            if str(appointment_record.state) != state3:
                response_data = {"mensaje": "Disculpe, esta cita ya ha sido tomada por alguien mas, seleccione otra hora o fecha"}
                json_response = json.dumps(response_data)
                return Response(json_response, mimetype='application/json', status=207)

        """ NOTA

            NO COLOCAR EL VALS HACIA ABAJO DENTRO DEL FOR 
        
        """
        # Si no se encontró ninguna cita que cumpla con las condiciones, se ejecuta el código de abajo
        vals = {
            'visit_type': tipoVisita,
            'patient': idpaciente,
            'state': state,
            'name': idcita,
        }
        for appointment_record in appointment:
            id = appointment_record.id
            party.write([appointment_record], vals)
        token = idcita
        sendEmailId(token,name,apell,ced,eda,healthproV,specialty,fechas,horaV,tipoide,cedul)
        response_data = {"mensaje": idcita}
        json_response = json.dumps(response_data)
        return Response(json_response, mimetype='application/json', status=200)
    
    
    # De aqui en adelante, todo lo relacionado al historial.
    
@app.route('/load_history', methods=['POST'])
def loadHistory(request):
     with Transaction().start(database_name, 1, context=CONTEXT):
         party = Pool().get('party.party')
         party2 = Pool().get('gnuhealth.patient')
         cedula = request.form.get('cedula').strip('"')
        # Obtener los parámetros de paginación
         page = request.form.get('page', 1, type=int)
         print(page)
         per_page = request.form.get('per_page', 10, type=int)
         offset = (page - 1) * per_page
         # Buscar los terceros correspondientes
         cedula = '28262650'.strip('"')
         terceros = party.search([('ref', '=', cedula)])
         id_fed_titular = f"TIT_{cedula}"
         id_fed_beneficiarios = [f'TIT_{cedula}']
         for i in range(1, 10):
             id_fed_beneficiarios.append(f'BEN_{cedula}_{i}')
             id_fed_beneficiarios.append(f'BEN_{cedula}')
         titular = party.search([('federation_account', '=', id_fed_titular)], limit=1)[0]
         beneficiarios = party.search([('federation_account', 'in', id_fed_beneficiarios)])
         response_dict = {'pacientes': []}
         for benefico in beneficiarios:
             idCedula = benefico.id
             terceros2 = party2.search([('name', '=', idCedula)])
             saveid = None
             if benefico.is_patient == False or not terceros2:
                 party.write([benefico], {'is_patient': True})
             # Si no hay paciente asociado, crear uno nuevo en la tabla gnuhealth_patient
                 name = idCedula
                 vals = {
                     'name': name,
                     'active': True,
                 }
                 new_patient = party2.create([vals])[0]
                 saveid = new_patient.id

             else:
                 saveid = terceros2[0].id
             # Actualizar el ID del paciente en el registro correspondiente
             response_dict['pacientes'].append({
                 'idpaciente': saveid,
             })
         party3 = Pool().get('gnuhealth.appointment')
         listAppointment = {'appointments': []}
         patient_ids = [p['idpaciente'] for p in response_dict['pacientes']]
         appointmentsSearch = party3.search([('patient', 'in', patient_ids)])
         total_appointments = len(appointmentsSearch)
         total_pages = int(math.ceil(total_appointments / per_page))
         current_page = page
         appointments = appointmentsSearch[offset : offset + per_page]

         listAppointment = {
             'appointments': [],
             'pagination': {
                 'total': total_appointments,
                 'per_page': per_page,
                 'total_pages': total_pages,
                 'current_page': current_page
             }
         }

         for cita in appointments:
             patient_name = cita.patient.name.name
             patient_lastname = cita.patient.lastname
             speciality_name = cita.speciality.nameSpanish
             appointment_date = cita.appointment_date
             appointment_date_str = cita.appointment_date.strftime('%Y-%m-%dT%H:%M:%S')
             state = translate_state(cita.state)
             visit_type = cita.visit_type
             healthprof_name = cita.healthprof.name.name
             idcita = cita.name
             caracas_time = convert_to_caracas_time(cita.appointment_date)
             formatted_date2 = caracas_time.strftime('%d-%m-%Y')
             formatted_date3 = caracas_time.strftime('%H:%M')

             listAppointment['appointments'].append({
             'Nombre': patient_name,
             'Apellido': patient_lastname,
             'Especialidad': speciality_name,
             'Fecha': formatted_date2,
             'Hora': formatted_date3,
             'Estatus': state,
             'Tipo': visit_type,
             'HealthPorf': healthprof_name,
             'idcita': idcita

             })

         json_response = json.dumps(listAppointment)
         return Response(json_response, mimetype='application/json', status=200)

# @app.route('cancel_appointment', methods=['POST'])
# def selectedAutocomplete(request):
#      with Transaction().start(database_name, 1, context=CONTEXT):
#          party = Pool().get('gnuhealth.appointment')
#          idcita = request.form.get('idcita').strip('"')
#          appointment = party.search([('name', '=', idcita)])
#          vals = {
#                       'state': True,
#                   }
#          appointment.write(vals)
#          return Response(mimetype='application/json', status=200)
    
    # Confirmed = Confirmado
    # Checked_in = Registrado
    # done = Hecho
    # user_cancelled = Cancelado por el usuario
    # center_cancelled = Cancelado por el centro de salud
    # no_show = No asistió
    
