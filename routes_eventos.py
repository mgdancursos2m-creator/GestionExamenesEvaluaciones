from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from bson import ObjectId
from datetime import datetime
from decorators import admin_required, instructor_required
from models import db  
from decorators import login_required, admin_required, instructor_required, alumno_required
#import logging

# Configurar logging
#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger(__name__)

eventos_bp = Blueprint('eventos', __name__)

@eventos_bp.route('/evento/<evento_id>')
@admin_required
def detalle_evento(evento_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash('Evento no encontrado', 'error')
            return redirect(url_for('admin.agenda'))
        
        # Procesar información del evento
        alumnos = evento.get('alumnos_asignados', [])
        total_alumnos = len(alumnos)
        
        return render_template('admin/detalle_evento.html',
                             evento=evento,
                             alumnos=alumnos,
                             total_alumnos=total_alumnos)
                             
    except Exception as e:
        print(f"ERROR en detalle_evento: {e}")
        flash('Error al cargar el evento', 'error')
        return redirect(url_for('admin.agenda'))

@eventos_bp.route('/evento/<evento_id>/alumnos')
@login_required
def alumnos_evento(evento_id):
    try:
        print(f"DEBUG [alumnos_evento]: Iniciando para evento {evento_id}")
        
        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash('Evento no encontrado', 'error')
            return redirect_back()
        
        # Los datos de alumnos ya están en el evento
        alumnos_asignados = evento.get('alumnos_asignados', [])
        cuestionarios_detalle = evento.get('cuestionarios_detalle', [])
        evaluaciones_detalle = evento.get('evaluaciones_detalle', [])
        
        print(f"DEBUG [alumnos_evento]: {len(alumnos_asignados)} alumnos en el evento")
        
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
        
        print(f"DEBUG [alumnos_evento]: {len(alumnos)} alumnos procesados para la tabla")
        
        # Renderizar la plantilla
        return render_template('admin/alumnos_evento.html',
            evento=evento,
            alumnos=alumnos,
            total_alumnos=len(alumnos_asignados),
            total_cuestionarios_completados=evento.get('cuestionarios_contestados', 0),
            total_evaluaciones_completadas=evento.get('evaluaciones_contestadas', 0),
            promedio_cuestionarios=evento.get('promedio_cuestionarios', 0),
            promedio_evaluaciones=evento.get('promedio_evaluaciones', 0),
            es_instructor=False)
        
    except Exception as e:
        print(f"ERROR en alumnos_evento: {e}")
        import traceback
        traceback.print_exc()
        flash('Error al cargar los alumnos del evento', 'error')
        if session.get('role') == 'admin':
            return redirect(url_for('admin.agenda'))
        else:
            return redirect(url_for('instructor.instructor_agenda'))


# Genera los datos para las graficas
def generar_datos_graficas(evento):
    """Genera los datos para las gráficas de un evento"""
    
    # Obtener el ID del evento
    evento_id = str(evento.get('_id', ''))
    
    # Obtener datos del evento
    alumnos_asignados = evento.get('alumnos_asignados', [])  # Lista de diccionarios con datos completos
    cuestionarios = evento.get('cuestionarios_detalle', [])
    evaluaciones = evento.get('evaluaciones_detalle', [])
    
    print(f"DEBUG [generar_datos_graficas]: Procesando evento {evento_id}")
    print(f"DEBUG [generar_datos_graficas]: {len(alumnos_asignados)} alumnos asignados")
    print(f"DEBUG [generar_datos_graficas]: {len(cuestionarios)} cuestionarios")
    print(f"DEBUG [generar_datos_graficas]: {len(evaluaciones)} evaluaciones")
    
    # Inicializar estructuras de datos
    datos_cuestionarios = None
    datos_evaluaciones = None
    datos_alumnos = None
    
    # 1. Datos para la gráfica de cuestionarios (por rangos)
    if cuestionarios:
        # Inicializar contadores de rangos
        rangos = [0, 0, 0, 0]  # 0-50%, 51-70%, 71-85%, 86-100%
        
        for cuestionario in cuestionarios:
            calificacion = cuestionario.get('calificacion', 0)
            if calificacion <= 50:
                rangos[0] += 1
            elif calificacion <= 70:
                rangos[1] += 1
            elif calificacion <= 85:
                rangos[2] += 1
            else:
                rangos[3] += 1
        
        datos_cuestionarios = {
            'labels': ['0-50%', '51-70%', '71-85%', '86-100%'],
            'datasets': [{
                'data': rangos,
                'backgroundColor': ['#dc3545', '#ffc107', '#0dcaf0', '#198754']
            }]
        }
        
        print(f"DEBUG: Rangos de cuestionarios: {rangos}")
    
    # 2. Datos para la gráfica de evaluaciones (línea por alumno)
    if evaluaciones and alumnos_asignados:
        # Crear diccionario para mapear evaluaciones por email
        eval_por_email = {}
        for evaluacion in evaluaciones:
            email = evaluacion.get('email')
            if email:
                eval_por_email[email] = evaluacion
        
        # Preparar datos para la gráfica
        labels_evaluaciones = []
        data_evaluaciones = []
        
        for alumno in alumnos_asignados:
            email = alumno.get('email')
            nombre = alumno.get('nombre', email.split('@')[0] if email else 'Sin nombre')
            
            if email in eval_por_email:
                labels_evaluaciones.append(nombre)
                # Usar puntuacion_promedio de la evaluación
                puntuacion = eval_por_email[email].get('puntuacion_promedio', 0)
                data_evaluaciones.append(puntuacion)
        
        if labels_evaluaciones and data_evaluaciones:
            datos_evaluaciones = {
                'labels': labels_evaluaciones,
                'datasets': [{
                    'label': 'Evaluación',
                    'data': data_evaluaciones,
                    'borderColor': '#198754',
                    'backgroundColor': 'rgba(25, 135, 84, 0.1)',
                    'borderWidth': 2,
                    'fill': True
                }]
            }
            print(f"DEBUG: Datos evaluaciones - {len(labels_evaluaciones)} alumnos")
    
    # 3. Datos para la gráfica de calificación por alumno (cuestionarios - barras)
    if cuestionarios and alumnos_asignados:
        # Crear diccionario para mapear cuestionarios por email
        cuestionario_por_email = {}
        for cuestionario in cuestionarios:
            email = cuestionario.get('email')
            if email:
                cuestionario_por_email[email] = cuestionario
        
        # Preparar datos para la gráfica
        labels_alumnos = []
        data_alumnos = []
        background_colors = []
        
        for alumno in alumnos_asignados:
            email = alumno.get('email')
            nombre = alumno.get('nombre', email.split('@')[0] if email else 'Sin nombre')
            
            if email in cuestionario_por_email:
                labels_alumnos.append(nombre)
                calificacion = cuestionario_por_email[email].get('calificacion', 0)
                data_alumnos.append(calificacion)
                
                # Asignar color según calificación
                if calificacion <= 50:
                    background_colors.append('#dc3545')  # Rojo
                elif calificacion <= 70:
                    background_colors.append('#ffc107')  # Amarillo
                elif calificacion <= 85:
                    background_colors.append('#0dcaf0')  # Azul claro
                else:
                    background_colors.append('#198754')  # Verde
            else:
                # Alumno sin cuestionario
                labels_alumnos.append(nombre)
                data_alumnos.append(0)
                background_colors.append('#6c757d')  # Gris
        
        if labels_alumnos:
            datos_alumnos = {
                'labels': labels_alumnos,
                'datasets': [{
                    'label': 'Calificación (%)',
                    'data': data_alumnos,
                    'backgroundColor': background_colors,
                    'borderColor': background_colors,
                    'borderWidth': 1
                }]
            }
            print(f"DEBUG: Gráfica alumnos - Labels: {labels_alumnos}")
            print(f"DEBUG: Gráfica alumnos - Calificaciones: {data_alumnos}")
            print(f"DEBUG: Gráfica alumnos - Colores: {background_colors}")
        else:
            print("DEBUG: No se pudieron generar datos para gráfica de alumnos")
    
    print(f"DEBUG [generar_datos_graficas]: Datos alumnos generados: {datos_alumnos is not None}")
    
    return {
        "cuestionarios": datos_cuestionarios,
        "evaluaciones": datos_evaluaciones,
        "alumnos": datos_alumnos
    }

def obtener_datos_grafica_alumnos(evento_id, alumnos_emails):
    """Obtiene los datos para la gráfica de calificación por alumno"""
    try:
        if not alumnos_emails:
            print(f"DEBUG: No hay emails de alumnos para el evento {evento_id}")
            return None
        
        labels = []
        calificaciones = []
        colores = []
        
        print(f"DEBUG [obtener_datos_grafica_alumnos]: Procesando {len(alumnos_emails)} alumnos")
        
        for email in alumnos_emails:
            # Buscar en la colección Alumnos - Asegúrate de usar la forma correcta
            # Si db es una clase Database, podría ser: db.Alumnos o db['Alumnos']
            alumno = None
            
            # Intenta diferentes formas de acceder a la colección
            if hasattr(db, 'Alumnos'):
                alumno = db.Alumnos.find_one({'email': email})
            elif hasattr(db, 'db') and hasattr(db.db, 'Alumnos'):
                alumno = db.db.Alumnos.find_one({'email': email})
            elif hasattr(db, 'get_collection'):
                alumno = db.get_collection('Alumnos').find_one({'email': email})
            
            if not alumno:
                print(f"DEBUG: Alumno {email} no encontrado")
                continue
                
            # Usar nombre del alumno o email como etiqueta
            nombre = alumno.get('nombre', email.split('@')[0])
            labels.append(nombre)
            
            # Buscar calificación del cuestionario
            cuestionario = None
            if hasattr(db, 'cuestionarios'):
                cuestionario = db.cuestionarios.find_one({
                    'evento_id': ObjectId(evento_id),
                    'alumno_email': email
                })
            
            if cuestionario and 'calificacion' in cuestionario:
                calif = cuestionario['calificacion']
            else:
                calif = 0
                
            calificaciones.append(calif)
            
            # Asignar color según calificación
            if calif >= 81:
                color = '#198754'  # Verde
            elif calif >= 71:
                color = '#0dcaf0'  # Azul
            elif calif >= 51:
                color = '#ffc107'  # Amarillo
            else:
                color = '#dc3545'  # Rojo
                
            colores.append(color)
        
        # Si no hay calificaciones, devolver None
        if not calificaciones:
            print("DEBUG: No se encontraron calificaciones para ningún alumno")
            return None
        
        print(f"DEBUG: Gráfica alumnos - Labels: {labels}, Calificaciones: {calificaciones}")
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Calificación (%)',
                'data': calificaciones,
                'backgroundColor': colores,
                'borderColor': colores,
                'borderWidth': 1
            }]
        }
        
    except Exception as e:
        print(f"Error en obtener_datos_grafica_alumnos: {e}")
        import traceback
        traceback.print_exc()
        return None



