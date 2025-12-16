from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from bson import ObjectId
from datetime import datetime
from decorators import admin_required
from models import db  # ✅ Cambio importante: Solo importar db, no Database
from werkzeug.security import generate_password_hash
from decorators import login_required, admin_required, instructor_required, alumno_required
from helpers import generar_datos_graficas

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# =============================================================================
# DASHBOARD Y GESTIÓN PRINCIPAL
# =============================================================================

@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

# ===============================
# GESTIÓN DE EVENTOS -
# ===============================

@admin_bp.route('/eventos')
@admin_required
def gestion_eventos():
    try:
        # Obtener parámetros de ordenación y filtrado
        sort_by = request.args.get('sort', 'fecha_evento')
        order = request.args.get('order', 'desc')
        filter_type = request.args.get('filter_type', '')
        filter_value = request.args.get('filter_value', '')
        
        # Obtener todos los eventos
        eventos = list(db.get_eventos())
        
        # Aplicar filtro si se especifica
        if filter_type and filter_value:
            eventos_filtrados = []
            for evento in eventos:
                if filter_type == 'instructor':
                    instructor_nombre = evento.get('instructor_nombre', '')
                    if instructor_nombre and filter_value.lower() in instructor_nombre.lower():
                        eventos_filtrados.append(evento)
                elif filter_type == 'curso':
                    curso_nombre = evento.get('curso_nombre', '')
                    if curso_nombre and filter_value.lower() in curso_nombre.lower():
                        eventos_filtrados.append(evento)
                elif filter_type == 'estatus':
                    estatus = evento.get('estatus', '')
                    if estatus and filter_value.lower() in estatus.lower():
                        eventos_filtrados.append(evento)
                elif filter_type == 'fecha':
                    fecha_evento = evento.get('fecha_evento')
                    if fecha_evento:
                        fecha_str = fecha_evento.strftime('%d/%m/%Y')
                        if filter_value in fecha_str:
                            eventos_filtrados.append(evento)
            eventos = eventos_filtrados
            print(f"DEBUG: Filtrado por {filter_type}={filter_value}, encontrados {len(eventos)} eventos")
        
        # Mapeo de campos para ordenación
        sort_map = {
            'curso': 'curso_nombre',
            'fecha': 'fecha_evento',
            'estatus': 'estatus',
            'instructor': 'instructor_nombre'
        }
        
        # Obtener el campo real para ordenar
        sort_field = sort_map.get(sort_by, 'fecha_evento')
        
        # Función para obtener el valor por el cual ordenar
        def get_sort_key(evento):
            value = evento.get(sort_field)
            if value is None:
                return ''
            # Si es una fecha, ya es un objeto datetime
            return value
        
        # Ordenar los eventos
        reverse = (order == 'desc')
        eventos.sort(key=get_sort_key, reverse=reverse)
        
        print(f"DEBUG: Ordenando por {sort_field} en orden {order}")
        
        return render_template('admin/eventos.html', 
                             eventos=eventos, 
                             sort_by=sort_by, 
                             order=order,
                             filter_type=filter_type,
                             filter_value=filter_value)
        
    except Exception as e:
        print(f"ERROR en gestion_eventos: {e}")
        import traceback
        traceback.print_exc()
        flash("Error al cargar la gestión de eventos", 'error')
        return redirect(url_for('admin.admin_dashboard'))




# =============================================================================
# GESTIÓN DE ALUMNOS
# =============================================================================

@admin_bp.route('/buscar_alumno')
@admin_required
def buscar_alumno():
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'exists': False})
        
        # ✅ Cambio: Usar db en lugar de Database
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
        print(f'ERROR en buscar_alumno: {e}')
        return jsonify({'exists': False, 'error': str(e)})

@admin_bp.route('/alumnos')
@admin_required
def gestion_alumnos():
    # ✅ Cambio: Usar db en lugar de Database
    alumnos = list(db.get_alumnos())
    cursos = list(db.get_cursos_activos())
    return render_template('admin/alumnos.html', alumnos=alumnos, cursos=cursos)

@admin_bp.route('/alumno/agregar', methods=['POST'])
@admin_required
def agregar_alumno():
    try:
        email = request.form.get('email')
        nombre = request.form.get('nombre')
        curso = request.form.get('curso')
        
        if not email or not nombre or not curso:
            flash('Todos los campos son requeridos', 'error')
            return redirect(url_for('admin.gestion_alumnos'))
        
        alumno_data = {
            'email': email,
            'nombre': nombre,
            'curso': curso,
            'fecha_registro': datetime.now()
        }
        
        # ✅ Cambio: Usar db en lugar de Database
        alumno_existente = db.get_alumno_by_email(email)
        if alumno_existente:
            flash('El alumno con este email ya existe', 'error')
            return redirect(url_for('admin.gestion_alumnos'))
        
        result = db.insert_alumno(alumno_data)
        flash('Alumno agregado exitosamente', 'success')
        
    except Exception as e:
        print(f"ERROR al agregar alumno: {e}")
        flash(f'Error al agregar alumno: {str(e)}', 'error')
    
    return redirect(url_for('admin.gestion_alumnos'))

