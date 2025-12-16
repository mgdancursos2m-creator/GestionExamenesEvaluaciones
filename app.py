from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from bson import ObjectId
from datetime import datetime
import json
import config
from models import Database,db # Se agrega DBpara un enfoque mas simple

app = Flask(__name__)
app.config.from_object(config.Config)

# Función para verificar autenticación
def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('No tienes permisos para acceder a esta página', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validación para admin (no requiere formato de email)
        if email == 'admin' and password == 'nimda':
            session['user'] = 'admin'
            session['role'] = 'admin'
            session['nombre'] = 'Administrador'
            session.permanent = True
            return redirect(url_for('admin_dashboard'))

        # Para usuarios normales (no admin), validar formato de email
        if not email or '@' not in email:
            flash('Por favor, ingresa un correo electrónico válido', 'error')
            return render_template('login.html')

        if not password or len(password) < 4:
            flash('La contraseña debe tener al menos 4 caracteres', 'error')
            return render_template('login.html')

        # Verificar alumno existente
        alumno = Database.get_alumno_by_email(email)
        if alumno:
            session['user'] = email
            session['role'] = 'alumno'
            session['nombre'] = alumno.get('nombre')
            session.permanent = True
            return redirect(url_for('user_dashboard'))

        # Verificar instructor
        instructor = Database.get_instructor_by_email(email)
        if instructor:
            session['user'] = email
            session['role'] = 'instructor'
            session['nombre'] = instructor.get('nombre')
            session.permanent = True
            return redirect(url_for('user_dashboard'))

        # Si el alumno no existe, redirigir al formulario de registro
        return redirect(url_for('registro_alumno', email=email))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/registro-alumno', methods=['GET', 'POST'])
def registro_alumno():
    email = request.args.get('email', '')
    
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            nombre = request.form.get('nombre')
            curso = request.form.get('curso')
            
            print(f"DEBUG: Registrando alumno - Email: {email}, Nombre: {nombre}, Curso: {curso}")

            # Validar campos requeridos
            if not email or not nombre or not curso:
                flash('Todos los campos son requeridos', 'error')
                cursos = list(Database.get_cursos_activos_con_instructor())
                return render_template('registro_alumno.html', email=email, cursos=cursos)

            # Verificar si el alumno ya existe (por si acaso)
            alumno_existente = Database.get_alumno_by_email(email)
            if alumno_existente:
                flash('El alumno con este email ya existe', 'error')
                return redirect(url_for('login'))

            # Crear datos del alumno
            alumno_data = {
                'email': email,
                'nombre': nombre,
                'curso': curso,
                'fecha_registro': datetime.now()
            }

            # Insertar en la base de datos
            result = Database.insert_alumno(alumno_data)
            print(f"DEBUG: Alumno insertado con ID: {result.inserted_id}")

            # Iniciar sesión automáticamente
            session['user'] = email
            session['role'] = 'alumno'
            session['nombre'] = nombre
            session.permanent = True

            flash(f'¡Registro exitoso! Bienvenido/a {nombre}', 'success')
            return redirect(url_for('user_dashboard'))

        except Exception as e:
            print(f"ERROR al registrar alumno: {e}")
            flash(f'Error al registrar alumno: {str(e)}', 'error')
            cursos = list(Database.get_cursos_activos_con_instructor())
            return render_template('registro_alumno.html', email=email, cursos=cursos)

    # GET request - mostrar formulario de registro
    cursos = list(Database.get_cursos_activos_con_instructor())
    return render_template('registro_alumno.html', email=email, cursos=cursos)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

# Rutas de Administrador
@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')

# Gestión de Alumnos
@app.route('/admin/alumnos')
@login_required(role='admin')
def gestion_alumnos():
    alumnos = list(Database.get_alumnos())
    cursos = list(Database.get_cursos_activos())
    return render_template('admin/alumnos.html', alumnos=alumnos, cursos=cursos)

@app.route('/admin/alumno/agregar', methods=['POST'])
@login_required(role='admin')
def agregar_alumno():
    try:
        email = request.form.get('email')
        nombre = request.form.get('nombre')
        curso = request.form.get('curso')
        
        print(f"DEBUG: Intentando agregar alumno - Email: {email}, Nombre: {nombre}, Curso: {curso}")  # Para debug
        
        if not email or not nombre or not curso:
            flash('Todos los campos son requeridos', 'error')
            return redirect(url_for('gestion_alumnos'))
        
        alumno_data = {
            'email': email,
            'nombre': nombre,
            'curso': curso,
            'fecha_registro': datetime.now()
        }
        
        # Verificar si el alumno ya existe
        alumno_existente = Database.get_alumno_by_email(email)
        if alumno_existente:
            flash('El alumno con este email ya existe', 'error')
            return redirect(url_for('gestion_alumnos'))
        
        result = Database.insert_alumno(alumno_data)
        print(f"DEBUG: Alumno insertado con ID: {result.inserted_id}")  # Para debug
        
        flash('Alumno agregado exitosamente', 'success')
        
    except Exception as e:
        print(f"ERROR al agregar alumno: {e}")  # Para debug
        flash(f'Error al agregar alumno: {str(e)}', 'error')
    
    return redirect(url_for('gestion_alumnos'))


@app.route('/admin/alumno/eliminar/<email>')
@login_required(role='admin')
def eliminar_alumno(email):
    try:
        Database.delete_alumno(email)
        flash('Alumno eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar alumno: {str(e)}', 'error')
    
    return redirect(url_for('gestion_alumnos'))

# Gestión de Instructores - Rutas actualizadas
# Ruta para la gestión de instructores
@app.route('/admin/gestion_instructores')
@login_required(role='admin')
def gestion_instructores():
    try:
        # Obtener todos los instructores
        instructores = list(Database.get_instructores())
        
        # Obtener todos los eventos para buscar asignaciones
        try:
            todos_eventos = Database.get_eventos()
        except Exception as e:
            print(f"ERROR: No se pudieron obtener los eventos: {e}")
            todos_eventos = []
        
        # Para cada instructor, buscar eventos asignados
        for instructor in instructores:
            eventos_asignados = []
            
            # Buscar en todos los eventos cuáles están asignados a este instructor
            for evento in todos_eventos:
                try:
                    # Verificar si el evento está asignado a este instructor
                    evento_instructor_id = evento.get('instructor_id')
                    evento_instructor_email = evento.get('instructor_email')
                    instructor_id_str = str(instructor['_id'])
                    
                    # Comparar por ID o por email
                    if (evento_instructor_id == instructor_id_str or 
                        evento_instructor_email == instructor.get('email')):
                        
                        # Obtener información del curso
                        curso_nombre = 'Curso no especificado'
                        if 'curso_id' in evento:
                            curso = Database.get_curso_by_id(evento['curso_id'])
                            if curso:
                                curso_nombre = curso.get('nombre', 'Curso sin nombre')
                        
                        # Formatear fecha si existe
                        fecha_evento = 'Fecha no especificada'
                        if 'fecha_evento' in evento:
                            if isinstance(evento['fecha_evento'], datetime):
                                fecha_evento = evento['fecha_evento'].strftime('%d/%m/%Y')
                            else:
                                fecha_evento = str(evento['fecha_evento'])
                        
                        # Crear objeto de evento con información completa
                        evento_info = {
                            'nombre': evento.get('nombre', 'Evento sin nombre'),
                            'curso_nombre': curso_nombre,
                            'estatus': evento.get('estatus', 'desconocido'),
                            'fecha': fecha_evento
                        }
                        
                        eventos_asignados.append(evento_info)
                except Exception as e:
                    print(f"Error procesando evento para instructor {instructor.get('nombre', 'N/A')}: {e}")
                    continue
            
            instructor['eventos_asignados'] = eventos_asignados
        
        return render_template('admin/gestion_instructores.html', 
                             instructores=instructores)
                             
    except Exception as e:
        print(f"ERROR en gestion_instructores: {e}")
        flash('Error al cargar la gestión de instructores', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/instructor/agregar', methods=['POST'])
@login_required(role='admin')
def agregar_instructor():
    try:
        instructor_data = {
            'email': request.form.get('email'),
            'nombre': request.form.get('nombre'),
            'especialidad': request.form.get('especialidad'),
            'cursos': [],  # Array de cursos que impartirá
            'fecha_registro': datetime.now()
        }
        
        # Verificar si el instructor ya existe
        if Database.get_instructor_by_email(instructor_data['email']):
            flash('El instructor con este email ya existe', 'error')
            return redirect(url_for('gestion_instructores'))
        
        Database.insert_instructor(instructor_data)
        flash('Instructor agregado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al agregar instructor: {str(e)}', 'error')
    
    return redirect(url_for('gestion_instructores'))

#Agregar instructor por evento
@app.route('/admin/asignar_instructor_evento', methods=['GET', 'POST'])
@login_required(role='admin')
def asignar_instructor_evento():
    try:
        if request.method == 'POST':
            instructor_email = request.form.get('instructor_email')
            curso_id = request.form.get('curso_id')
            evento_id = request.form.get('evento_id')
            
            # Validar que todos los campos estén presentes
            if not instructor_email or not curso_id or not evento_id:
                flash('Todos los campos son requeridos', 'error')
                return redirect(url_for('asignar_instructor_evento'))
            
            # Obtener instructor
            instructor = Database.get_instructor_by_email(instructor_email)
            if not instructor:
                flash('Instructor no encontrado', 'error')
                return redirect(url_for('asignar_instructor_evento'))
            
            # Obtener evento
            evento = Database.get_evento_by_id(evento_id)
            if not evento:
                flash('Evento no encontrado', 'error')
                return redirect(url_for('asignar_instructor_evento'))
            
            # Actualizar evento con instructor
            update_data = {
                'instructor_id': str(instructor['_id']),  # Convertir a string
                'instructor_email': instructor_email,
                'instructor_nombre': instructor['nombre']
            }
            
            Database.update_evento(evento_id, update_data)
            flash(f'Instructor {instructor["nombre"]} asignado al evento exitosamente', 'success')
            return redirect(url_for('asignar_instructor_evento'))
        
        # GET request - mostrar formulario
        instructores = list(Database.get_instructores())
        cursos = list(Database.get_cursos_activos())
        
        # Obtener eventos abiertos por curso
        eventos_por_curso = {}
        for curso in cursos:
            eventos_abiertos = Database.get_eventos_abiertos_by_curso(str(curso['_id']))
            eventos_por_curso[str(curso['_id'])] = eventos_abiertos
        
        return render_template('admin/asignar_instructor_evento.html',
                             instructores=instructores,
                             cursos=cursos,
                             eventos_por_curso=eventos_por_curso)
                             
    except Exception as e:
        print(f"ERROR en asignar_instructor_evento: {e}")
        flash('Error al cargar el formulario de asignación', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/instructor/asignar_curso', methods=['POST'])
@login_required(role='admin')
def asignar_curso_instructor():
    try:
        instructor_email = request.form.get('instructor_email')
        curso_id = request.form.get('curso_id')
        
        # Obtener instructor y curso
        instructor = Database.get_instructor_by_email(instructor_email)
        curso = Database.get_curso_by_id(curso_id)
        
        if not instructor or not curso:
            flash('Instructor o curso no encontrado', 'error')
            return redirect(url_for('gestion_instructores'))
        
        # Actualizar el curso con el instructor
        curso_update = {
            'asignado': True,
            'instructor_id': instructor['_id'],
            'instructor_email': instructor_email,
            'instructor_nombre': instructor['nombre']
        }
        Database.update_curso(curso_id, curso_update)
        
        # Actualizar el instructor con el curso
        if 'cursos' not in instructor:
            instructor_update = {'cursos': [ObjectId(curso_id)]}
        else:
            cursos_actuales = instructor['cursos']
            cursos_actuales.append(ObjectId(curso_id))
            instructor_update = {'cursos': cursos_actuales}
        
        Database.update_instructor(instructor_email, instructor_update)
        
        flash(f'Curso "{curso["nombre"]}" asignado exitosamente a {instructor["nombre"]}', 'success')
    except Exception as e:
        flash(f'Error al asignar curso: {str(e)}', 'error')
    
    return redirect(url_for('gestion_instructores'))

#Agenda eventos
@app.route('/admin/agenda')
@login_required(role='admin')
def agenda_eventos():
    try:
        # Obtener parámetros de fecha (mes y año)
        year = request.args.get('year', default=datetime.now().year, type=int)
        month = request.args.get('month', default=datetime.now().month, type=int)
        
        # Validar parámetros
        if not (1 <= month <= 12):
            month = datetime.now().month
        if year < 2020 or year > 2030:
            year = datetime.now().year
            
        eventos = list(Database.get_eventos_by_mes(year, month))
        
        # Generar lista de meses para el selector
        meses = [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]
        
        # Generar lista de años (desde 2020 hasta 2030)
        años = list(range(2020, 2031))
        
        return render_template('admin/agenda.html', 
                             eventos=eventos, 
                             mes_actual=month,
                             año_actual=year,
                             meses=meses,
                             años=años)

    except Exception as e:
        print(f"ERROR en agenda_eventos: {e}")
        
        # Definir las variables necesarias incluso en caso de error
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
                             años=años)



# Gestión de Cursos - Ruta actualizada
@app.route('/admin/cursos')
@login_required(role='admin')
def gestion_cursos():
    try:
        print("DEBUG: Cargando gestión de cursos...")

        # Obtener cursos activos
        cursos = list(Database.get_cursos_activos())
        print(f"DEBUG: Cursos encontrados: {len(cursos)}")

        # Obtener instructores
        instructores = list(Database.get_instructores())
        print(f"DEBUG: Instructores encontrados: {len(instructores)}")

        # Obtener eventos por curso
        eventos_dict = {}
        for curso in cursos:
            eventos_curso = list(Database.get_eventos_by_curso(str(curso['_id'])))
            eventos_dict[str(curso['_id'])] = eventos_curso

        # Enriquecer cada curso con información
        cursos_con_info = []
        
        for curso in cursos:
            try:
                curso_id_str = str(curso['_id'])
                print(f"\nDEBUG: Procesando curso: {curso.get('nombre')} (ID: {curso_id_str})")

                # Obtener total de alumnos para este curso
                total_alumnos = Database.get_total_alumnos_by_curso(curso['nombre'])
                print(f"DEBUG: Total alumnos: {total_alumnos}")

                # Obtener todos los exámenes del curso
                examenes = list(Database.get_examenes_by_curso(curso_id_str))
                print(f"DEBUG: Exámenes encontrados: {len(examenes)}")

                # Separar cuestionarios y evaluaciones
                cuestionarios = [e for e in examenes if e.get('tipo_examen') == 'cuestionario']
                evaluaciones_taller = [e for e in examenes if e.get('tipo_examen') == 'evaluacion_taller']
                print(f"DEBUG: Cuestionarios: {len(cuestionarios)}, Evaluaciones: {len(evaluaciones_taller)}")

                # Obtener evaluaciones completadas
                evaluaciones_completadas = list(Database.get_evaluaciones_by_curso(curso_id_str))
                print(f"DEBUG: Evaluaciones completadas totales: {len(evaluaciones_completadas)}")

                # Obtener CUESTIONARIOS completados
                cuestionarios_completados = list(Database.get_cuestionarios_by_curso(curso_id_str))
                print(f"DEBUG: Cuestionarios completados totales: {len(cuestionarios_completados)}")

                # Filtrar por tipo
                evaluaciones_cuestionarios = list(cuestionarios_completados)
                evaluaciones_taller_completadas = [e for e in evaluaciones_completadas if e.get('tipo_evaluacion') == 'evaluacion_taller']
                
                print(f"DEBUG: Evaluaciones cuestionarios completadas: {len(evaluaciones_cuestionarios)}")
                print(f"DEBUG: Evaluaciones taller completadas: {len(evaluaciones_taller_completadas)}")

                # Calcular promedios
                promedio_cuestionarios = 0
                if evaluaciones_cuestionarios:
                    calificaciones = [e.get('calificación', 0) for e in evaluaciones_cuestionarios if e.get('calificación') is not None]
                    print(f"DEBUG: Calificaciones cuestionarios: {calificaciones}")
                    if calificaciones:
                        promedio_cuestionarios = sum(calificaciones) / len(calificaciones)

                promedio_evaluaciones = 0
                if evaluaciones_taller_completadas:
                    promedios = [e.get('promedio_general', 0) for e in evaluaciones_taller_completadas if e.get('promedio_general') is not None]
                    print(f"DEBUG: Promedios evaluaciones: {promedios}")
                    if promedios:
                        promedio_escala = sum(promedios) / len(promedios)
                        promedio_evaluaciones = (promedio_escala / 6) * 100

                print(f"DEBUG: Promedio cuestionarios: {promedio_cuestionarios}%")
                print(f"DEBUG: Promedio evaluaciones: {promedio_evaluaciones}%")

                # Crear objeto de curso enriquecido
                curso_info = {
                    **curso,
                    'total_eventos': len(eventos_curso),  # Cambiado de total_alumnos a total_eventos
                    'cuestionarios_count': len(cuestionarios),
                    'evaluaciones_count': len(evaluaciones_taller),
                    'evaluaciones_completadas_cuestionarios': len(evaluaciones_cuestionarios),
                    'evaluaciones_completadas_taller': len(evaluaciones_taller_completadas),
                    'promedio_cuestionarios': round(promedio_cuestionarios, 2),
                    'promedio_evaluaciones': round(promedio_evaluaciones, 2),
                    'tiene_cuestionarios': len(cuestionarios) > 0,
                    'tiene_evaluaciones': len(evaluaciones_taller_completadas) > 0
                }
                cursos_con_info.append(curso_info)

            except Exception as curso_error:
                print(f"ERROR procesando curso {curso.get('nombre')}: {curso_error}")
                import traceback
                print(f"TRACE: {traceback.format_exc()}")
                # Agregar curso básico
                curso_info = {
                    **curso,
                    'total_alumnos': 0,
                    'cuestionarios_count': 0,
                    'evaluaciones_count': 0,
                    'evaluaciones_completadas_cuestionarios': 0,
                    'evaluaciones_completadas_taller': 0,
                    'promedio_cuestionarios': 0,
                    'promedio_evaluaciones': 0,
                    'tiene_cuestionarios': False,
                    'tiene_evaluaciones': False
                }
                cursos_con_info.append(curso_info)

        return render_template('admin/cursos.html', 
                             cursos=cursos_con_info, 
                             instructores=instructores,
                             eventos_dict=eventos_dict)

    except Exception as e:
        print(f"ERROR CRÍTICO en gestion_cursos: {e}")
        import traceback
        print(f"TRAZA COMPLETA: {traceback.format_exc()}")
        flash("Error al cargar los cursos", 'error')
        return render_template('admin/cursos.html', cursos=[], instructores=[], eventos_dict={})

    except Exception as e:
        print(f"ERROR CRÍTICO en gestion_cursos: {e}")
        import traceback
        print(f"TRAZA COMPLETA: {traceback.format_exc()}")
        flash("Error al cargar los cursos", 'error')
        return render_template('admin/cursos.html', cursos=[], instructores=[], eventos_dict={})

# Asignar cuestionario forzado automaticamente
@app.route('/admin/curso/<curso_id>/asignar_cuestionario_auto', methods=['POST'])
@login_required(role='admin')
def asignar_cuestionario_auto(curso_id):
    try:
        print(f"DEBUG: Asignando cuestionario automáticamente para curso: {curso_id}")
        
        # Obtener el curso
        curso = Database.get_curso_by_id(curso_id)
        if not curso:
            return jsonify({'success': False, 'message': 'Curso no encontrado'})
        
        # Buscar cuestionarios del curso
        cuestionarios = list(Database.get_examenes_by_curso_and_tipo(curso_id, 'cuestionario'))
        print(f"DEBUG: Cuestionarios encontrados: {len(cuestionarios)}")
        
        if not cuestionarios:
            return jsonify({'success': False, 'message': 'No hay cuestionarios para este curso'})
        
        # Tomar el primer cuestionario
        primer_cuestionario = cuestionarios[0]
        cuestionario_id = primer_cuestionario['_id']
        
        print(f"DEBUG: Asignando cuestionario ID: {cuestionario_id}")
        
        # Actualizar el curso
        update_result = Database.update_curso(curso_id, {'cuestionario_id': cuestionario_id})
        
        # Verificar
        curso_actualizado = Database.get_curso_by_id(curso_id)
        
        if curso_actualizado.get('cuestionario_id') == cuestionario_id:
            return jsonify({'success': True, 'message': 'Cuestionario asignado correctamente'})
        else:
            return jsonify({'success': False, 'message': 'No se pudo asignar el cuestionario'})
            
    except Exception as e:
        print(f"ERROR en asignar_cuestionario_auto: {e}")
        return jsonify({'success': False, 'message': str(e)})

#Asignar cuestionario al curso automáticamente
def asignar_cuestionario_id_automaticamente(curso_id, curso):
    """Asignar automáticamente cuestionario_id si no existe pero hay cuestionarios"""
    try:
        # Obtener cuestionarios del curso
        cuestionarios = list(Database.get_examenes_by_curso_and_tipo(str(curso_id), 'cuestionario'))
        
        if cuestionarios and not curso.get('cuestionario_id'):
            # Tomar el primer cuestionario encontrado
            primer_cuestionario = cuestionarios[0]
            cuestionario_id = primer_cuestionario['_id']
            
            # Actualizar el curso
            Database.update_curso(str(curso_id), {'cuestionario_id': cuestionario_id})
            print(f"DEBUG: Asignado cuestionario_id automáticamente: {cuestionario_id}")
            
            return cuestionario_id
    except Exception as e:
        print(f"ERROR al asignar cuestionario_id automáticamente: {e}")
    
    return curso.get('cuestionario_id')

# Ruta para ver cuestionarios del curso
@app.route('/admin/curso/<curso_id>/cuestionarios')
@login_required(role='admin')
def cuestionarios_curso(curso_id):
    try:
        curso = Database.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('gestion_cursos'))

        # Obtener cuestionarios del curso
        cuestionarios = list(Database.get_examenes_by_curso_and_tipo(curso_id, 'cuestionario'))
        
        # Obtener evaluaciones completadas para cada cuestionario
        cuestionarios_con_info = []
        for cuestionario in cuestionarios:
            evaluaciones = list(Database.get_evaluaciones_by_examen(str(cuestionario['_id'])))
            
            # Calcular promedio del cuestionario
            promedio = 0
            if evaluaciones:
                calificaciones = [e.get('calificación', 0) for e in evaluaciones if e.get('calificación') is not None]
                if calificaciones:
                    promedio = sum(calificaciones) / len(calificaciones)
            
            cuestionario_info = {
                **cuestionario,
                'evaluaciones_completadas': len(evaluaciones),
                'promedio': round(promedio, 2)
            }
            cuestionarios_con_info.append(cuestionario_info)

        return render_template('admin/cuestionarios_curso.html', 
                             curso=curso, 
                             cuestionarios=cuestionarios_con_info)

    except Exception as e:
        print(f"ERROR en cuestionarios_curso: {e}")
        flash('Error al cargar los cuestionarios del curso', 'error')
        return redirect(url_for('gestion_cursos'))

#Ruta para ver los cuestionarios de los alumnos
@app.route('/user/cuestionario/<cuestionario_id>')
@login_required(role='alumno')
def ver_cuestionario_completado(cuestionario_id):
    try:
        # Obtener el cuestionario
        cuestionario = Database.get_cuestionario_by_id(cuestionario_id)
        if not cuestionario:
            flash('Cuestionario no encontrado', 'error')
            return redirect(url_for('user_dashboard'))

        # Verificar que el cuestionario pertenece al alumno actual
        if cuestionario['alumno_email'] != session['user']:
            flash('No tienes permisos para ver este cuestionario', 'error')
            return redirect(url_for('user_dashboard'))

        # Obtener información del examen y curso
        examen = Database.get_examen_by_id(str(cuestionario['examen_id']))
        curso = Database.get_curso_by_id(str(cuestionario['curso_id']))

        return render_template('user/ver_cuestionario.html',
            cuestionario=cuestionario,
            examen=examen,
            curso=curso)

    except Exception as e:
        print(f"ERROR al cargar cuestionario completado: {e}")
        flash('Error al cargar el cuestionario', 'error')
        return redirect(url_for('user_dashboard'))


# Ruta para ver evaluaciones del curso
@app.route('/admin/curso/<curso_id>/evaluaciones')
@login_required(role='admin')
def evaluaciones_curso(curso_id):
    try:
        print(f"DEBUG: Cargando evaluaciones para curso ID: {curso_id}")
        
        curso = Database.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('gestion_cursos'))

        # Obtener evaluaciones completadas DIRECTAMENTE del curso
        evaluaciones_completadas = list(Database.get_evaluaciones_by_curso(curso_id))
        evaluaciones_completadas = [e for e in evaluaciones_completadas if e.get('tipo_evaluacion') == 'evaluacion_taller']
        
        print(f"DEBUG: Evaluaciones completadas encontradas: {len(evaluaciones_completadas)}")

        # Enriquecer con información del examen (si existe)
        evaluaciones_con_info = []
        for eval_completada in evaluaciones_completadas:
            examen_id = eval_completada.get('examen_id')
            examen_nombre = eval_completada.get('examen_nombre', 'Evaluación (Examen eliminado)')
            
            # Si tenemos examen_id, intentar obtener más información
            if examen_id:
                examen = Database.get_examen_by_id(str(examen_id))
                if examen:
                    examen_nombre = examen.get('nombre', examen_nombre)
            
            # Convertir promedio a escala legible
            promedio_general = eval_completada.get('promedio_general', 0)
            escala_texto = convertir_escala(promedio_general)
            
            eval_info = {
                **eval_completada,
                'examen_nombre': examen_nombre,
                'escala_texto': escala_texto,
                'examen_id': str(examen_id) if examen_id else None
            }
            evaluaciones_con_info.append(eval_info)

        print(f"DEBUG: Total evaluaciones a mostrar: {len(evaluaciones_con_info)}")
        return render_template('admin/evaluaciones_curso.html',
            curso=curso,
            evaluaciones=evaluaciones_con_info)

    except Exception as e:
        print(f"ERROR en evaluaciones_curso: {e}")
        import traceback
        print(f"TRACE: {traceback.format_exc()}")
        flash('Error al cargar las evaluaciones del curso', 'error')
        return redirect(url_for('gestion_cursos'))

    except Exception as e:
        print(f"ERROR en evaluaciones_curso: {e}")
        import traceback
        print(f"TRACE: {traceback.format_exc()}")
        flash('Error al cargar las evaluaciones del curso', 'error')
        return redirect(url_for('gestion_cursos'))