@eventos_bp.route('/evento/<evento_id>/estadisticas')
@admin_required
def estadisticas_evento(evento_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return jsonify({'success': False, 'message': 'Evento no encontrado'})
        
        # Calcular estadísticas
        alumnos = evento.get('alumnos_asignados', [])
        total_alumnos = len(alumnos)
        
        estadisticas = {
            'total_alumnos': total_alumnos,
            'cuestionarios_contestados': evento.get('cuestionarios_contestados', 0),
            'evaluaciones_contestadas': evento.get('evaluaciones_contestadas', 0),
            'promedio_cuestionarios': evento.get('promedio_cuestionarios', 0),
            'promedio_evaluaciones': evento.get('promedio_evaluaciones', 0)
        }
        
        return jsonify({'success': True, 'estadisticas': estadisticas})
        
    except Exception as e:
        print(f"ERROR en estadisticas_evento: {e}")
        return jsonify({'success': False, 'message': 'Error al calcular estadísticas'})


def obtener_datos_alumnos_grafica(evento_id, alumnos_emails):
    """Obtiene los datos para la gráfica de calificación por alumno"""
    try:
        if not alumnos_emails:
            return None
        
        labels = []
        calificaciones = []
        colores = []
        
        for email in alumnos_emails:
            # Obtener información del alumno
            alumno = db.usuarios.find_one({'email': email})
            if not alumno:
                continue
                
            # Usar nombre del alumno o email como etiqueta
            nombre = alumno.get('nombre', email.split('@')[0])
            labels.append(nombre)
            
            # Buscar calificación del cuestionario
            cuestionario = db.cuestionarios.find_one({
                'evento_id': ObjectId(evento_id),
                'alumno_email': email
            })
            
            if cuestionario and 'calificacion' in cuestionario:
                calif = cuestionario['calificacion']
            else:
                calif = 0
                
            calificaciones.append(calif)
            
            # Asignar color según calificación
            if calif >= 81:
                color = '#198754'  # Verde
            elif calif >= 71:
                color = '#0dcaf0'  # Azul
            elif calif >= 51:
                color = '#ffc107'  # Amarillo
            else:
                color = '#dc3545'  # Rojo
                
            colores.append(color)
        
        # Si no hay calificaciones, devolver None
        if not calificaciones:
            return None
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Calificación (%)',
                'data': calificaciones,
                'backgroundColor': colores,
                'borderColor': colores,
                'borderWidth': 1
            }]
        }
        
    except Exception as e:
        print(f"Error en obtener_datos_alumnos_grafica: {e}")
        return None

