from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from bson import ObjectId
from datetime import datetime
from decorators import instructor_required, login_required
from models import db
from helpers import generar_datos_graficas
from urllib.parse import urlparse, urljoin

instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor')

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def is_safe_url(target):
    """Verifica si la URL es segura para redirección"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def redirect_back(default='instructor.instructor_agenda', **kwargs):
    """Redirige a la página anterior"""
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))

# =============================================================================
# DASHBOARD Y RUTAS PRINCIPALES
# =============================================================================

@instructor_bp.route('/dashboard')
@instructor_required
def user_dashboard():
    try:
        email_instructor = session['user']
        eventos_cursor = db.get_eventos_by_instructor(email_instructor)
        
        print(f"=== EVENTOS PARA INSTRUCTOR: {email_instructor} ===")
        
        # Convertir el cursor a lista
        eventos_lista = []
        if eventos_cursor:
            eventos_lista = list(eventos_cursor)
        
        # Depuración
        for i, evento in enumerate(eventos_lista):
            print(f"\nEvento {i+1}:")
            print(f"  ID: {evento.get('_id')}")
            print(f"  Curso: {evento.get('curso_nombre')}")
            print(f"  Fecha: {evento.get('fecha_evento')}")
            print(f"  Estatus: {evento.get('estatus')}")
            print(f"  Alumnos: {len(evento.get('alumnos_asignados', []))}")
            print(f"  cuestionarios_contestados: {evento.get('cuestionarios_contestados', 'NO EXISTE')}")
            print(f"  evaluaciones_contestadas: {evento.get('evaluaciones_contestadas', 'NO EXISTE')}")

        # ✅ Pasar la lista de eventos a la plantilla
        return render_template('user/dashboard_instructor.html', 
                               eventos=eventos_lista,
                               instructor_nombre=session.get('nombre'))
    except Exception as e:
        print(f"ERROR en dashboard instructor: {e}")
        import traceback
        traceback.print_exc()
        return render_template('user/dashboard_instructor.html', 
                               eventos=[],
                               instructor_nombre=session.get('nombre'))

# =============================================================================
# AGENDA Y EVENTOS
# =============================================================================

@instructor_bp.route('/agenda')
@instructor_required
def instructor_agenda():
    try:
        year = request.args.get('year', default=datetime.now().year, type=int)
        month = request.args.get('month', default=datetime.now().month, type=int)

        if not (1 <= month <= 12):
            month = datetime.now().month
        if year < 2020 or year > 2030:
            year = datetime.now().year

        # ✅ Cambio: Usar db en lugar de Database
        eventos = list(db.get_eventos_by_instructor(session['user']))
        
        eventos_mes = []
        for evento in eventos:
            if evento.get('fecha_evento'):
                if evento['fecha_evento'].year == year and evento['fecha_evento'].month == month:
                    evento.setdefault('total_alumnos', len(evento.get('alumnos_asignados', [])))
                    evento.setdefault('cuestionarios_contestados', 0)
                    evento.setdefault('evaluaciones_contestadas', 0)
                    evento.setdefault('promedio_cuestionarios', 0)
                    evento.setdefault('promedio_evaluaciones', 0)
                    eventos_mes.append(evento)

        meses = [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]

        años = list(range(2020, 2031))

        return render_template('instructor/agenda.html',
            eventos=eventos_mes,
            mes_actual=month,
            año_actual=year,
            meses=meses,
            años=años,
            instructor_nombre=session.get('nombre'))

    except Exception as e:
        print(f"ERROR en instructor_agenda: {e}")
        
        meses = [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]
        años = list(range(2020, 2031))
        
        flash('Error al cargar la agenda', 'error')
        return render_template('instructor/agenda.html',
            eventos=[],
            mes_actual=datetime.now().month,
            año_actual=datetime.now().year,
            meses=meses,
            años=años,
            instructor_nombre=session.get('nombre'))

# =============================================================================
# GESTIÓN DE ALUMNOS EN EVENTOS
# =============================================================================

@instructor_bp.route('/evento/<evento_id>/alumnos')
@instructor_required
def instructor_alumnos_evento(evento_id):
    try:
        print(f"DEBUG [instructor_alumnos_evento]: Iniciando para evento {evento_id}")
        
        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash('Evento no encontrado', 'error')
            return redirect_back()
        
        # ✅ CORRECCIÓN: Los datos de alumnos ya están en el evento
        alumnos_asignados = evento.get('alumnos_asignados', [])
        cuestionarios_detalle = evento.get('cuestionarios_detalle', [])
        evaluaciones_detalle = evento.get('evaluaciones_detalle', [])
        
        print(f"DEBUG [instructor_alumnos_evento]: {len(alumnos_asignados)} alumnos en el evento")
        
        # Crear diccionarios para búsqueda rápida
        cuestionarios_por_email = {q.get('email'): q for q in cuestionarios_detalle}
        evaluaciones_por_email = {e.get('email'): e for e in evaluaciones_detalle}
        
        # Procesar alumnos para la plantilla
        alumnos = []
        for alumno_dict in alumnos_asignados:
            email = alumno_dict.get('email', '')
            cuestionario = cuestionarios_por_email.get(email)
            evaluacion = evaluaciones_por_email.get(email)
            
            alumno_data = {
                'nombre': alumno_dict.get('nombre', ''),
                'email': email,
                'telefono': alumno_dict.get('telefono', ''),
                'fecha_inscripcion': alumno_dict.get('fecha_inscripcion', None),
                'tiene_cuestionario': cuestionario is not None,
                'tiene_evaluacion': evaluacion is not None,
                'cuestionario': cuestionario,
                'evaluacion': evaluacion
            }
            alumnos.append(alumno_data)
        
        print(f"DEBUG [instructor_alumnos_evento]: {len(alumnos)} alumnos procesados para la tabla")
        
        # Renderizar la plantilla
        return render_template('admin/alumnos_evento.html',
            evento=evento,
            alumnos=alumnos,
            total_alumnos=len(alumnos_asignados),
            total_cuestionarios_completados=evento.get('cuestionarios_contestados', 0),
            total_evaluaciones_completadas=evento.get('evaluaciones_contestadas', 0),
            promedio_cuestionarios=evento.get('promedio_cuestionarios', 0),
            promedio_evaluaciones=evento.get('promedio_evaluaciones', 0),
            es_instructor=True)  # ✅ Cambiado a True para instructor
        
    except Exception as e:
        print(f"ERROR en instructor_alumnos_evento: {e}")
        import traceback
        traceback.print_exc()
        flash('Error al cargar los alumnos del evento', 'error')
        return redirect(url_for('instructor.instructor_agenda'))

# =============================================================================
# OPERACIONES SOBRE EVENTOS
# =============================================================================

@instructor_bp.route('/evento/<evento_id>/cerrar', methods=['POST'])
@instructor_required
def cerrar_evento_instructor(evento_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return jsonify({'success': False, 'message': 'Evento no encontrado'})
        
        # Verificar que el evento pertenece al instructor actual
        if evento.get('instructor_email') != session['user']:
            return jsonify({'success': False, 'message': 'No tienes permisos para cerrar este evento'})
        
        # ✅ Cambio: Usar db en lugar de Database
        db.update_evento(evento_id, {'estatus': 'cerrado'})
        return jsonify({'success': True, 'message': 'Evento cerrado exitosamente'})
        
    except Exception as e:
        print(f"ERROR en cerrar_evento_instructor: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# Gráficas de evento del intructor
@instructor_bp.route('/evento/<evento_id>/estadisticas-graficas')
@instructor_required
def instructor_estadisticas_graficas(evento_id):
    """Endpoint para obtener datos de gráficas para un evento específico (instructor)"""
    
    try:
        print(f"DEBUG: Solicitando estadísticas de gráficas para evento: {evento_id}")

        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            print(f"DEBUG: Evento {evento_id} no encontrado")
            return jsonify({'success': False, 'message': 'Evento no encontrado'}), 404

        # Verificar que el evento pertenece al instructor actual
        if evento.get('instructor_email') != session['user']:
            return jsonify({'success': False, 'message': 'No tienes permisos para ver este evento'}), 403

        # Importar la función auxiliar desde routes_eventos
        from routes_eventos import generar_datos_graficas
        
        # Generar datos de gráficas
        datos_graficas = generar_datos_graficas(evento)

        # Verificar si hay datos
        tiene_datos_cuestionarios = datos_graficas["cuestionarios"] is not None
        tiene_datos_evaluaciones = datos_graficas["evaluaciones"] is not None

        if tiene_datos_cuestionarios or tiene_datos_evaluaciones:
            return jsonify({
                'success': True,
                'datos': datos_graficas,
                'message': 'Datos de gráficas obtenidos correctamente'
            })
        else:
            return jsonify({
                'success': True,
                'datos': datos_graficas,
                'message': 'No hay datos de cuestionarios o evaluaciones registrados'
            })

    except Exception as e:
        print(f"ERROR en instructor_estadisticas_graficas: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al obtener estadísticas: {str(e)}'
        }), 500

# =============================================================================
# GESTIÓN DE ALUMNOS EN EVENTOS (PARA INSTRUCTOR)
# =============================================================================

@instructor_bp.route('/buscar_alumno')
@instructor_required
def buscar_alumno_instructor():
    """Buscar alumno por email (para instructores)"""
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'exists': False})
        
        # Buscar alumno en la base de datos
        alumno = db.get_alumno_by_email(email)
        if alumno:
            return jsonify({
                'exists': True,
                'alumno': {
                    'nombre': alumno.get('nombre'),
                    'telefono': alumno.get('telefono', '')
                }
            })
        else:
            return jsonify({'exists': False})
            
    except Exception as e:
        print(f'ERROR en buscar_alumno_instructor: {e}')
        return jsonify({'exists': False, 'error': str(e)})

@instructor_bp.route('/evento/<evento_id>/agregar_alumno', methods=['POST'])
@instructor_required
def agregar_alumno_evento_instructor(evento_id):
    """Agregar alumno a evento (para instructores)"""
    try:
        # Verificar que el evento existe
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return jsonify({'success': False, 'message': 'Evento no encontrado'})

        # Verificar que el instructor tiene permisos
        if evento.get('instructor_email') != session['user']:
            return jsonify({'success': False, 'message': 'No tienes permisos para modificar este evento'}), 403

        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        telefono = request.form.get('telefono', '')

        if not nombre or not email:
            return jsonify({'success': False, 'message': 'Nombre y email son requeridos'})

        # Buscar alumno existente
        alumno_existente = db.get_alumno_by_email(email)

        if not alumno_existente:
            # Crear nuevo alumno con contraseña por defecto "paso"
            from werkzeug.security import generate_password_hash
            password_default = "paso"
            hashed_password = generate_password_hash(password_default)

            alumno_data = {
                'nombre': nombre,
                'email': email,
                'telefono': telefono,
                'password': hashed_password,
                'curso': evento.get('curso_nombre', ''),
                'fecha_registro': datetime.now()
            }
            db.insert_alumno(alumno_data)
        else:
            # Actualizar teléfono si se proporcionó uno nuevo
            if telefono and alumno_existente.get('telefono') != telefono:
                db.update_alumno(email, {'telefono': telefono})

        # Preparar datos del alumno para el evento
        alumno_evento = {
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'fecha_inscripcion': datetime.now()
        }

        alumnos_actuales = evento.get('alumnos_asignados', [])
        
        # Verificar si el alumno ya está inscrito
        alumno_ya_inscrito = any(alumno.get('email') == email for alumno in alumnos_actuales)
        if alumno_ya_inscrito:
            return jsonify({'success': False, 'message': 'El alumno ya está inscrito en este evento'})

        # Agregar alumno al evento
        alumnos_actuales.append(alumno_evento)
        # Limpiar alumnos vacíos si existen
        alumnos_limpios = [alumno for alumno in alumnos_actuales if alumno.get('email')]
        db.update_evento(evento_id, {'alumnos_asignados': alumnos_limpios})

        # ✅ CORRECCIÓN: Importar la función de routes_admin
        from routes_admin import actualizar_metricas_evento
        actualizar_metricas_evento(evento_id)

        return jsonify({
            'success': True,
            'message': f'Alumno {nombre} agregado al evento exitosamente',
            'total_alumnos': len(alumnos_actuales)
        })

    except Exception as e:
        print(f'ERROR en agregar_alumno_evento_instructor: {e}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@instructor_bp.route('/evento/<evento_id>/eliminar-alumno/<email>')
@instructor_required
def eliminar_alumno_evento_instructor(evento_id, email):
    """Eliminar alumno de evento (para instructores)"""
    try:
        # Verificar que el evento existe
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash('Evento no encontrado', 'error')
            return redirect(url_for('instructor.instructor_agenda'))

        # Verificar que el instructor tiene permisos
        if evento.get('instructor_email') != session['user']:
            flash('No tienes permisos para modificar este evento', 'error')
            return redirect(url_for('instructor.instructor_agenda'))

        alumnos_actuales = evento.get('alumnos_asignados', [])
        
        # Filtrar la lista de alumnos, removiendo el alumno con el email proporcionado
        nuevos_alumnos = [alumno for alumno in alumnos_actuales if alumno.get('email') != email]
        
        if len(nuevos_alumnos) == len(alumnos_actuales):
            flash('El alumno no estaba inscrito en este evento', 'warning')
        else:
            db.update_evento(evento_id, {'alumnos_asignados': nuevos_alumnos})
            flash('Alumno eliminado del evento exitosamente', 'success')
            
            # ✅ CORRECCIÓN: Importar la función de routes_admin
            from routes_admin import actualizar_metricas_evento
            actualizar_metricas_evento(evento_id)

        return redirect(url_for('instructor.instructor_alumnos_evento', evento_id=evento_id))
        
    except Exception as e:
        print(f'ERROR en eliminar_alumno_evento_instructor: {e}')
        flash('Error al eliminar alumno del evento', 'error')
        return redirect(url_for('instructor.instructor_alumnos_evento', evento_id=evento_id))

@instructor_bp.route('/evento/<evento_id>/editar-alumno', methods=['POST'])
@instructor_required
def editar_alumno_evento_instructor(evento_id):
    """Editar alumno en evento (para instructores)"""
    try:
        email_original = request.form.get('email_original')
        nuevo_email = request.form.get('nuevo_email')
        nuevo_nombre = request.form.get('nuevo_nombre')
        nuevo_telefono = request.form.get('nuevo_telefono', '')

        if not email_original or not nuevo_email or not nuevo_nombre:
            return jsonify({'success': False, 'message': 'Email original, nuevo email y nombre son requeridos'})

        # Normalizar emails
        email_original = email_original.strip().lower()
        nuevo_email = nuevo_email.strip().lower()

        # Verificar que el instructor tiene permisos sobre este evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return jsonify({'success': False, 'message': 'Evento no encontrado'})
        
        if evento.get('instructor_email') != session['user']:
            return jsonify({'success': False, 'message': 'No tienes permisos para modificar este evento'}), 403

        # Verificar si el nuevo email ya existe (y no es el mismo alumno)
        if email_original != nuevo_email:
            alumno_existente = db.get_alumno_by_email(nuevo_email)
            if alumno_existente:
                return jsonify({'success': False, 'message': 'Ya existe un alumno con ese email'})

        # Obtener datos actuales del alumno
        alumno_actual = db.get_alumno_by_email(email_original)
        if not alumno_actual:
            return jsonify({'success': False, 'message': 'Alumno no encontrado en la base de datos'})

        # Actualizar alumno en la colección Alumnos
        datos_actualizados = {
            'nombre': nuevo_nombre,
            'email': nuevo_email,
            'telefono': nuevo_telefono
        }
        
        resultado_alumno = db.update_alumno(email_original, datos_actualizados)

        # Actualizar alumno en el evento actual (solo este evento, no todos)
        alumnos_evento = evento.get('alumnos_asignados', [])
        alumno_encontrado = False
        
        for i, alumno in enumerate(alumnos_evento):
            alumno_email = alumno.get('email', '').strip().lower()
            if alumno_email == email_original:
                alumno['nombre'] = nuevo_nombre
                alumno['email'] = nuevo_email
                alumno['telefono'] = nuevo_telefono
                alumno_encontrado = True
                break
        
        if alumno_encontrado:
            db.update_evento(evento_id, {'alumnos_asignados': alumnos_evento})

        return jsonify({
            'success': True, 
            'message': 'Alumno actualizado exitosamente en este evento.'
        })

    except Exception as e:
        print(f'ERROR en editar_alumno_evento_instructor: {e}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@instructor_bp.route('/evento/<evento_id>/reabrir', methods=['POST'])
@instructor_required
def reabrir_evento_instructor(evento_id):
    """Reabrir evento cerrado (para instructores)"""
    try:
        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return jsonify({'success': False, 'message': 'Evento no encontrado'})
        
        # Verificar que el evento pertenece al instructor actual
        if evento.get('instructor_email') != session['user']:
            return jsonify({'success': False, 'message': 'No tienes permisos para reabrir este evento'}), 403
        
        # Verificar que el evento esté cerrado
        if evento.get('estatus') != 'cerrado':
            return jsonify({'success': False, 'message': 'El evento ya está abierto'})
        
        # Reabrir el evento
        db.update_evento(evento_id, {'estatus': 'abierto'})
        return jsonify({'success': True, 'message': 'Evento reabierto exitosamente'})
        
    except Exception as e:
        print(f"ERROR en reabrir_evento_instructor: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})