# Ruta para cargar cuestionario CSV a un curso específico
@app.route('/admin/curso/<curso_id>/cargar_cuestionario', methods=['POST'])
@login_required(role='admin')
def cargar_cuestionario_curso(curso_id):
    try:
        if 'archivo_csv' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('gestion_cursos'))

        archivo = request.files['archivo_csv']
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('gestion_cursos'))

        if not archivo.filename.endswith('.csv'):
            flash('El archivo debe ser un CSV', 'error')
            return redirect(url_for('gestion_cursos'))

        # Obtener información del curso
        curso = Database.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('gestion_cursos'))

        # Leer y procesar el archivo CSV
        contenido = archivo.stream.read().decode('utf-8')
        lineas = contenido.split('\n')
        
        preguntas_data = []

        for linea in lineas[1:]:  # Saltar encabezado
            if linea.strip():
                partes = linea.strip().split(',')
                if len(partes) >= 5:
                    numero_pregunta = partes[0].strip()
                    pregunta_texto = partes[1].strip()
                    tipo_respuesta = partes[2].strip().lower()
                    
                    if tipo_respuesta == 'opcion_multiple':
                        opciones_str = partes[3].strip()
                        respuesta_correcta = partes[4].strip()
                        
                        # Dividir opciones
                        opciones = [opcion.strip() for opcion in opciones_str.split('|')]
                        
                        if pregunta_texto and opciones and respuesta_correcta:
                            preguntas_data.append({
                                'numero': numero_pregunta,
                                'tipo': 'opcion_multiple',
                                'pregunta': pregunta_texto,
                                'opciones': opciones,
                                'respuesta_correcta': respuesta_correcta
                            })

        # Crear examen de cuestionario
        examen_data = {
            'curso_id': ObjectId(curso_id),
            'nombre': f"Cuestionario - {curso['nombre']}",
            'tipo_examen': 'cuestionario',
            'preguntas': preguntas_data,
            'fecha_creacion': datetime.now()
        }

        Database.insert_examen(examen_data)
        flash(f'Cuestionario cargado exitosamente con {len(preguntas_data)} preguntas', 'success')

    except Exception as e:
        flash(f'Error al cargar cuestionario: {str(e)}', 'error')

    return redirect(url_for('gestion_cursos'))