@eventos_bp.route('/evento/<evento_id>/cerrar', methods=['POST'])
@admin_required
def cerrar_evento(evento_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash('Evento no encontrado', 'error')
            return redirect(url_for('admin.agenda'))
        
        # Actualizar estado del evento
        result = db.update_evento(evento_id, {
            'estatus': 'cerrado',
            'fecha_cierre': datetime.now()
        })
        
        if result:
            flash('Evento cerrado exitosamente', 'success')
        else:
            flash('Error al cerrar el evento', 'error')
            
        return redirect(url_for('admin.agenda'))
        
    except Exception as e:
        print(f"ERROR en cerrar_evento: {e}")
        flash('Error al cerrar el evento', 'error')
        return redirect(url_for('admin.agenda'))

@eventos_bp.route('/evento/<evento_id>/reabrir', methods=['POST'])
@admin_required
def reabrir_evento(evento_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash('Evento no encontrado', 'error')
            return redirect(url_for('admin.agenda'))
        
        # Actualizar estado del evento
        result = db.update_evento(evento_id, {
            'estatus': 'abierto',
            'fecha_cierre': None
        })
        
        if result:
            flash('Evento reabierto exitosamente', 'success')
        else:
            flash('Error al reabrir el evento', 'error')
            
        return redirect(url_for('admin.agenda'))
        
    except Exception as e:
        print(f"ERROR en reabrir_evento: {e}")
        flash('Error al reabrir el evento', 'error')
        return redirect(url_for('admin.agenda'))

@eventos_bp.route('/evento/<evento_id>/actualizar_fecha', methods=['POST'])
@admin_required
def actualizar_fecha_evento(evento_id):
    try:
        nueva_fecha = request.form.get('nueva_fecha')
        if not nueva_fecha:
            flash('La fecha es requerida', 'error')
            return redirect(url_for('eventos.detalle_evento', evento_id=evento_id))
        
        # ✅ Cambio: Usar db en lugar de Database
        result = db.update_evento(evento_id, {
            'fecha_evento': datetime.strptime(nueva_fecha, '%Y-%m-%d')
        })
        
        if result:
            flash('Fecha del evento actualizada exitosamente', 'success')
        else:
            flash('Error al actualizar la fecha del evento', 'error')
            
        return redirect(url_for('eventos.detalle_evento', evento_id=evento_id))
        
    except Exception as e:
        print(f"ERROR en actualizar_fecha_evento: {e}")
        flash('Error al actualizar la fecha del evento', 'error')
        return redirect(url_for('eventos.detalle_evento', evento_id=evento_id))

@eventos_bp.route('/evento/<evento_id>/eliminar', methods=['POST'])
@admin_required
def eliminar_evento(evento_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        result = db.delete_evento(evento_id)
        
        if result:
            flash('Evento eliminado exitosamente', 'success')
        else:
            flash('Error al eliminar el evento', 'error')
            
        return redirect(url_for('admin.agenda'))
        
    except Exception as e:
        print(f"ERROR en eliminar_evento: {e}")
        flash('Error al eliminar el evento', 'error')
        return redirect(url_for('admin.agenda'))

# Función auxiliar para actualizar métricas
def actualizar_metricas_evento(evento_id):
    """Actualiza las métricas de un evento"""
    try:
        # ✅ Cambio: Usar db en lugar de Database
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return
        
        total_alumnos = len(evento.get('alumnos_asignados', []))
        
        # Aquí puedes agregar más lógica para calcular otras métricas
        db.update_evento(evento_id, {
            'total_alumnos': total_alumnos
        })
        
    except Exception as e:
        print(f"ERROR en actualizar_metricas_evento: {e}")


def redirect_back(default='admin.agenda', **kwargs):
    """Redirige a la página anterior o a una por defecto"""
    import flask
    request = flask.request
    
    # Intentar obtener la URL de referencia
    referrer = request.referrer
    
    if referrer:
        return redirect(referrer)
    
    # Si no hay referrer, redirigir según el rol del usuario
    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('admin.agenda', **kwargs))
    elif role == 'instructor':
        return redirect(url_for('instructor.instructor_agenda', **kwargs))
    else:
        return redirect(url_for(default, **kwargs))