@admin_bp.route('/alumno/eliminar/<email>')
@admin_required
def eliminar_alumno(email):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        db.delete_alumno(email)
        flash('Alumno eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar alumno: {str(e)}', 'error')
    
    return redirect(url_for('admin.gestion_alumnos'))

@admin_bp.route('/registrar_alumno_sistema', methods=['POST'])
@admin_required
def registrar_alumno_sistema():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        email = data.get('email')
        telefono = data.get('telefono', '')
        
        if not nombre or not email:
            return jsonify({'success': False, 'message': 'Nombre y email son requeridos'})
        
        # ✅ Cambio: Usar db en lugar de Database
        alumno_existente = db.get_alumno_by_email(email)
        if alumno_existente:
            return jsonify({'success': False, 'message': 'El alumno ya está registrado en el sistema'})
        
        password_default = "minda123"
        hashed_password = generate_password_hash(password_default)
        
        alumno_data = {
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'password': hashed_password,
            'curso': '',
            'fecha_registro': datetime.now()
        }
        
        db.insert_alumno(alumno_data)
        return jsonify({'success': True, 'message': 'Alumno registrado en el sistema exitosamente'})
        
    except Exception as e:
        print(f"ERROR en registrar_alumno_sistema: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@admin_bp.route('/evento/<evento_id>/agregar_alumno', methods=['POST'])
@admin_required
def agregar_alumno_evento(evento_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return jsonify({'success': False, 'message': 'Evento no encontrado'})

        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        telefono = request.form.get('telefono', '')

        print(f"DEBUG: Datos recibidos - nombre: {nombre}, email: {email}, telefono: {telefono}")

        if not nombre or not email:
            return jsonify({'success': False, 'message': 'Nombre y email son requeridos'})

        # Buscar alumno existente
        alumno_existente = db.get_alumno_by_email(email)
        print(f"DEBUG: Alumno existente: {alumno_existente}")

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
            print(f"DEBUG: Nuevo alumno creado: {email}")
        else:
            # Actualizar teléfono si se proporcionó uno nuevo
            if telefono and alumno_existente and alumno_existente.get('telefono') != telefono:
                db.update_alumno(email, {'telefono': telefono})
                print(f"DEBUG: Teléfono actualizado para alumno: {email}")

        # Preparar datos del alumno para el evento
        alumno_evento = {
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'fecha_inscripcion': datetime.now()
        }

        alumnos_actuales = evento.get('alumnos_asignados', [])
        print(f"DEBUG: Alumnos actuales en evento: {len(alumnos_actuales)}")
        
        # Verificar si el alumno ya está inscrito
        alumno_ya_inscrito = any(alumno.get('email') == email for alumno in alumnos_actuales)
        if alumno_ya_inscrito:
            return jsonify({'success': False, 'message': 'El alumno ya está inscrito en este evento'})

        # Agregar alumno al evento
        alumnos_actuales.append(alumno_evento)
        # Limpiar alumnos vacíos si existen
        alumnos_limpios = [alumno for alumno in alumnos_actuales if alumno.get('email')]
        db.update_evento(evento_id, {'alumnos_asignados': alumnos_limpios})
        print(f"DEBUG: Alumno agregado al evento. Total ahora: {len(alumnos_actuales)}")

        # Actualizar métricas del evento
        actualizar_metricas_evento(evento_id)

        return jsonify({
            'success': True,
            'message': f'Alumno {nombre} agregado al evento exitosamente',
            'total_alumnos': len(alumnos_actuales)
        })

    except Exception as e:
        print(f'ERROR en agregar_alumno_evento: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@admin_bp.route('/evento/<evento_id>/eliminar-alumno/<email>')
@admin_required
def eliminar_alumno_evento(evento_id, email):
    try:
        print(f"DEBUG: Eliminando alumno {email} del evento {evento_id}")
        
        # ✅ Cambio: Usar db en lugar de Database
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash('Evento no encontrado', 'error')
            return redirect(url_for('admin.agenda'))

        alumnos_actuales = evento.get('alumnos_asignados', [])
        
        # Filtrar la lista de alumnos, removiendo el alumno con el email proporcionado
        nuevos_alumnos = [alumno for alumno in alumnos_actuales if alumno.get('email') != email]
        
        if len(nuevos_alumnos) == len(alumnos_actuales):
            flash('El alumno no estaba inscrito en este evento', 'warning')
        else:
            db.update_evento(evento_id, {'alumnos_asignados': nuevos_alumnos})
            flash('Alumno eliminado del evento exitosamente', 'success')
            
            # Actualizar métricas del evento
            actualizar_metricas_evento(evento_id)

        return redirect(url_for('eventos.alumnos_evento', evento_id=evento_id))
        
    except Exception as e:
        print(f'ERROR en eliminar_alumno_evento: {e}')
        flash('Error al eliminar alumno del evento', 'error')
        return redirect(url_for('eventos.alumnos_evento', evento_id=evento_id))

@admin_bp.route('/evento/<evento_id>/editar-alumno', methods=['POST'])
@admin_required
def editar_alumno_evento(evento_id):
    try:
        email_original = request.form.get('email_original')
        nuevo_email = request.form.get('nuevo_email')
        nuevo_nombre = request.form.get('nuevo_nombre')
        nuevo_telefono = request.form.get('nuevo_telefono', '')

        print(f"DEBUG: Editando alumno - Original: '{email_original}', Nuevo: '{nuevo_email}'")

        if not email_original or not nuevo_email or not nuevo_nombre:
            return jsonify({'success': False, 'message': 'Email original, nuevo email y nombre son requeridos'})

        # Normalizar emails
        email_original = email_original.strip().lower()
        nuevo_email = nuevo_email.strip().lower()

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
        print(f"DEBUG: Resultado actualización alumno: {resultado_alumno}")

        # Actualizar alumno en TODOS los eventos donde esté registrado
        todos_eventos = db.get_eventos()
        eventos_actualizados = 0
        
        print(f"DEBUG: Buscando en {len(todos_eventos)} eventos totales")
        
        for evento in todos_eventos:
            alumnos_evento = evento.get('alumnos_asignados', [])
            alumno_encontrado = False
            
            # Filtrar alumnos vacíos
            alumnos_evento = [alumno for alumno in alumnos_evento if alumno.get('email')]
            
            for i, alumno in enumerate(alumnos_evento):
                # Comparar emails de forma case-insensitive y sin espacios
                alumno_email = alumno.get('email', '').strip().lower()
                if alumno_email == email_original:
                    print(f"DEBUG: Encontrado alumno en evento {evento.get('_id')} - posición {i}")
                    alumno['nombre'] = nuevo_nombre
                    alumno['email'] = nuevo_email
                    alumno['telefono'] = nuevo_telefono
                    alumno_encontrado = True
                    break
            
            if alumno_encontrado:
                resultado = db.update_evento(str(evento['_id']), {'alumnos_asignados': alumnos_evento})
                print(f"DEBUG: Resultado actualización evento {evento.get('_id')}: {resultado}")
                if resultado:
                    eventos_actualizados += 1

        print(f"DEBUG: Alumno actualizado en {eventos_actualizados} eventos")

        return jsonify({
            'success': True, 
            'message': f'Alumno actualizado exitosamente. Actualizado en {eventos_actualizados} eventos.'
        })

    except Exception as e:
        print(f'ERROR en editar_alumno_evento: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# =============================================================================
# GESTIÓN DE INSTRUCTORES
# =============================================================================

@admin_bp.route('/gestion_instructores')
@admin_required
def gestion_instructores():
    try:
        # ✅ Variable correctamente definida
        instructores = list(db.get_instructores())
        todos_eventos = db.get_eventos()

        print(f"DEBUG: Encontrados {len(instructores)} instructores")
        print(f"DEBUG: Encontrados {len(todos_eventos)} eventos")

        for instructor in instructores:
            eventos_asignados = []
            for evento in todos_eventos:
                try:
                    evento_instructor_id = evento.get('instructor_id')
                    evento_instructor_email = evento.get('instructor_email')
                    instructor_id_str = str(instructor['_id'])

                    if (evento_instructor_id == instructor_id_str or
                        evento_instructor_email == instructor.get('email')):

                        curso_nombre = 'Curso no especificado'
                        if 'curso_id' in evento:
                            curso = db.get_curso_by_id(evento['curso_id'])
                            if curso:
                                curso_nombre = curso.get('nombre', 'Curso sin nombre')

                        fecha_evento = 'Fecha no especificada'
                        if 'fecha_evento' in evento:
                            if isinstance(evento['fecha_evento'], datetime):
                                fecha_evento = evento['fecha_evento'].strftime('%d/%m/%Y')
                            else:
                                fecha_evento = str(evento['fecha_evento'])
                        alumnos_count = len(evento.get('alumnos_asignados', []))

                        evento_info = {
                            'id': str(evento['_id']),
                            'nombre': evento.get('nombre', 'Evento sin nombre'),
                            'curso_nombre': curso_nombre,
                            'estatus': evento.get('estatus', 'desconocido'),
                            'fecha': fecha_evento,
                            'alumnos_count': alumnos_count,
                            'url_alumnos': url_for('eventos.alumnos_evento', evento_id=str(evento['_id']))
                        }
                        eventos_asignados.append(evento_info)
                except Exception as e:
                    print(f"Error procesando evento para instructor {instructor.get('nombre', 'N/A')}: {e}")
                    continue

            instructor['eventos_asignados'] = eventos_asignados

        # ✅ RETURN CORREGIDO - variable correcta
        return render_template('admin/gestion_instructores.html', instructores=instructores)

    except Exception as e:
        print(f"ERROR en gestion_instructores: {e}")
        import traceback
        traceback.print_exc()
        flash("Error al cargar la gestión de instructores", 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/instructor/agregar', methods=['POST'])
@admin_required
def agregar_instructor():
    try:
        instructor_data = {
            'email': request.form.get('email'),
            'nombre': request.form.get('nombre'),
            'especialidad': request.form.get('especialidad'),
            'cursos': [],
            'fecha_registro': datetime.now()
        }
        
        # ✅ Cambio: Usar db en lugar de Database
        if db.get_instructor_by_email(instructor_data['email']):
            flash('El instructor con este email ya existe', 'error')
            return redirect(url_for('admin.gestion_instructores'))
        
        db.insert_instructor(instructor_data)
        flash('Instructor agregado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al agregar instructor: {str(e)}', 'error')
    
    return redirect(url_for('admin.gestion_instructores'))

@admin_bp.route('/instructor/eliminar/<email>')
@admin_required
def eliminar_instructor(email):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        db.delete_instructor(email)
        flash('Instructor eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar instructor: {str(e)}', 'error')
    
    return redirect(url_for('admin.gestion_instructores'))

@admin_bp.route('/asignar_instructor_evento', methods=['POST'])
def asignar_instructor_evento():
    try:
        # Obtener datos como JSON
        data = request.get_json()
        
        evento_id = data.get('evento_id')
        instructor_email = data.get('instructor_email')
        instructor_nombre = data.get('instructor_nombre')
        
        print(f"DEBUG RUTA: Datos recibidos - evento_id: {evento_id}, instructor_email: {instructor_email}, instructor_nombre: {instructor_nombre}")
        
        # Validar datos requeridos
        if not evento_id:
            print("DEBUG RUTA: Error - evento_id vacío")
            return jsonify({'success': False, 'message': 'ID del evento no válido'}), 400
            
        if not instructor_email:
            print("DEBUG RUTA: Error - instructor_email vacío")
            return jsonify({'success': False, 'message': 'Por favor seleccione un instructor'}), 400
        
        print(f"DEBUG RUTA: Llamando a db.update_evento_instructor...")
        
        # ✅ Cambio: Usar db en lugar de Database
        result = db.update_evento_instructor(evento_id, instructor_email, instructor_nombre)
        
        print(f"DEBUG RUTA: Resultado de update_evento_instructor: {result}")
        
        if result:
            print(f"DEBUG RUTA: Éxito - Instructor asignado")
            return jsonify({
                'success': True, 
                'message': f'Instructor {instructor_nombre} asignado correctamente al evento'
            })
        else:
            print(f"DEBUG RUTA: Fallo - No se pudo actualizar la base de datos")
            return jsonify({
                'success': False, 
                'message': 'Error al asignar instructor - no se pudo actualizar la base de datos'
            }), 500
            
    except Exception as e:
        print(f"DEBUG RUTA: Error general: {str(e)}")
        import traceback
        print(f"DEBUG RUTA: Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'message': 'Error interno del servidor al asignar instructor'
        }), 500

# =============================================================================
# GESTIÓN DE CURSOS
# =============================================================================

@admin_bp.route('/cursos')
@admin_required
def gestion_cursos():
    try:
        from bson import ObjectId

        # ✅ Cambio: Usar db en lugar de Database
        cursos = list(db.get_cursos_activos())
        instructores = list(db.get_instructores())

        print(f"DEBUG: Encontrados {len(cursos)} cursos")

        # Procesar información de cursos
        cursos_con_info = []
        for curso in cursos:
            curso_id_str = str(curso['_id'])
            curso_object_id = ObjectId(curso_id_str)

            # Verificar evaluación y cuestionario
            tiene_evaluacion = 'evaluacion' in curso and curso['evaluacion'] is not None
            tiene_cuestionario = 'cuestionario' in curso and curso['cuestionario'] is not None

            print(f"DEBUG: Procesando curso: {curso.get('nombre')}")
            print(f"DEBUG - Curso ID (string): {curso_id_str}")
            print(f"DEBUG - Curso ID (ObjectId): {curso_object_id}")
            print(f"DEBUG - Evaluación: {tiene_evaluacion}, Cuestionario: {tiene_cuestionario}")

            # Contar eventos
            try:
                # ✅ Cambio: Usar db en lugar de Database
                total_eventos = db.db.Eventos.count_documents({
                    'curso_id': curso_object_id
                })
                print(f"DEBUG: Eventos encontrados para curso {curso_id_str}: {total_eventos}")
            except Exception as e:
                print(f"Error contando eventos: {e}")
                total_eventos = 0

            curso_info = {
                'id': curso_id_str,
                'nombre': curso.get('nombre', 'Sin nombre'),
                'descripcion': curso.get('descripcion', ''),
                'instructor_id': curso.get('instructor_id'),
                'total_eventos': total_eventos,
                'fecha_creacion': curso.get('fecha_creacion'),
                'estado': curso.get('estado', 'activo'),
                'tiene_evaluacion': tiene_evaluacion,
                'tiene_cuestionario': tiene_cuestionario,
                'evaluacion_obj': curso.get('evaluacion'),
                'cuestionario_obj': curso.get('cuestionario')
            }
            cursos_con_info.append(curso_info)

        return render_template('admin/cursos.html',
            cursos=cursos_con_info,
            instructores=instructores)

    except Exception as e:
        print(f"ERROR en gestion_cursos: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error al cargar la gestión de cursos', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/curso/agregar', methods=['POST'])
@admin_required
def agregar_curso():
    try:
        curso_data = {
            'nombre': request.form.get('nombre'),
            'description': request.form.get('description'),
            'horas_totales': int(request.form.get('horas_totales')),
            'dias_duracion': int(request.form.get('dias_duracion')),
            'estatus': 'activo',
            'fecha_creacion': datetime.now()
        }

        # ✅ Cambio: Usar db en lugar de Database
        result = db.insert_curso(curso_data)
        curso_id = result.inserted_id

        # Crear evaluación del taller por defecto
        estructura_evaluacion = {
            'escala': '(1) Muy mal (2) Mal (3) Regular (4) Bien (5) Muy Bien (6) Excelente',
            'secciones': {
                'taller': [
                    {'numero': '1', 'texto': 'El tiempo para el taller fue suficiente'},
                    {'numero': '2', 'texto': 'El material proporcionado'},
                    {'numero': '3', 'texto': 'El apoyo didáctico videoconferencia'},
                    {'numero': '4', 'texto': 'La calidad de la videoconferencia'},
                    {'numero': '5', 'texto': 'El horario fue adecuado'},
                    {'numero': '6', 'texto': 'Los ejemplos facilitaron la comprensión'}
                ],
                'instructor': [
                    {'numero': '2.1', 'texto': 'Dominio del tema'},
                    {'numero': '2.2', 'texto': 'Exposición clara'},
                    {'numero': '2.3', 'texto': 'Resolución de dudas'},
                    {'numero': '2.4', 'texto': 'Motivo la participación'},
                    {'numero': '2.5', 'texto': 'Disposición durante el taller'},
                    {'numero': '2.6', 'texto': 'La puntualidad en el taller'}
                ],
                'comentarios': 'Por favor proporciónanos un comentario de este taller'
            }
        }

        preguntas_estandar = []

        for pregunta in estructura_evaluacion['secciones']['taller']:
            preguntas_estandar.append({
                'tipo': 'escala',
                'seccion': 'taller',
                'numero': pregunta['numero'],
                'pregunta': pregunta['texto'],
                'opciones': ['1', '2', '3', '4', '5', '6']
            })

        for pregunta in estructura_evaluacion['secciones']['instructor']:
            preguntas_estandar.append({
                'tipo': 'escala',
                'seccion': 'instructor',
                'numero': pregunta['numero'],
                'pregunta': pregunta['texto'],
                'opciones': ['1', '2', '3', '4', '5', '6']
            })

        preguntas_estandar.append({
            'tipo': 'texto_largo',
            'seccion': 'comentarios',
            'numero': '',
            'pregunta': estructura_evaluacion['secciones']['comentarios']
        })

        evaluacion_data = {
            'curso_id': curso_id,
            'nombre': f"Evaluación del Taller - {curso_data['nombre']}",
            'tipo_examen': 'evaluacion_taller',
            'descripcion': 'Evaluación de satisfacción del taller e instructor',
            'estructura': estructura_evaluacion,
            'preguntas': preguntas_estandar,
            'formato_especifico': True,
            'fecha_creacion': datetime.now()
        }

        # NOTA: El método insert_examen no está definido en tu Database
        # Necesitarías implementarlo o comentar esta parte
        # evaluacion_result = db.insert_examen(evaluacion_data)
        
        db.update_curso(str(curso_id), {
            'evaluacion': evaluacion_data 
        })

        flash('Curso agregado exitosamente. Se ha creado la evaluación del taller por defecto.', 'success')
        
    except Exception as e:
        flash(f'Error al agregar curso: {str(e)}', 'error')

    return redirect(url_for('admin.gestion_cursos'))

@admin_bp.route('/curso/eliminar/<curso_id>')
@admin_required
def eliminar_curso(curso_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        db.delete_curso(curso_id)
        flash('Curso eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar curso: {str(e)}', 'error')
    return redirect(url_for('admin.gestion_cursos'))

@admin_bp.route('/curso/<curso_id>/cargar_cuestionario', methods=['POST'])
@admin_required
def cargar_cuestionario_curso(curso_id):
    try:
        if 'archivo_csv' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('admin.gestion_cursos'))

        archivo = request.files['archivo_csv']
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('admin.gestion_cursos'))

        if not archivo.filename.endswith('.csv'):
            flash('El archivo debe ser un CSV', 'error')
            return redirect(url_for('admin.gestion_cursos'))

        # ✅ Cambio: Usar db en lugar de Database
        curso = db.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('admin.gestion_cursos'))

        contenido = archivo.stream.read().decode('utf-8')
        lineas = contenido.split('\n')
        
        preguntas_data = []

        for linea in lineas[1:]:
            if linea.strip():
                partes = linea.strip().split(';')
                if len(partes) >= 5:
                    numero_pregunta = partes[0].strip()
                    pregunta_texto = partes[1].strip()
                    tipo_respuesta = partes[2].strip().lower()
                    
                    if tipo_respuesta == 'opcion_multiple':
                        opciones_str = partes[3].strip()
                        respuesta_correcta = partes[4].strip()
                        
                        opciones = [opcion.strip() for opcion in opciones_str.split('|')]
                        
                        if pregunta_texto and opciones and respuesta_correcta:
                            preguntas_data.append({
                                'numero': numero_pregunta,
                                'tipo': 'opcion_multiple',
                                'pregunta': pregunta_texto,
                                'opciones': opciones,
                                'respuesta_correcta': respuesta_correcta
                            })

        cuestionario_data = {
            'nombre': f"Cuestionario - {curso['nombre']}",
            'tipo_examen': 'cuestionario',
            'preguntas': preguntas_data,
            'fecha_creacion': datetime.now()
        }

        db.update_curso(curso_id, {
            'cuestionario': cuestionario_data
        })
        flash(f'Cuestionario cargado exitosamente con {len(preguntas_data)} preguntas', 'success')

    except Exception as e:
        print(f"ERROR CRÍTICO en cargar_cuestionario_curso: {e}")
        flash(f'Error al cargar cuestionario: {str(e)}', 'error')

    return redirect(url_for('admin.gestion_cursos'))

@admin_bp.route('/curso/<curso_id>/evento/crear', methods=['POST'])
@admin_required
def crear_evento_curso(curso_id):
    try:
        print(f"DEBUG: Creando evento para curso_id: {curso_id}")
        print(f"DEBUG: Datos del formulario: {dict(request.form)}")
        print(f"🔍 DEBUG COMPLETO:")
        print(f"🔍 curso_id desde URL: {curso_id}")
        print(f"🔍 Tipo de curso_id: {type(curso_id)}")
        print(f"🔍 request.view_args: {request.view_args}")
        print(f"🔍 request.path: {request.path}")

        fecha_evento = request.form.get('fecha_evento')
        instructor_email = request.form.get('instructor_email')

        if not fecha_evento:
            flash('La fecha del evento es requerida', 'error')
            return redirect(url_for('admin.gestion_cursos'))
        
        # ✅ Usar directamente el curso_id de la URL
        if not curso_id:
            flash('ID de curso no válido', 'error')
            return redirect(url_for('admin.gestion_cursos'))

        # ✅ Cambio: Usar db en lugar de Database
        curso = db.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('admin.gestion_cursos'))

        # Si se proporcionó un instructor, obtener sus datos
        instructor_id = None
        instructor_nombre = None
        if instructor_email:
            instructor = db.get_instructor_by_email(instructor_email)
            if instructor:
                instructor_id = str(instructor['_id'])  # ✅ Usar '_id' en lugar de 'id'
                instructor_nombre = instructor['nombre']

        evento_data = {
            'curso_id': ObjectId(curso_id),
            'curso_nombre': curso['nombre'],
            'fecha_evento': datetime.strptime(fecha_evento, '%Y-%m-%d'),
            'instructor_id': instructor_id,
            'instructor_email': instructor_email,
            'instructor_nombre': instructor_nombre,
            'alumnos_asignados': [],
            'estatus': 'abierto',
            'fecha_creacion': datetime.now(),
            'total_alumnos': 0,
            'cuestionarios_contestados': 0,
            'promedio_cuestionarios': 0,
            'evaluaciones_contestadas': 0,
            'promedio_evaluaciones': 0,
            'cuestionarios_detalle': [],
            'evaluaciones_detalle': []
        }

        db.insert_evento(evento_data)
        flash('Evento creado exitosamente con estatus: ABIERTO', 'success')

    except Exception as e:
        print(f"ERROR en crear_evento_curso: {e}")
        flash(f'Error al crear evento: {str(e)}', 'error')

    return redirect(url_for('admin.gestion_cursos'))



# =============================================================================
# VISTAS DE EVALUACIÓN Y CUESTIONARIOS DE CURSOS
# =============================================================================

@admin_bp.route('/curso/<curso_id>/ver_evaluacion')
@admin_required
def ver_evaluacion_curso(curso_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        curso = db.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('admin.gestion_cursos'))
        
        # Verificar si el curso tiene evaluación
        if 'evaluacion' not in curso:
            flash('Este curso no tiene evaluación configurada', 'warning')
            return redirect(url_for('admin.gestion_cursos'))
        
        evaluacion = curso['evaluacion']
        return render_template('admin/ver_evaluacion_curso.html', 
                             curso=curso, 
                             evaluacion=evaluacion)
                             
    except Exception as e:
        print(f"ERROR al cargar evaluación del curso: {e}")
        flash('Error al cargar la evaluación del curso', 'error')
        return redirect(url_for('admin.gestion_cursos'))

@admin_bp.route('/curso/<curso_id>/ver_cuestionario')
@admin_required
def ver_cuestionario_curso(curso_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        curso = db.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('admin.gestion_cursos'))
        
        # Verificar si el curso tiene cuestionario
        if 'cuestionario' not in curso:
            flash('Este curso no tiene cuestionario configurado', 'warning')
            return redirect(url_for('admin.gestion_cursos'))
        
        cuestionario = curso['cuestionario']
        return render_template('admin/ver_cuestionario_curso.html', 
                             curso=curso, 
                             cuestionario=cuestionario)
                             
    except Exception as e:
        print(f"ERROR al cargar cuestionario del curso: {e}")
        flash('Error al cargar el cuestionario del curso', 'error')
        return redirect(url_for('admin.gestion_cursos'))

@admin_bp.route('/agenda')
@admin_required
def agenda():
    try:
        year = request.args.get('year', default=datetime.now().year, type=int)
        month = request.args.get('month', default=datetime.now().month, type=int)

        print(f"DEBUG AGENDA: Año solicitado: {year}, Mes solicitado: {month}")

        # Validar mes
        if not (1 <= month <= 12):
            month = datetime.now().month
        if year < 2020 or year > 2030:
            year = datetime.now().year

        # ✅ Cambio: Usar db en lugar de Database
        eventos = list(db.get_eventos_by_mes(year, month))

        print(f"DEBUG AGENDA: Eventos encontrados: {len(eventos)}")

        for evento in eventos:
            print(f"DEBUG AGENDA: Evento - {evento.get('curso_nombre')} - Fecha: {evento.get('fecha_evento')}")

        # Procesar eventos para el template
        for evento in eventos:
            if not evento.get('nombre') and evento.get('curso_nombre'):
                evento['nombre'] = evento['curso_nombre']

            evento.setdefault('total_alumnos', len(evento.get('alumnos_asignados', [])))
            evento.setdefault('cuestionarios_contestados', 0)
            evento.setdefault('evaluaciones_contestadas', 0)
            evento.setdefault('promedio_cuestionarios', 0)
            evento.setdefault('promedio_evaluaciones', 0)
            evento.setdefault('estatus', 'abierto')

        meses = [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]

        años = list(range(2020, 2031))
        instructores = list(db.get_instructores())
        print(f"DEBUG: Se encontraron {len(instructores)} instructores")

        return render_template('admin/agenda.html',
            eventos=eventos,
            mes_actual=month,
            año_actual=year,
            meses=meses,
            años=años,
            instructores=instructores)

    except Exception as e:
        print(f"ERROR en agenda: {e}")
        import traceback
        traceback.print_exc()

        meses = [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]

        años = list(range(2020, 2031))

        flash('Error al cargar la agenda', 'error')
        return render_template('admin/agenda.html',
            eventos=[],
            mes_actual=datetime.now().month,
            año_actual=datetime.now().year,
            meses=meses,
            años=años,
            instructores=[])
                             
    except Exception as e:
        print(f"ERROR en agenda: {str(e)}")
        flash('Error al cargar la agenda de eventos', 'error')
        return render_template('admin/agenda.html',
                             eventos=[],
                             meses=[],
                             años=[],
                             mes_actual=datetime.now().month,
                             año_actual=datetime.now().year)

def calcular_estadisticas_evento(evento):
    """Calcula estadísticas de cuestionarios y evaluaciones para un evento"""
    try:
        evento_id = str(evento.get('_id', ''))
        curso_id = str(evento.get('curso_id', ''))
        
        # Valores por defecto
        stats = {
            'total_alumnos': 0,
            'cuestionarios_contestados': 0,
            'evaluaciones_registradas': 0,
            'promedio_cuestionarios': 0,
            'promedio_evaluaciones': 0
        }
        
        # Obtener alumnos del evento
        alumnos = evento.get('alumnos_asignados', [])
        total_alumnos = len(alumnos)
        stats['total_alumnos'] = total_alumnos
        
        if total_alumnos == 0 or not curso_id:
            return stats
        
        # Contadores para promedios
        total_cuestionarios = 0
        total_evaluaciones = 0
        suma_cuestionarios = 0
        suma_evaluaciones = 0
        
        # Revisar cada alumno
        for alumno in alumnos:
            email = alumno.get('email')
            if not email:
                continue
                
            # Cuestionarios del alumno
            cuestionarios = list(db.get_cuestionarios_by_alumno_and_curso(email, curso_id))
            if cuestionarios:
                total_cuestionarios += 1
                for cuestionario in cuestionarios:
                    suma_cuestionarios += cuestionario.get('calificación', 0)
            
            # Evaluaciones del alumno  
            evaluaciones = list(db.get_evaluaciones_by_alumno_and_curso(email, curso_id))
            if evaluaciones:
                total_evaluaciones += 1
                for evaluacion in evaluaciones:
                    suma_evaluaciones += evaluacion.get('promedio_general', 0)
        
        # Calcular promedios
        stats.update({
            'cuestionarios_contestados': total_cuestionarios,
            'evaluaciones_registradas': total_evaluaciones,
            'promedio_cuestionarios': round(suma_cuestionarios / total_cuestionarios, 1) if total_cuestionarios > 0 else 0,
            'promedio_evaluaciones': round(suma_evaluaciones / total_evaluaciones, 1) if total_evaluaciones > 0 else 0
        })
        
        return stats
        
    except Exception as e:
        print(f"ERROR en calcular_estadisticas_evento: {str(e)}")
        return stats

def actualizar_metricas_evento(evento_id):
    """Actualiza las métricas de un evento"""
    try:
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return
        
        total_alumnos = len(evento.get('alumnos_asignados', []))
        cuestionarios = evento.get('cuestionarios_detalle', [])
        evaluaciones = evento.get('evaluaciones_detalle', [])
        
        # Calcular promedios como float directamente
        promedio_cuestionarios = 0.0
        promedio_evaluaciones = 0.0
        
        if cuestionarios:
            suma_cuestionarios = sum(q.get('calificacion', 0) for q in cuestionarios)
            promedio_cuestionarios = float(suma_cuestionarios / len(cuestionarios))
        
        if evaluaciones:
            suma_evaluaciones = sum(e.get('puntuacion_promedio', 0) for e in evaluaciones)
            promedio_evaluaciones = float(suma_evaluaciones / len(evaluaciones))
        
        db.update_evento(evento_id, {
            'total_alumnos': total_alumnos,
            'cuestionarios_contestados': len(cuestionarios),
            'evaluaciones_contestadas': len(evaluaciones),
            'promedio_cuestionarios': promedio_cuestionarios,  # Float directo
            'promedio_evaluaciones': promedio_evaluaciones     # Float directo
        })
        
    except Exception as e:
        print(f"ERROR en actualizar_metricas_evento: {e}")

# =============================================================================
# ESTADÍSTICAS Y GRÁFICAS PARA EVENTOS
# =============================================================================

@admin_bp.route('/evento/<evento_id>/estadisticas-graficas')
@admin_required
def estadisticas_graficas_evento(evento_id):
    """Endpoint para obtener datos de gráficas para un evento específico"""
    try:
        print(f"DEBUG [estadisticas_graficas_evento]: Solicitando para evento: {evento_id}")
        
        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return jsonify({'success': False, 'message': 'Evento no encontrado'}), 404
        
        # Verificar datos
        print(f"DEBUG: Evento: {evento.get('curso_nombre')}")
        print(f"DEBUG: Alumnos asignados: {len(evento.get('alumnos_asignados', []))}")
        print(f"DEBUG: Cuestionarios: {len(evento.get('cuestionarios_detalle', []))}")
        print(f"DEBUG: Evaluaciones: {len(evento.get('evaluaciones_detalle', []))}")
        
        # Usar la función generar_datos_graficas
        from routes_eventos import generar_datos_graficas
        datos_graficas = generar_datos_graficas(evento)
        
        # Verificar resultados
        print(f"DEBUG: Resultado - Cuestionarios: {'SÍ' if datos_graficas.get('cuestionarios') else 'NO'}")
        print(f"DEBUG: Resultado - Evaluaciones: {'SÍ' if datos_graficas.get('evaluaciones') else 'NO'}")
        print(f"DEBUG: Resultado - Alumnos: {'SÍ' if datos_graficas.get('alumnos') else 'NO'}")
        
        # Si no hay datos de alumnos pero hay alumnos asignados, crear datos mínimos
        if not datos_graficas.get('alumnos') and evento.get('alumnos_asignados'):
            print("DEBUG: Creando datos mínimos para gráfica de alumnos")
            
            labels = []
            for alumno in evento.get('alumnos_asignados', []):
                labels.append(alumno.get('nombre', alumno.get('email', '').split('@')[0]))
            
            # Valores por defecto basados en el promedio
            promedio = evento.get('promedio_cuestionarios', 65)
            datos_graficas['alumnos'] = {
                'labels': labels,
                'datasets': [{
                    'label': 'Calificación (%)',
                    'data': [promedio] * len(labels),
                    'backgroundColor': ['#0d6efd', '#6f42c1'][:len(labels)],
                    'borderColor': ['#0d6efd', '#6f42c1'][:len(labels)],
                    'borderWidth': 1
                }]
            }
        
        return jsonify({
            'success': True,
            'datos': datos_graficas,
            'message': 'Datos procesados correctamente'
        })
        
    except Exception as e:
        print(f"ERROR en estadisticas_graficas_evento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al obtener estadísticas: {str(e)}'
        }), 500


def obtener_datos_alumnos_grafica(evento_id, alumnos_emails):
    """Obtiene los datos para la gráfica de calificación por alumno"""
    try:
        if not alumnos_emails:
            return None
        
        labels = []
        calificaciones = []
        colores = []
        
        for email in alumnos_emails:
            # ✅ Buscar en la colección Alumnos
            alumno = db.Alumnos.find_one({'email': email})
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

def actualizar_metricas_evento(evento_id):
    """Actualiza las métricas de un evento"""
    try:
        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            return False
        
        total_alumnos = len(evento.get('alumnos_asignados', []))
        
        # Calcular promedios
        cuestionarios = evento.get('cuestionarios_detalle', [])
        evaluaciones = evento.get('evaluaciones_detalle', [])
        
        promedio_cuestionarios = 0.0
        promedio_evaluaciones = 0.0
        
        if cuestionarios:
            suma_cuestionarios = sum(q.get('calificacion', 0) for q in cuestionarios)
            promedio_cuestionarios = float(suma_cuestionarios / len(cuestionarios))
        
        if evaluaciones:
            suma_evaluaciones = sum(e.get('puntuacion_promedio', 0) for e in evaluaciones)
            promedio_evaluaciones = float(suma_evaluaciones / len(evaluaciones))
        
        # Actualizar el evento
        db.update_evento(evento_id, {
            'total_alumnos': total_alumnos,
            'cuestionarios_contestados': len(cuestionarios),
            'evaluaciones_contestadas': len(evaluaciones),
            'promedio_cuestionarios': promedio_cuestionarios,
            'promedio_evaluaciones': promedio_evaluaciones
        })
        
        return True
    except Exception as e:
        print(f"ERROR en actualizar_metricas_evento: {e}")
        return False