# Ruta para crear evento de curso
@app.route('/admin/curso/<curso_id>/evento/crear', methods=['POST'])
@login_required(role='admin')
def crear_evento_curso(curso_id):
    try:
        fecha_evento = request.form.get('fecha_evento')
        # ELIMINADO: instructor_email del formulario de evento
        
        if not fecha_evento:
            flash('La fecha del evento es requerida', 'error')
            return redirect(url_for('gestion_cursos'))

        # Obtener información del curso
        curso = Database.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('gestion_cursos'))

        evento_data = {
            'curso_id': ObjectId(curso_id),
            'curso_nombre': curso['nombre'],
            'fecha_evento': datetime.strptime(fecha_evento, '%Y-%m-%d'),
            'instructor_id': None,  # Se asignará posteriormente
            'instructor_email': None,
            'instructor_nombre': None,
            'alumnos_asignados': [],
            'estatus': 'abierto',  # NUEVO: estatus por defecto
            'fecha_creacion': datetime.now()
        }

        Database.insert_evento(evento_data)
        flash('Evento creado exitosamente con estatus: ABIERTO', 'success')

    except Exception as e:
        flash(f'Error al crear evento: {str(e)}', 'error')

    return redirect(url_for('gestion_cursos'))


# Función auxiliar para convertir escala numérica a texto
def convertir_escala(puntaje):
    if puntaje >= 5.5:
        return "Excelente"
    elif puntaje >= 4.5:
        return "Muy Bien"
    elif puntaje >= 3.5:
        return "Bien"
    elif puntaje >= 2.5:
        return "Regular"
    elif puntaje >= 1.5:
        return "Mal"
    else:
        return "Muy mal"


# AGREGAR CURSOS
@app.route('/admin/curso/agregar', methods=['POST'])
@login_required(role='admin')
def agregar_curso():
    try:
        curso_data = {
            'nombre': request.form.get('nombre'),
            'description': request.form.get('description'),
            'horas_totales': int(request.form.get('horas_totales')),
            'dias_duracion': int(request.form.get('dias_duracion')),
            'estatus': 'activo',
            'fecha_creacion': datetime.now(),
            'evaluacion_id': None,
            'cuestionario_id': None
            # ELIMINADO: instructor_id, instructor_nombre, asignado
        }

        # Insertar curso
        result = Database.insert_curso(curso_data)
        curso_id = result.inserted_id

        # Crear evaluación del taller por defecto con la estructura específica
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

        # Crear preguntas en formato estándar para la evaluación
        preguntas_estandar = []

        # Agregar preguntas del taller
        for pregunta in estructura_evaluacion['secciones']['taller']:
            preguntas_estandar.append({
                'tipo': 'escala',
                'seccion': 'taller',
                'numero': pregunta['numero'],
                'pregunta': pregunta['texto'],
                'opciones': ['1', '2', '3', '4', '5', '6']
            })

        # Agregar preguntas del instructor
        for pregunta in estructura_evaluacion['secciones']['instructor']:
            preguntas_estandar.append({
                'tipo': 'escala',
                'seccion': 'instructor',
                'numero': pregunta['numero'],
                'pregunta': pregunta['texto'],
                'opciones': ['1', '2', '3', '4', '5', '6']
            })

        # Agregar pregunta de comentarios
        preguntas_estandar.append({
            'tipo': 'texto_largo',
            'seccion': 'comentarios',
            'numero': '',
            'pregunta': estructura_evaluacion['secciones']['comentarios']
        })

        # Crear el examen de evaluación del taller
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

        evaluacion_result = Database.insert_examen(evaluacion_data)
        
        # Actualizar el curso con el ID de la evaluación
        Database.update_curso(str(curso_id), {
            'evaluacion_id': evaluacion_result.inserted_id
        })

        flash('Curso agregado exitosamente. Se ha creado la evaluación del taller por defecto.', 'success')
        
    except Exception as e:
        flash(f'Error al agregar curso: {str(e)}', 'error')

    return redirect(url_for('gestion_cursos'))

@app.route('/admin/curso/eliminar/<curso_id>')
@login_required(role='admin')
def eliminar_curso(curso_id):
    try:
        Database.delete_curso(curso_id)
        flash('Curso eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar curso: {str(e)}', 'error')
    return redirect(url_for('gestion_cursos'))

@app.route('/admin/evaluacion/<evaluacion_id>')
@login_required(role='admin')
def detalle_evaluacion_admin(evaluacion_id):
    try:
        print(f"🔵 DEBUG: Buscando evaluación con ID: {evaluacion_id}")
        
        evaluacion = Database.get_evaluacion_by_id(evaluacion_id)
        if not evaluacion:
            print(f"🔴 ERROR: Evaluación no encontrada para ID: {evaluacion_id}")
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('gestion_cursos'))
        
        # Obtener información del examen
        examen_id = str(evaluacion.get('examen_id', ''))
        examen = Database.get_examen_by_id(examen_id) if examen_id else None
        
        # Obtener información del curso
        curso_id = str(evaluacion.get('curso_id', ''))
        curso = Database.get_curso_by_id(curso_id) if curso_id else None
        
        print(f"🔵 DEBUG: Evaluación encontrada - Alumno: {evaluacion.get('alumno_nombre')}")
        
        return render_template('admin/detalle_evaluacion.html',
                            evaluacion=evaluacion,
                            examen=examen,
                            curso=curso)
        
    except Exception as e:
        print(f"🔴 ERROR en detalle_evaluacion_admin: {e}")
        import traceback
        print(f"🔴 TRAZA COMPLETA: {traceback.format_exc()}")
        flash('Error al cargar los detalles de la evaluación', 'error')
        return redirect(url_for('gestion_cursos'))


# Gestión de Exámenes - Rutas completas
@app.route('/admin/examenes')
@login_required(role='admin')
def gestion_examenes():
    try:
        cursos = list(Database.get_cursos_activos_con_instructor())
        examenes = list(db.Exámenes.find())
        
        examenes_procesados = []
        
        for examen in examenes:
            curso = Database.get_curso_by_id(str(examen['curso_id']))
            
            # Asegurarse de que el ID se convierte a string
            examen_id_str = str(examen['_id'])
            
            examen_procesado = {
                'id': examen_id_str,  # Esto es lo importante
                'nombre': examen.get('nombre', 'Sin nombre'),
                'tipo_examen': examen.get('tipo_examen', 'regular'),
                'curso_nombre': curso['nombre'] if curso else 'Curso no encontrado',
                'instructor_nombre': curso.get('instructor_nombre', 'N/A') if curso else 'N/A',
                'fecha_creacion': examen.get('fecha_creacion'),
                'descripcion': examen.get('descripcion', ''),
                'preguntas_count': len(examen.get('preguntas', []))
            }
            examenes_procesados.append(examen_procesado)
            
            # Debug
            print(f"DEBUG - Examen: {examen_procesado['nombre']}, ID: {examen_procesado['id']}")

        return render_template('admin/examenes.html', 
                             examenes=examenes_procesados, 
                             cursos=cursos)
        
    except Exception as e:
        print(f"ERROR al cargar exámenes: {e}")
        flash(f'Error al cargar los exámenes: {str(e)}', 'error')
        return render_template('admin/examenes.html', examenes=[], cursos=[])


@app.route('/admin/examen/cargar_csv', methods=['POST'])
@login_required(role='admin')
def cargar_examen_csv():
    try:
        if 'archivo_csv' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('gestion_examenes'))
        
        archivo = request.files['archivo_csv']
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('gestion_examenes'))
        
        if not archivo.filename.endswith('.csv'):
            flash('El archivo debe ser un CSV', 'error')
            return redirect(url_for('gestion_examenes'))
        
        tipo_examen = request.form.get('tipo_examen_csv')
        curso_id = request.form.get('curso_id_csv')
        nombre_examen = request.form.get('nombre_examen_csv')
        
        # Validar que no exista un examen del mismo tipo para este curso
        examen_existente = Database.get_examen_by_curso_and_tipo(curso_id, tipo_examen)
        if examen_existente:
            flash(f'Ya existe un examen de tipo {tipo_examen} para este curso', 'error')
            return redirect(url_for('gestion_examenes'))
        
        # Leer y procesar el archivo CSV
        contenido = archivo.stream.read().decode('utf-8')
        lineas = contenido.split('\n')
        
        preguntas_data = []
        
        if tipo_examen == 'cuestionario':
            # CSV para cuestionario: pregunta,opciones,respuesta
            for linea in lineas[1:]:  # Saltar encabezado
                if linea.strip():
                    partes = linea.strip().split(',')
                    if len(partes) >= 3:
                        pregunta = partes[0].strip()
                        opciones_str = partes[1].strip()
                        respuesta_correcta = partes[2].strip()
                        
                        # Dividir opciones (separadas por |)
                        opciones = [opcion.strip() for opcion in opciones_str.split('|')]
                        
                        if pregunta and opciones and respuesta_correcta:
                            preguntas_data.append({
                                'tipo': 'opcion_multiple',
                                'pregunta': pregunta,
                                'opciones': opciones,
                                'respuesta_correcta': respuesta_correcta
                            })
        
        elif tipo_examen == 'encuesta':
            # CSV para encuesta: pregunta
            for linea in lineas[1:]:  # Saltar encabezado
                if linea.strip():
                    pregunta = linea.strip()
                    if pregunta and not pregunta.lower().startswith('pregunta'):
                        preguntas_data.append({
                            'tipo': 'respuesta_abierta',
                            'pregunta': pregunta
                        })
        
        examen_data = {
            'curso_id': ObjectId(curso_id),
            'nombre': nombre_examen,
            'tipo_examen': tipo_examen,
            'preguntas': preguntas_data,
            'fecha_creacion': datetime.now()
        }
        
        Database.insert_examen(examen_data)
        flash(f'Examen cargado exitosamente desde CSV con {len(preguntas_data)} preguntas', 'success')
        
    except Exception as e:
        flash(f'Error al cargar examen desde CSV: {str(e)}', 'error')
    
    return redirect(url_for('gestion_examenes'))

@app.route('/admin/examen/eliminar/<examen_id>')
@login_required(role='admin')
def eliminar_examen(examen_id):
    try:
        Database.delete_examen(examen_id)
        flash('Examen eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar examen: {str(e)}', 'error')
    
    return redirect(url_for('gestion_examenes'))

@app.route('/admin/examen/detalle/<examen_id>')
@login_required(role='admin')
def detalle_examen(examen_id):
    try:
        print(f"DEBUG: Buscando examen con ID: {examen_id}")

        if not examen_id or examen_id.strip() == "":
            flash('ID de examen no proporcionado', 'error')
            return redirect(url_for('gestion_examenes'))
        
        examen = Database.get_examen_by_id(examen_id)
        
        if not examen:
            flash('Examen no encontrado en la base de datos', 'error')
            return redirect(url_for('gestion_examenes'))
        
        # Obtener información del curso
        curso_id_str = str(examen['curso_id'])
        curso = Database.get_curso_by_id(curso_id_str)
        
        return render_template('admin/detalle_examen.html', 
                             examen=examen, 
                             curso=curso)

    except Exception as e:
        print(f"ERROR en detalle_examen: {e}")
        flash(f'Error al cargar detalle del examen: {str(e)}', 'error')
        return redirect(url_for('gestion_examenes'))

# Evaluación Específica para Taller
@app.route('/admin/evaluacion_taller/crear', methods=['POST'])
@login_required(role='admin')
def crear_evaluacion_taller():
    try:
        curso_id = request.form.get('curso_id')
        nombre_evaluacion = request.form.get('nombre_evaluacion')
        
        # Verificar que el curso existe y tiene instructor
        curso = Database.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('gestion_examenes'))
        
        # Crear la estructura EXACTA de la evaluación del taller
        estructura = {
            'escala': '(1) Muy mal     (2) Mal    (3) Regular     (4) Bien     (5) Muy Bien     (6) Excelente',
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
                ]
            },
            'comentarios': 'Por favor proporciónanos un comentario de este taller'
        }

        # También crear preguntas en el formato estándar para que el conteo funcione
        preguntas_estandar = []
        
        # Agregar preguntas del taller
        for pregunta in estructura['secciones']['taller']:
            preguntas_estandar.append({
                'tipo': 'escala',
                'seccion': 'taller',
                'numero': pregunta['numero'],
                'pregunta': pregunta['texto'],
                'opciones': ['1', '2', '3', '4', '5', '6']
            })
        
        # Agregar preguntas del instructor
        for pregunta in estructura['secciones']['instructor']:
            preguntas_estandar.append({
                'tipo': 'escala', 
                'seccion': 'instructor',
                'numero': pregunta['numero'],
                'pregunta': pregunta['texto'],
                'opciones': ['1', '2', '3', '4', '5', '6']
            })
        
        # Agregar pregunta de comentarios
        preguntas_estandar.append({
            'tipo': 'texto_largo',
            'seccion': 'comentarios',
            'numero': '',
            'pregunta': estructura['comentarios']
        })
        
        examen_data = {
            'curso_id': ObjectId(curso_id),
            'nombre': nombre_evaluacion or f"Evaluación del Taller - {curso['nombre']}",
            'descripcion': 'Evaluación de taller con escala del 1-6',
            'tipo_examen': 'evaluacion_taller',
            'formato_especifico': True,
            'estructura': estructura,
            'preguntas': preguntas_estandar,  # Esto hará que el conteo sea correcto
            'fecha_creacion': datetime.now()
        }
        
        Database.insert_examen(examen_data)
        flash(f'Evaluación de taller creada exitosamente con {len(preguntas_estandar)} preguntas', 'success')
        
    except Exception as e:
        print(f"ERROR: {e}")
        flash(f'Error al crear evaluación de taller: {str(e)}', 'error')
    
    return redirect(url_for('gestion_examenes'))

# Ruta para agregar examen manual (asegúrate de que existe)
@app.route('/admin/examen/agregar_manual', methods=['POST'])
@login_required(role='admin')
def agregar_examen_manual():
    try:
        tipo_examen = request.form.get('tipo_examen')
        curso_id = request.form.get('curso_id')
        nombre_examen = request.form.get('nombre_examen')
        descripcion = request.form.get('descripcion', '')
        
        # Validar que no exista un examen del mismo tipo para este curso
        examen_existente = Database.get_examen_by_curso_and_tipo(curso_id, tipo_examen)
        if examen_existente:
            flash(f'Ya existe un examen de tipo {tipo_examen} para este curso', 'error')
            return redirect(url_for('gestion_examenes'))
        
        preguntas_data = []
        
        if tipo_examen == 'cuestionario':
            num_preguntas = int(request.form.get('num_preguntas_cuestionario', 0))
            for i in range(num_preguntas):
                pregunta_texto = request.form.get(f'pregunta_c_{i}')
                opciones = [
                    request.form.get(f'opcion_c_{i}_0'),
                    request.form.get(f'opcion_c_{i}_1'),
                    request.form.get(f'opcion_c_{i}_2'),
                    request.form.get(f'opcion_c_{i}_3')
                ]
                respuesta_correcta = request.form.get(f'respuesta_correcta_{i}')
                
                if pregunta_texto and all(opciones) and respuesta_correcta:
                    preguntas_data.append({
                        'tipo': 'opcion_multiple',
                        'pregunta': pregunta_texto,
                        'opciones': opciones,
                        'respuesta_correcta': respuesta_correcta
                    })
        
        elif tipo_examen == 'encuesta':
            num_preguntas = int(request.form.get('num_preguntas_encuesta', 0))
            for i in range(num_preguntas):
                pregunta_texto = request.form.get(f'pregunta_e_{i}')
                if pregunta_texto:
                    preguntas_data.append({
                        'tipo': 'respuesta_abierta',
                        'pregunta': pregunta_texto
                    })
        
        examen_data = {
            'curso_id': ObjectId(curso_id),
            'nombre': nombre_examen,
            'descripcion': descripcion,
            'tipo_examen': tipo_examen,
            'preguntas': preguntas_data,
            'fecha_creacion': datetime.now()
        }
        
        Database.insert_examen(examen_data)
        flash('Examen creado exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al crear examen: {str(e)}', 'error')
    
    return redirect(url_for('gestion_examenes'))

# Rutas de Usuario (Alumno/Instructor)
@app.route('/user/dashboard')
@login_required()
def user_dashboard():
    if session.get('role') == 'alumno':
        # Obtener CUESTIONARIOS (exámenes de aprendizaje) del alumno
        cuestionarios = []
        # Obtener EVALUACIONES (opiniones del curso) del alumno
        evaluaciones_curso = []
        
        try:
            cuestionarios = list(Database.get_cuestionarios_by_alumno(session['user']))
            evaluaciones_curso = list(Database.get_evaluaciones_by_alumno(session['user']))
            
            # DEBUG: Verificar los datos obtenidos
            print(f"DEBUG - Cuestionarios encontrados: {len(cuestionarios)}")
            for c in cuestionarios:
                print(f"DEBUG - Cuestionario: {c.get('examen_nombre')}, Calificación: {c.get('calificacion')}")
                
            print(f"DEBUG - Evaluaciones encontradas: {len(evaluaciones_curso)}")
            
        except Exception as e:
            print(f"Error al obtener actividades: {e}")

        # Combinar ambas listas para mostrar en el dashboard
        actividades = cuestionarios + evaluaciones_curso
        # Ordenar por fecha más reciente
        actividades.sort(key=lambda x: x.get('fecha_realizacion', datetime.min), reverse=True)

        return render_template('user/dashboard.html', actividades=actividades)
    else:
        # Para instructores - mostrar eventos asignados
        try:
            eventos_asignados = list(Database.get_eventos_by_instructor(session['user']))
            return render_template('user/dashboard_instructor.html', 
                                 eventos=eventos_asignados,
                                 instructor_nombre=session.get('nombre'))
        except Exception as e:
            print(f"ERROR en dashboard instructor: {e}")
            return render_template('user/dashboard_instructor.html', 
                                 eventos=[],
                                 instructor_nombre=session.get('nombre'))

### Ruta para cargar cuestionario CSV 
@app.route('/admin/curso/<curso_id>/cargar_cuestionario', methods=['POST'])
@login_required(role='admin')
def cargar_cuestionario_curso_csv(curso_id):
    try:
        print(f"DEBUG: === INICIANDO CARGA DE CUESTIONARIO ===")
        print(f"DEBUG: Curso ID recibido: {curso_id}")
        
        if 'archivo_csv' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('gestion_cursos'))

        archivo = request.files['archivo_csv']
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('gestion_cursos'))

        if not archivo.filename.endswith('.csv'):
            flash('El archivo debe ser un CSV', 'error')
            return redirect(url_for('gestion_cursos'))

        # Obtener información del curso
        curso = Database.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('gestion_cursos'))
            
        print(f"DEBUG: Curso encontrado: {curso.get('nombre')}")
        print(f"DEBUG: Cuestionario ID actual: {curso.get('cuestionario_id')}")

        # Leer y procesar el archivo CSV
        contenido = archivo.stream.read().decode('utf-8')
        lineas = contenido.split('\n')
        
        preguntas_data = []
        preguntas_procesadas = 0

        for i, linea in enumerate(lineas[1:]):  # Saltar encabezado
            if linea.strip():
                partes = linea.strip().split(',')
                if len(partes) >= 5:
                    numero_pregunta = partes[0].strip()
                    pregunta_texto = partes[1].strip()
                    tipo_respuesta = partes[2].strip().lower()
                    
                    if tipo_respuesta == 'opcion_multiple':
                        opciones_str = partes[3].strip()
                        respuesta_correcta = partes[4].strip()
                        
                        # Dividir opciones
                        opciones = [opcion.strip() for opcion in opciones_str.split('|')]
                        
                        if pregunta_texto and opciones and respuesta_correcta:
                            preguntas_data.append({
                                'numero': numero_pregunta,
                                'tipo': 'opcion_multiple',
                                'pregunta': pregunta_texto,
                                'opciones': opciones,
                                'respuesta_correcta': respuesta_correcta
                            })
                            preguntas_procesadas += 1
                            print(f"DEBUG: Pregunta {preguntas_procesadas} procesada: {pregunta_texto[:50]}...")

        print(f"DEBUG: Total preguntas procesadas: {preguntas_procesadas}")

        # Crear examen de cuestionario
        examen_data = {
            'curso_id': ObjectId(curso_id),
            'nombre': f"Cuestionario - {curso['nombre']}",
            'tipo_examen': 'cuestionario',
            'preguntas': preguntas_data,
            'fecha_creacion': datetime.now()
        }

        print(f"DEBUG: Insertando cuestionario en la base de datos...")
        cuestionario_result = Database.insert_examen(examen_data)
        cuestionario_id = cuestionario_result.inserted_id
        
        print(f"DEBUG: Cuestionario insertado con ID: {cuestionario_id}")
        print(f"DEBUG: Tipo del ID: {type(cuestionario_id)}")

        # Actualizar el curso con el ID del cuestionario
        print(f"DEBUG: Actualizando curso con cuestionario_id...")
        update_data = {'cuestionario_id': cuestionario_id}
        print(f"DEBUG: Datos de actualización: {update_data}")
        
        update_result = Database.update_curso(curso_id, update_data)
        print(f"DEBUG: Resultado de actualización - Modified: {update_result.modified_count}")

        # Verificar la actualización
        curso_actualizado = Database.get_curso_by_id(curso_id)
        print(f"DEBUG: Curso después de actualizar:")
        print(f"DEBUG - Cuestionario ID: {curso_actualizado.get('cuestionario_id')}")
        print(f"DEBUG - Tiene cuestionario_id: {curso_actualizado.get('cuestionario_id') is not None}")

        flash(f'Cuestionario cargado exitosamente con {preguntas_procesadas} preguntas', 'success')

    except Exception as e:
        print(f"ERROR CRÍTICO en cargar_cuestionario_curso_csv: {e}")
        import traceback
        print(f"TRACE COMPLETA: {traceback.format_exc()}")
        flash(f'Error al cargar cuestionario: {str(e)}', 'error')

    return redirect(url_for('gestion_cursos'))


# Ruta para que los alumnos tomen la evaluación del taller
@app.route('/user/evaluacion_taller/<examen_id>')
@login_required(role='alumno')
def tomar_evaluacion_taller(examen_id):
    try:
        examen = Database.get_examen_by_id(examen_id)
        if not examen:
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('user_examenes'))
        
        # Verificar que es una evaluación de taller
        if examen.get('tipo_examen') != 'evaluacion_taller':
            flash('Esta no es una evaluación de taller', 'error')
            return redirect(url_for('user_examenes'))
        
        curso = Database.get_curso_by_id(str(examen['curso_id']))
        
        # Obtener información del alumno
        alumno = Database.get_alumno_by_email(session['user'])
        
        # Preparar datos predefinidos
        nombre_curso = curso['nombre'] if curso else 'Curso no encontrado'
        nombre_instructor = curso.get('instructor_nombre', 'Instructor no asignado')
        
        return render_template('user/tomar_evaluacion_taller.html', 
                             examen=examen, 
                             curso=curso,
                             nombre_curso=nombre_curso,
                             nombre_instructor=nombre_instructor,
                             estructura=examen.get('estructura', {}))

    except Exception as e:
        print(f"ERROR al cargar evaluación de taller: {e}")
        flash(f'Error al cargar la evaluación: {str(e)}', 'error')
        return redirect(url_for('user_examenes'))

# Ruta para ENVIAR el formulario (POST)
@app.route('/user/evaluacion_taller/<examen_id>/enviar', methods=['POST'])
@login_required(role='alumno')
def enviar_evaluacion_taller(examen_id):
    print("DEBUG: === INICIANDO ENVÍO DE EVALUACIÓN ===")
    print(f"DEBUG: Examen ID: {examen_id}")
    print(f"DEBUG: Usuario: {session['user']}")

    try:
        # 1. VERIFICAR EXAMEN
        print("DEBUG: 1. Buscando examen...")
        examen = Database.get_examen_by_id(examen_id)
        if not examen:
            print("ERROR: Examen no encontrado")
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('user_examenes'))
        print(f"DEBUG: Examen encontrado: {examen.get('nombre')}")

        # 2. VERIFICAR FORMULARIO
        print("DEBUG: 2. Procesando formulario...")
        respuestas = request.form
        print(f"DEBUG: Campos recibidos: {list(respuestas.keys())}")

        # 3. VERIFICAR CURSO
        print("DEBUG: 3. Verificando curso...")
        curso = Database.get_curso_by_id(str(examen['curso_id']))
        if not curso:
            print("ERROR: Curso no encontrado")
            flash('Error: Curso no encontrado', 'error')
            return redirect(url_for('user_examenes'))
        print(f"DEBUG: Curso: {curso.get('nombre')}")

        # 4. PROCESAR RESPUESTAS
        print("DEBUG: 4. Procesando respuestas...")
        resultados = {
            'informacion_general': {
                'nombre_taller': respuestas.get('nombre_taller', ''),
                'nombre_instructor': respuestas.get('nombre_instructor', '')
            },
            'respuestas_taller': {},
            'respuestas_instructor': {},
            'comentarios': respuestas.get('comentarios', '')
        }

        # Procesar preguntas del TALLER
        puntajes_taller = []
        if examen.get('estructura') and examen['estructura'].get('secciones'):
            for pregunta in examen['estructura']['secciones']['taller']:
                campo = f"pregunta_{pregunta['numero']}"
                puntaje_str = respuestas.get(campo, '0')
                try:
                    puntaje = int(puntaje_str)
                    resultados['respuestas_taller'][pregunta['numero']] = {
                        'pregunta': pregunta['texto'],
                        'puntaje': puntaje
                    }
                    puntajes_taller.append(puntaje)
                    print(f"DEBUG: Taller - {campo}: {puntaje}")
                except ValueError:
                    print(f"ERROR: No se pudo convertir puntaje para {campo}")
                    puntaje = 0

        # Procesar preguntas del INSTRUCTOR
        puntajes_instructor = []
        if examen.get('estructura') and examen['estructura'].get('secciones'):
            for pregunta in examen['estructura']['secciones']['instructor']:
                campo = f"pregunta_{pregunta['numero']}"
                puntaje_str = respuestas.get(campo, '0')
                try:
                    puntaje = int(puntaje_str)
                    resultados['respuestas_instructor'][pregunta['numero']] = {
                        'pregunta': pregunta['texto'],
                        'puntaje': puntaje
                    }
                    puntajes_instructor.append(puntaje)
                    print(f"DEBUG: Instructor - {campo}: {puntaje}")
                except ValueError:
                    print(f"ERROR: No se pudo convertir puntaje para {campo}")
                    puntaje = 0

        print(f"DEBUG: Puntajes taller: {puntajes_taller}")
        print(f"DEBUG: Puntajes instructor: {puntajes_instructor}")

        # 5. CALCULAR PROMEDIOS
        print("DEBUG: 5. Calculando promedios...")
        promedio_taller = sum(puntajes_taller) / len(puntajes_taller) if puntajes_taller else 0
        promedio_instructor = sum(puntajes_instructor) / len(puntajes_instructor) if puntajes_instructor else 0
        promedio_general = (promedio_taller + promedio_instructor) / 2 if puntajes_taller and puntajes_instructor else 0
        
        print(f"DEBUG: Promedios - T:{promedio_taller}, I:{promedio_instructor}, G:{promedio_general}")

        # 6. PREPARAR Y GUARDAR EVALUACIÓN
        print("DEBUG: 6. Preparando datos para guardar...")
        evaluacion_data = {
            'alumno_email': session['user'],
            'alumno_nombre': session.get('nombre'),
            'examen_id': ObjectId(examen_id),
            'examen_nombre': examen['nombre'],
            'curso_id': examen['curso_id'],
            'curso_nombre': curso['nombre'],
            'instructor_email': curso.get('instructor_email', 'N/A'),
            'instructor_nombre': curso.get('instructor_nombre', 'N/A'),
            'tipo_evaluacion': 'evaluacion_taller',
            'resultados': resultados,
            'promedio_taller': round(promedio_taller, 2),
            'promedio_instructor': round(promedio_instructor, 2),
            'promedio_general': round(promedio_general, 2),
            'fecha_realizacion': datetime.now()
        }

        print("DEBUG: Intentando guardar evaluación...")
        result = Database.insert_evaluacion(evaluacion_data)
        print(f"EXITO: Evaluación guardada con ID: {result.inserted_id}")

        flash(f'Evaluación enviada exitosamente! Promedio general: {promedio_general:.2f}/6', 'success')
        return redirect(url_for('user_dashboard'))

    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        import traceback
        print(f"TRAZA COMPLETA: {traceback.format_exc()}")
        flash(f'Error al enviar evaluación: {str(e)}', 'error')
        return redirect(url_for('user_examenes'))

@app.route('/user/examen/<examen_id>')
@login_required(role='alumno')
def tomar_examen(examen_id):
    try:
        examen = Database.get_examen_by_id(examen_id)
        if not examen:
            flash('Examen no encontrado', 'error')
            return redirect(url_for('user_examenes'))
        
        return render_template('user/tomar_examen.html', examen=examen)
    except Exception as e:
        flash(f'Error al cargar el examen: {str(e)}', 'error')
        return redirect(url_for('user_examenes'))

@app.route('/user/examen/<examen_id>/evaluar', methods=['POST'])
@login_required(role='alumno')
def evaluar_examen(examen_id):
    try:
        examen = Database.get_examen_by_id(examen_id)
        if not examen:
            flash('Examen no encontrado', 'error')
            return redirect(url_for('user_examenes'))
        
        respuestas = request.form
        respuestas_correctas = 0
        total_preguntas = len(examen['preguntas'])
        resultados = []
        
        print(f"DEBUG - Total preguntas: {total_preguntas}")
        print(f"DEBUG - Campos del formulario: {list(respuestas.keys())}")
        
        for i, pregunta in enumerate(examen['preguntas']):
            respuesta_usuario = respuestas.get(f'pregunta_{i}')
            print(f"DEBUG - Pregunta {i}: Usuario respondió: {respuesta_usuario}, Correcta: {pregunta['respuesta_correcta']}")
            
            # Comparar respuestas (asegurarnos de que no hay espacios extra)
            es_correcta = (respuesta_usuario and 
                          respuesta_usuario.strip() == pregunta['respuesta_correcta'].strip())
            
            if es_correcta:
                respuestas_correctas += 1
                print(f"DEBUG - ¡Respuesta correcta! Total correctas: {respuestas_correctas}")
            
            resultados.append({
                'pregunta': pregunta['pregunta'],
                'respuesta_usuario': respuesta_usuario,
                'respuesta_correcta': pregunta['respuesta_correcta'],
                'es_correcta': es_correcta
            })
        
        # CALCULAR CALIFICACIÓN
        if total_preguntas > 0:
            calificacion = (respuestas_correctas / total_preguntas) * 100
        else:
            calificacion = 0
            
        print(f"DEBUG - Respuestas correctas: {respuestas_correctas}/{total_preguntas}")
        print(f"DEBUG - Calificación calculada: {calificacion}")

        # Obtener información del alumno y curso
        alumno = Database.get_alumno_by_email(session['user'])
        curso = Database.get_curso_by_id(str(examen['curso_id']))

        # Crear documento para la colección CUESTIONARIOS - ¡CORREGIDO!
        cuestionario_data = {
            'alumno_email': session['user'], 
            'alumno_nombre': session.get('nombre'), 
            'examen_id': ObjectId(examen_id), 
            'examen_nombre': examen['nombre'], 
            'curso_id': ObjectId(str(examen['curso_id'])),  # Asegurar que es ObjectId
            'curso_nombre': curso['nombre'] if curso else 'N/A', 
            'instructor_email': curso.get('instructor_email', 'N/A') if curso else 'N/A', 
            'calificacion': float(calificacion),  # ¡CORREGIDO! Asegurar que es float
            'resultados': resultados, 
            'fecha_realizacion': datetime.now(), 
            'respuestas_correctas': respuestas_correctas, 
            'total_preguntas': total_preguntas,
            'tipo_evaluacion': 'cuestionario'
        }

        print(f"DEBUG - Datos a guardar - Calificacion: {cuestionario_data['calificacion']} (tipo: {type(cuestionario_data['calificacion'])})")

        # Guardar en la colección CUESTIONARIOS
        result = Database.insert_cuestionario(cuestionario_data)
        print(f"DEBUG - Cuestionario guardado con ID: {result.inserted_id}")

        flash(f'Examen completado. Calificación: {calificacion:.2f}%', 'success')
        return redirect(url_for('user_dashboard'))

    except Exception as e:
        print(f"ERROR CRÍTICO en evaluar_examen: {e}")
        import traceback
        print(f"TRACE: {traceback.format_exc()}")
        flash(f'Error al evaluar examen: {str(e)}', 'error')
        return redirect(url_for('user_examenes'))

    except Exception as e:
        print(f"ERROR CRÍTICO en evaluar_examen: {e}")
        import traceback
        print(f"TRACE: {traceback.format_exc()}")
        flash(f'Error al evaluar examen: {str(e)}', 'error')
        return redirect(url_for('user_examenes'))

@app.route('/user/examenes')
@login_required()
def user_examenes():
    if session.get('role') == 'alumno':
        try:
            alumno = Database.get_alumno_by_email(session['user'])
            if alumno and alumno.get('curso'):
                # Buscar el curso por nombre
                cursos = list(Database.get_cursos_activos())
                curso_alumno = None
                for curso in cursos:
                    if curso['nombre'] == alumno['curso']:
                        curso_alumno = curso
                        break

                if curso_alumno:
                    examenes = list(Database.get_examenes_by_curso(str(curso_alumno['_id'])))
                    return render_template('user/examenes.html', examenes=examenes)

            flash('No tienes cursos asignados o no hay exámenes disponibles', 'warning')
            return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            print(f"ERROR en user_examenes: {e}")
            flash('Error al cargar los exámenes', 'error')
            return redirect(url_for('user_dashboard'))
    else:
        # Para instructores, mostrar una página diferente o redirigir
        flash('Esta función solo está disponible para alumnos', 'warning')
        return redirect(url_for('user_dashboard'))

# Ver la evaluación por alumno
@app.route('/user/evaluacion/<evaluacion_id>')
@login_required(role='alumno')
def ver_evaluacion_completada(evaluacion_id):
    try:
        # Obtener la evaluación
        evaluacion = Database.get_evaluacion_by_id(evaluacion_id)
        
        if not evaluacion:
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Verificar que la evaluación pertenece al alumno actual
        if evaluacion['alumno_email'] != session['user']:
            flash('No tienes permisos para ver esta evaluación', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Obtener información del examen y curso
        examen = Database.get_examen_by_id(str(evaluacion['examen_id']))
        curso = Database.get_curso_by_id(str(evaluacion['curso_id']))
        
        return render_template('user/ver_evaluacion.html', 
                             evaluacion=evaluacion,
                             examen=examen,
                             curso=curso)
        
    except Exception as e:
        print(f"ERROR al cargar evaluación completada: {e}")
        flash('Error al cargar la evaluación', 'error')
        return redirect(url_for('user_dashboard'))

# Ruta para ver alumnos del curso con sus calificaciones
@app.route('/admin/curso/<curso_id>/alumnos')
@login_required(role='admin')
def alumnos_curso(curso_id):
    try:
        curso = Database.get_curso_by_id(curso_id)
        if not curso:
            flash('Curso no encontrado', 'error')
            return redirect(url_for('gestion_cursos'))

        # Obtener alumnos del curso
        alumnos = list(Database.get_alumnos_by_curso(curso['nombre']))
        
        # Enriquecer información de cada alumno con sus calificaciones
        alumnos_con_calificaciones = []
        for alumno in alumnos:
            # Obtener evaluaciones del alumno para este curso
            evaluaciones_alumno = list(Database.get_evaluaciones_by_alumno_and_curso(alumno['email'], curso_id))
            
            # Separar por tipo
            evaluaciones_cuestionarios = [e for e in evaluaciones_alumno if e.get('tipo_evaluacion') == 'cuestionario']
            evaluaciones_taller = [e for e in evaluaciones_alumno if e.get('tipo_evaluacion') == 'evaluacion_taller']
            
            # Calcular promedios
            promedio_cuestionarios = 0
            if evaluaciones_cuestionarios:
                calificaciones = [e.get('calificación', 0) for e in evaluaciones_cuestionarios if e.get('calificación') is not None]
                if calificaciones:
                    promedio_cuestionarios = sum(calificaciones) / len(calificaciones)
            
            promedio_evaluaciones = 0
            if evaluaciones_taller:
                promedios = [e.get('promedio_general', 0) for e in evaluaciones_taller if e.get('promedio_general') is not None]
                if promedios:
                    promedio_evaluaciones = sum(promedios) / len(promedios)
            
            alumno_info = {
                **alumno,
                'promedio_cuestionarios': round(promedio_cuestionarios, 2),
                'promedio_evaluaciones': round(promedio_evaluaciones, 2),
                'tiene_cuestionarios': len(evaluaciones_cuestionarios) > 0,
                'tiene_evaluaciones': len(evaluaciones_taller) > 0,
                'evaluaciones_cuestionarios': evaluaciones_cuestionarios,
                'evaluaciones_taller': evaluaciones_taller
            }
            alumnos_con_calificaciones.append(alumno_info)

        return render_template('admin/alumnos_curso.html', 
                             curso=curso, 
                             alumnos=alumnos_con_calificaciones)

    except Exception as e:
        print(f"ERROR en alumnos_curso: {e}")
        flash('Error al cargar los alumnos del curso', 'error')
        return redirect(url_for('gestion_cursos'))

# Ruta para ver detalle de evaluación específica de un alumno
@app.route('/admin/alumno/<alumno_email>/evaluacion/<evaluacion_id>')
@login_required(role='admin')
def detalle_evaluacion_alumno(alumno_email, evaluacion_id):
    try:
        evaluacion = Database.get_evaluacion_by_id(evaluacion_id)
        if not evaluacion:
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('gestion_cursos'))
        
        # Verificar que la evaluación pertenece al alumno
        if evaluacion['alumno_email'] != alumno_email:
            flash('No tienes permisos para ver esta evaluación', 'error')
            return redirect(url_for('gestion_cursos'))
        
        # Obtener información adicional
        examen = Database.get_examen_by_id(str(evaluacion['examen_id']))
        curso = Database.get_curso_by_id(str(evaluacion['curso_id']))
        alumno = Database.get_alumno_by_email(alumno_email)
        
        return render_template('admin/detalle_evaluacion_alumno.html',
                            evaluacion=evaluacion,
                            examen=examen,
                            curso=curso,
                            alumno=alumno)
    
    except Exception as e:
        print(f"ERROR en detalle_evaluacion_alumno: {e}")
        flash('Error al cargar el detalle de la evaluación', 'error')
        return redirect(url_for('gestion_cursos'))



# API para obtener datos (opcional)
@app.route('/api/cursos')
@login_required()
def api_cursos():
    cursos = list(Database.get_cursos_activos())
    return jsonify([{
        'id': str(curso['_id']),
        'nombre': curso['nombre'],
        'instructor': curso.get('instructor_email', '')
    } for curso in cursos])

# Manejo de errores
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template('error.html', error='Página no encontrada'), 404

@app.errorhandler(500)
def error_servidor(error):
    return render_template('error.html', error='Error interno del servidor'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)



def convertir_escala_evaluacion(puntaje):
    """Convertir puntaje numérico a texto descriptivo"""
    if puntaje >= 5.5:
        return "Excelente"
    elif puntaje >= 4.5:
        return "Muy Bien"
    elif puntaje >= 3.5:
        return "Bien"
    elif puntaje >= 2.5:
        return "Regular"
    elif puntaje >= 1.5:
        return "Mal"
    else:
        return "Muy mal"