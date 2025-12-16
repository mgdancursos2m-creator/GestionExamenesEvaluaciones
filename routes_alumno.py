from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from bson import ObjectId
from datetime import datetime
from decorators import alumno_required, login_required
from models import db  # ✅ Cambio importante: Solo importar db
from decorators import login_required, admin_required, instructor_required, alumno_required

ESCALA_EVALUACION = {
    1: "Muy mal",
    2: "Mal", 
    3: "Regular",
    4: "Bien",
    5: "Muy Bien",
    6: "Excelente"
}

alumno_bp = Blueprint('alumno', __name__, url_prefix='/alumno')

# =============================================================================
# DASHBOARD Y RUTAS PRINCIPALES
# =============================================================================

@alumno_bp.route('/dashboard')
@login_required
def user_dashboard():
    if session.get('role') == 'alumno':
        try:
            # IMPORTANTE: session['user'] debe ser 'polopolo@comico.com'
            user_email = session.get('user')
            
            if not user_email:
                flash("No se encontró información de usuario", "warning")
                return redirect(url_for('login'))
            
            print(f"DEBUG: Buscando eventos para: {user_email}")
            
            # OBTENER LA CONEXIÓN REAL A MONGODB
            mongo_db = db._get_db()
            
            if mongo_db is None:
                flash("Error de conexión a la base de datos", "error")
                return render_template('user/dashboard.html', eventos=[], actividades=[])
            
            # 1. BUSCAR EVENTOS DONDE EL ALUMNO ESTÁ ASIGNADO
            eventos_cursor = mongo_db.Eventos.find({
                "alumnos_asignados": {
                    "$elemMatch": {"email": user_email}
                }
            })
            
            eventos_list = list(eventos_cursor)
            print(f"DEBUG: Encontrados {len(eventos_list)} eventos")
            
            eventos_procesados = []
            
            for evento in eventos_list:
                print(f"DEBUG: Procesando evento: {evento.get('curso_nombre')}")
                
                # 2. Obtener el curso relacionado
                curso = mongo_db.Cursos.find_one({"_id": evento["curso_id"]})
                
                # 3. Determinar si el curso tiene cuestionario y evaluación
                tiene_cuestionario = False
                tiene_evaluacion = False
                cuestionario_completado = False
                evaluacion_completada = False
                
                if curso:
                    # VERIFICAR CUESTIONARIO - ajustado a tu estructura
                    cuestionario_data = curso.get("cuestionario", {})
                    if cuestionario_data and cuestionario_data.get("preguntas"):
                        tiene_cuestionario = len(cuestionario_data["preguntas"]) > 0
                    
                    # VERIFICAR EVALUACIÓN - ajustado a tu estructura
                    evaluacion_data = curso.get("evaluacion", {})
                    if evaluacion_data and evaluacion_data.get("preguntas"):
                        tiene_evaluacion = len(evaluacion_data["preguntas"]) > 0
                    
                    # 4. Verificar si el alumno ya completó el cuestionario en este evento
                    if tiene_cuestionario and "cuestionarios_detalle" in evento:
                        for detalle in evento.get("cuestionarios_detalle", []):
                            if detalle.get("email") == user_email:
                                cuestionario_completado = True
                                break
                    
                    # 5. Verificar si el alumno ya completó la evaluación en este evento
                    if tiene_evaluacion and "evaluaciones_detalle" in evento:
                        for detalle in evento.get("evaluaciones_detalle", []):
                            if detalle.get("email") == user_email:
                                evaluacion_completada = True
                                break
                
                # 6. Construir objeto para el template
                evento_dict = {
                    "curso_nombre": evento.get("curso_nombre", "Sin nombre"),
                    "fecha_evento": evento.get("fecha_evento"),
                    "tiene_cuestionario": tiene_cuestionario,
                    "cuestionario_completado": cuestionario_completado,
                    "tiene_evaluacion": tiene_evaluacion,
                    "evaluacion_completada": evaluacion_completada,
                    "evento_id": str(evento["_id"]),
                    "curso_id": str(evento["curso_id"])
                }
                
                eventos_procesados.append(evento_dict)
                print(f"DEBUG: Evento añadido: {evento_dict}")
            
            # 7. OBTENER ACTIVIDADES RECIENTES
            actividades = []
            
            # Buscar eventos con cuestionarios completados por el alumno
            eventos_con_cuestionarios = mongo_db.Eventos.find({
                "cuestionarios_detalle": {
                    "$elemMatch": {"email": user_email}
                }
            })
            
            for evento in eventos_con_cuestionarios:
                for detalle in evento.get("cuestionarios_detalle", []):
                    if detalle.get("email") == user_email:
                        actividad = {
                            "tipo_evaluacion": "cuestionario",
                            "examen_nombre": f"Cuestionario - {evento.get('curso_nombre', 'Sin nombre')}",
                            "fecha_realizacion": detalle.get("fecha_respuesta", datetime.utcnow()),
                            "calificacion": detalle.get("calificacion"),
                            "curso_nombre": evento.get("curso_nombre", "Sin nombre")
                        }
                        actividades.append(actividad)
            
            # Buscar eventos con evaluaciones completadas por el alumno
            eventos_con_evaluaciones = mongo_db.Eventos.find({
                "evaluaciones_detalle": {
                    "$elemMatch": {"email": user_email}
                }
            })
            
            for evento in eventos_con_evaluaciones:
                for detalle in evento.get("evaluaciones_detalle", []):
                    if detalle.get("email") == user_email:
                        actividad = {
                            "tipo_evaluacion": "evaluacion",
                            "examen_nombre": f"Evaluación - {evento.get('curso_nombre', 'Sin nombre')}",
                            "fecha_realizacion": detalle.get("fecha_respuesta", datetime.utcnow()),
                            "promedio_general": detalle.get("promedio_general"),
                            "curso_nombre": evento.get("curso_nombre", "Sin nombre")
                        }
                        actividades.append(actividad)
            
            # Ordenar actividades por fecha
            actividades.sort(key=lambda x: x.get('fecha_realizacion', datetime.min), reverse=True)
            
            return render_template('user/dashboard.html', 
                                 eventos=eventos_procesados, 
                                 actividades=actividades)
        
        except Exception as e:
            print(f"Error detallado en dashboard: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return render_template('user/dashboard.html', eventos=[], actividades=[])
    else:
        return redirect(url_for('instructor.user_dashboard'))


# =============================================================================
# GESTIÓN DE EXÁMENES Y EVALUACIONES
# =============================================================================

@alumno_bp.route('/examenes')
@login_required
def user_examenes():
    """Muestra todos los exámenes completados por el alumno"""
    try:
        user_email = session.get('user')
        
        # Obtener la conexión a la base de datos
        mongo_db = db._get_db()
        
        # Buscar eventos donde el alumno haya completado cuestionarios
        eventos = mongo_db.Eventos.find({
            "alumnos_asignados.email": user_email,
            "cuestionarios_detalle": {
                "$elemMatch": {"email": user_email}
            }
        })
        
        examenes_completados = []
        for evento in eventos:
            # Encontrar el detalle del cuestionario del alumno
            for detalle in evento.get("cuestionarios_detalle", []):
                if detalle.get("email") == user_email:
                    examenes_completados.append({
                        "evento_id": str(evento.get("_id")),
                        "curso_nombre": evento.get("curso_nombre", "Curso sin nombre"),
                        "fecha_evento": evento.get("fecha_evento"),
                        "fecha_cuestionario": detalle.get("fecha_respuesta"),
                        "calificacion": detalle.get("calificacion", 0),
                        "respuestas_correctas": detalle.get("respuestas_correctas", 0),
                        "total_preguntas": detalle.get("total_preguntas", 0),
                        "estatus": "completado"
                    })
        
        # Ordenar por fecha más reciente
        examenes_completados.sort(key=lambda x: x.get("fecha_cuestionario", datetime.min), reverse=True)
        
        return render_template(
            'alumno/mis_examenes.html',
            examenes=examenes_completados
        )
        
    except Exception as e:
        print(f"ERROR en user_examenes: {str(e)}")
        flash("Error al cargar los exámenes", "error")
        return redirect(url_for('alumno.user_dashboard'))



@alumno_bp.route('/tomar_examen/<evento_id>/<curso_id>')
@login_required
def tomar_examen(evento_id, curso_id):
    try:
        # Obtener el evento usando tu módulo db
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash("Evento no encontrado", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        # Obtener el curso usando tu módulo db
        curso = db.get_curso_by_id(curso_id)
        if not curso:
            flash("Curso no encontrado", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        # Obtener el cuestionario del curso
        cuestionario = curso.get("cuestionario")
        if not cuestionario:
            flash("Este curso no tiene cuestionario disponible", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        # Verificar que el alumno esté inscrito en el evento
        user_email = session.get('user')
        alumno_inscrito = False
        
        for alumno in evento.get('alumnos_asignados', []):
            if alumno.get('email') == user_email:
                alumno_inscrito = True
                break
        
        if not alumno_inscrito:
            flash("No estás inscrito en este evento", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        # Verificar si ya completó el cuestionario
        cuestionarios_detalle = evento.get('cuestionarios_detalle', [])
        for detalle in cuestionarios_detalle:
            if detalle.get('email') == user_email:
                flash("Ya has completado este cuestionario", "info")
                return redirect(url_for('alumno.user_dashboard'))
        
        # Obtener las preguntas del cuestionario
        preguntas = cuestionario.get("preguntas", [])
        
        # Preparar datos para la plantilla - IMPORTANTE: Ajustar la estructura
        examen_data = {
            "titulo": cuestionario.get("nombre", "Cuestionario"),
            "instrucciones": cuestionario.get("instrucciones", "Responde todas las preguntas."),
            "tiempo_limite": 60,  # Valor por defecto
            "_id": str(curso.get("_id"))
        }
        
        # Preparar las preguntas en formato que entienda la plantilla
        preguntas_formateadas = []
        for pregunta in preguntas:
            # Convertir la estructura de pregunta de MongoDB a formato esperado por la plantilla
            pregunta_formateada = {
                "_id": str(pregunta.get("numero")),  # Usar el número como ID
                "enunciado": pregunta.get("pregunta", ""),
                "tipo": "multiple_choice",  # Todas son de opción múltiple según tu estructura
                "opciones": []
            }
            
            # Procesar las opciones
            opciones = pregunta.get("opciones", [])
            for i, opcion_texto in enumerate(opciones):
                # Limpiar las opciones (quitando comillas extras)
                opcion_limpia = opcion_texto.strip().strip('"')
                pregunta_formateada["opciones"].append({
                    "texto": opcion_limpia,
                    "valor": chr(97 + i)  # a, b, c, etc.
                })
            
            preguntas_formateadas.append(pregunta_formateada)
        
        return render_template(
            'alumno/tomar_examen.html',
            examen=examen_data,
            preguntas=preguntas_formateadas,  # Usar las preguntas formateadas
            curso_nombre=curso.get("nombre"),
            evento_id=evento_id,
            curso_id=curso_id
        )
        
    except Exception as e:
        print(f"ERROR en tomar_examen: {str(e)}")
        flash("Error al cargar el cuestionario", "error")
        return redirect(url_for('alumno.user_dashboard'))

# Guardar las respuestas del cuestionario
@alumno_bp.route('/guardar_cuestionario/<evento_id>', methods=['POST'])
@login_required
def guardar_cuestionario(evento_id):
    try:
        user_email = session.get('user')
        user_nombre = session.get('nombre')

        # Obtener respuestas del formulario
        respuestas = request.form.to_dict()

        # Obtener el evento y curso
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash("Evento no encontrado", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        curso = db.get_curso_by_id(str(evento.get('curso_id')))
        if not curso or not curso.get("cuestionario"):
            flash("Curso o cuestionario no encontrado", "error")
            return redirect(url_for('alumno.user_dashboard'))

        # Calcular calificación
        preguntas = curso.get("cuestionario", {}).get("preguntas", [])
        respuestas_correctas = 0

        for pregunta in preguntas:
            pregunta_num = pregunta.get("numero")
            respuesta_usuario = respuestas.get(f"pregunta_{pregunta_num}")
            respuesta_correcta = pregunta.get("respuesta_correcta")

            if respuesta_usuario and respuesta_usuario.strip().lower() == respuesta_correcta.strip().lower():
                respuestas_correctas += 1

        total_preguntas = len(preguntas)
        calificación_calculada = (respuestas_correctas / total_preguntas * 100) if total_preguntas > 0 else 0

        # Crear objeto de detalle del cuestionario
        detalle_cuestionario = {
            "email": user_email,
            "nombre": user_nombre,
            "fecha_respuesta": datetime.utcnow(),
            "respuestas": respuestas,
            "calificacion": calificación_calculada,
            "estatus": "completado",
            "respuestas_correctas": respuestas_correctas,
            "total_preguntas": total_preguntas
        }

        # Obtener conexión directa a MongoDB para operaciones complejas
        mongo_db = db._get_db()

        # Primero: Agregar el cuestionario del alumno
        result = mongo_db.Eventos.update_one(
            {
                "_id": ObjectId(evento_id),
                "alumnos_asignados.email": user_email
            },
            {
                "$push": {"cuestionarios_detalle": detalle_cuestionario},
                "$set": {
                    "fecha_actualizacion": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            # Segundo: Recalcular métricas globales
            evento_actualizado = mongo_db.Eventos.find_one({"_id": ObjectId(evento_id)})
            
            if evento_actualizado and 'cuestionarios_detalle' in evento_actualizado:
                cuestionarios = evento_actualizado['cuestionarios_detalle']
                total_cuestionarios = len(cuestionarios)
                
                if total_cuestionarios > 0:
                    # Calcular el promedio REAL de todos los cuestionarios
                    suma_calificaciones = sum(q.get('calificacion', 0) for q in cuestionarios)
                    promedio_real = suma_calificaciones / total_cuestionarios
                    
                    # Actualizar con los valores correctos
                    mongo_db.Eventos.update_one(
                        {"_id": ObjectId(evento_id)},
                        {
                            "$set": {
                                "cuestionarios_contestados": total_cuestionarios,
                                "promedio_cuestionarios": promedio_real
                            }
                        }
                    )
                else:
                    # No hay cuestionarios (caso improbable)
                    mongo_db.Eventos.update_one(
                        {"_id": ObjectId(evento_id)},
                        {
                            "$set": {
                                "cuestionarios_contestados": 0,
                                "promedio_cuestionarios": 0
                            }
                        }
                    )
            
            flash(f"¡Cuestionario completado! Calificación: {calificación_calculada:.1f}%", "success")
        else:
            flash("No se pudo guardar el cuestionario. Verifica que estés inscrito en el evento.", "warning")

        return redirect(url_for("alumno.user_dashboard"))

    except Exception as e:
        print(f"ERROR en guardar_cuestionario: {e}")
        flash("Error al guardar el cuestionario", "error")
        return redirect(url_for('alumno.user_dashboard'))



# procesar el examen
@alumno_bp.route('/procesar_examen/<evento_id>/<curso_id>', methods=['POST'])
@login_required
def procesar_examen(evento_id, curso_id):
    try:
        user_email = session.get('user')
        user_nombre = session.get('nombre')
        
        print(f"DEBUG procesar_examen: Usuario={user_email}, Evento={evento_id}, Curso={curso_id}")

        # Obtener respuestas del formulario
        respuestas = request.form.to_dict()
        print(f"DEBUG: Respuestas recibidas: {respuestas}")

        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash("Evento no encontrado", "error")
            return redirect(url_for('alumno.user_dashboard'))

        # Obtener el curso y cuestionario
        curso = db.get_curso_by_id(curso_id)
        if not curso or not curso.get("cuestionario"):
            flash("Curso o cuestionario no encontrado", "error")
            return redirect(url_for('alumno.user_dashboard'))

        # Calcular calificación
        preguntas_originales = curso.get("cuestionario", {}).get("preguntas", [])
        print(f"DEBUG: Número de preguntas originales: {len(preguntas_originales)}")
        
        respuestas_correctas = 0
        resultados_detalle = []

        for pregunta in preguntas_originales:
            pregunta_num = str(pregunta.get('numero'))
            respuesta_usuario = respuestas.get(f'pregunta_{pregunta_num}')
            respuesta_correcta = pregunta.get('respuesta_correcta')
            
            # Verificar si la respuesta es correcta
            es_correcta = respuesta_usuario and respuesta_usuario.strip().lower() == respuesta_correcta.strip().lower()

            if es_correcta:
                respuestas_correctas += 1

            # Guardar detalle para mostrar resultados
            resultados_detalle.append({
                'pregunta': pregunta.get('pregunta'),
                'respuesta_usuario': respuesta_usuario or 'No respondida',
                'respuesta_correcta': respuesta_correcta,
                'es_correcta': es_correcta
            })

        total_preguntas = len(preguntas_originales)
        calificación_calculada = (respuestas_correctas / total_preguntas * 100) if total_preguntas > 0 else 0
        
        print(f"DEBUG: Calificación calculada: {calificación_calculada}%")
        print(f"DEBUG: Respuestas correctas: {respuestas_correctas}/{total_preguntas}")
        
        # ================ CÓDIGO PARA GUARDAR EN MONGODB ================
        
        # Crear objeto de detalle del cuestionario
        detalle_cuestionario = {
            "email": user_email,
            "nombre": user_nombre,
            "fecha_respuesta": datetime.utcnow(),
            "respuestas": respuestas,
            "calificación": calificación_calculada,
            "estatus": "completado",
            "respuestas_correctas": respuestas_correctas,
            "total_preguntas": total_preguntas,
            "resultados_detalle": resultados_detalle
        }
        
        print(f"DEBUG: Detalle cuestionario a guardar: {detalle_cuestionario}")
        
        # Obtener conexión directa a MongoDB
        mongo_db = db._get_db()
        
        # Verificar que el alumno está inscrito en el evento
        alumno_inscrito = any(
            alumno.get('email') == user_email 
            for alumno in evento.get('alumnos_asignados', [])
        )
        
        if not alumno_inscrito:
            flash("No estás inscrito en este evento", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        # 1. Agregar el cuestionario del alumno al array cuestionarios_detalle
        resultado_insercion = mongo_db.Eventos.update_one(
            {
                "_id": ObjectId(evento_id),
                "alumnos_asignados.email": user_email
            },
            {
                "$push": {"cuestionarios_detalle": detalle_cuestionario},
                "$set": {
                    "fecha_actualizacion": datetime.utcnow()
                }
            }
        )
        
        print(f"DEBUG: Resultado inserción - matched: {resultado_insercion.matched_count}, modified: {resultado_insercion.modified_count}")
        
        if resultado_insercion.modified_count > 0:
            # 2. Recalcular métricas del evento
            evento_actualizado = mongo_db.Eventos.find_one({"_id": ObjectId(evento_id)})
            
            if evento_actualizado and 'cuestionarios_detalle' in evento_actualizado:
                cuestionarios = evento_actualizado['cuestionarios_detalle']
                total_cuestionarios = len(cuestionarios)
                
                if total_cuestionarios > 0:
                    # Calcular el promedio de todos los cuestionarios
                    suma_calificaciones = sum(q.get('calificación', 0) for q in cuestionarios)
                    promedio_real = suma_calificaciones / total_cuestionarios
                    
                    # Actualizar métricas del evento
                    mongo_db.Eventos.update_one(
                        {"_id": ObjectId(evento_id)},
                        {
                            "$set": {
                                "cuestionarios_contestados": total_cuestionarios,
                                "promedio_cuestionarios": promedio_real
                            }
                        }
                    )
                    
                    print(f"DEBUG: Métricas actualizadas - Total: {total_cuestionarios}, Promedio: {promedio_real}")
                else:
                    # Si no hay cuestionarios (caso improbable)
                    mongo_db.Eventos.update_one(
                        {"_id": ObjectId(evento_id)},
                        {
                            "$set": {
                                "cuestionarios_contestados": 0,
                                "promedio_cuestionarios": 0
                            }
                        }
                    )
            
            flash(f"¡Cuestionario completado exitosamente! Calificación: {calificación_calculada:.1f}%", "success")
        else:
            flash("Error: No se pudo guardar el cuestionario. El alumno no está inscrito en el evento.", "warning")
        
        # ================ FIN DEL CÓDIGO PARA GUARDAR ================
        
        # Mostrar la página de resultados
        # Si la plantilla no existe, usamos render_template_string temporalmente
        try:
            return render_template('alumno/resultado_examen.html',
                calificacion=calificación_calculada,
                respuestas_correctas=respuestas_correctas,
                total_preguntas=total_preguntas,
                resultados=resultados_detalle,
                curso_nombre=curso.get('nombre'),
                evento_id=evento_id)
        except Exception as template_error:
            print(f"ERROR con plantilla: {template_error}")
            # Fallback: mostrar resultados en HTML básico
            resultados_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Resultados</title></head>
            <body>
                <h1>Resultados del Examen</h1>
                <h2>Curso: {curso.get('nombre')}</h2>
                <p><strong>Calificación:</strong> {calificación_calculada:.1f}%</p>
                <p><strong>Respuestas correctas:</strong> {respuestas_correctas} de {total_preguntas}</p>
                <h3>Detalle:</h3>
                <ul>
            """
            
            for resultado in resultados_detalle:
                resultados_html += f"""
                <li>
                    <strong>{resultado['pregunta']}</strong><br>
                    Tu respuesta: {resultado['respuesta_usuario']}<br>
                    Correcta: {resultado['respuesta_correcta']}<br>
                    {'✓ Correcto' if resultado['es_correcta'] else '✗ Incorrecto'}
                </li>
                """
            
            resultados_html += """
                </ul>
                <a href="/user/dashboard">Volver al Dashboard</a>
            </body>
            </html>
            """
            
            return resultados_html

    except Exception as e:
        print(f"ERROR en procesar_examen: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Error al procesar el examen: {str(e)}", "error")
        return redirect(url_for('alumno.user_dashboard'))

@alumno_bp.route('/examen/<examen_id>/evaluar', methods=['POST'])
@alumno_required
def evaluar_examen(examen_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        examen = db.get_examen_by_id(examen_id)
        if not examen:
            flash('Examen no encontrado', 'error')
            return redirect(url_for('alumno.user_examenes'))
        
        respuestas = request.form
        respuestas_correctas = 0
        total_preguntas = len(examen['preguntas'])
        resultados = []
        
        for i, pregunta in enumerate(examen['preguntas']):
            respuesta_usuario = respuestas.get(f'pregunta_{i}')
            es_correcta = (respuesta_usuario and 
                          respuesta_usuario.strip() == pregunta['respuesta_correcta'].strip())
            
            if es_correcta:
                respuestas_correctas += 1
            
            resultados.append({
                'pregunta': pregunta['pregunta'],
                'respuesta_usuario': respuesta_usuario,
                'respuesta_correcta': pregunta['respuesta_correcta'],
                'es_correcta': es_correcta
            })
        
        if total_preguntas > 0:
            calificacion = (respuestas_correctas / total_preguntas) * 100
        else:
            calificacion = 0

        # ✅ Cambio: Usar db en lugar de Database
        alumno = db.get_alumno_by_email(session['user'])
        curso = db.get_curso_by_id(str(examen['curso_id']))

        cuestionario_data = {
            'alumno_email': session['user'], 
            'alumno_nombre': session.get('nombre'), 
            'examen_id': ObjectId(examen_id), 
            'examen_nombre': examen['nombre'], 
            'curso_id': ObjectId(str(examen['curso_id'])),
            'curso_nombre': curso['nombre'] if curso else 'N/A', 
            'instructor_email': curso.get('instructor_email', 'N/A') if curso else 'N/A', 
            'calificacion': float(calificacion),
            'resultados': resultados, 
            'fecha_realizacion': datetime.now(), 
            'respuestas_correctas': respuestas_correctas, 
            'total_preguntas': total_preguntas,
            'tipo_evaluacion': 'cuestionario'
        }

        # ✅ Cambio: Usar db en lugar de Database
        result = db.insert_cuestionario(cuestionario_data)

        if examen and examen.get('tipo_examen') == 'cuestionario':
            # ✅ Cambio: Usar db en lugar de Database
            eventos = list(db.get_eventos_by_curso(str(examen['curso_id'])))
            for evento in eventos:
                alumnos_evento = evento.get('alumnos_asignados', [])
                if any(alumno['email'] == session['user'] for alumno in alumnos_evento):
                    # Actualizar métricas del evento
                    from routes_eventos import actualizar_metricas_evento
                    actualizar_metricas_evento(str(evento['_id']))
                    break
        
        flash(f"Examen completado. Calificación: {calificacion:.2f}%", 'success')
        return redirect(url_for('alumno.user_dashboard'))

    except Exception as e:
        print(f"ERROR CRÍTICO en evaluar_examen: {e}")
        flash(f'Error al evaluar examen: {str(e)}', 'error')
        return redirect(url_for('alumno.user_examenes'))

# =============================================================================
# EVALUACIONES DE TALLER
# =============================================================================

@alumno_bp.route('/tomar_evaluacion/<evento_id>/<curso_id>')
@login_required
def tomar_evaluacion(evento_id, curso_id):
    """Muestra el formulario de evaluación para un evento"""
    try:
        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash("Evento no encontrado", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        # Obtener el curso
        curso = db.get_curso_by_id(curso_id)
        if not curso:
            flash("Curso no encontrado", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        # Obtener la evaluación del curso
        evaluacion_data = curso.get("evaluacion")
        if not evaluacion_data:
            flash("Este curso no tiene evaluación disponible", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        # Verificar que el alumno esté inscrito
        user_email = session.get('user')
        alumno_inscrito = False
        for alumno in evento.get('alumnos_asignados', []):
            if alumno.get('email') == user_email:
                alumno_inscrito = True
                break
        
        if not alumno_inscrito:
            flash("No estás inscrito en este evento", "error")
            return redirect(url_for('alumno.user_dashboard'))
        
        # Verificar si ya completó la evaluación
        evaluaciones_detalle = evento.get('evaluaciones_detalle', [])
        for detalle in evaluaciones_detalle:
            if detalle.get('email') == user_email:
                flash("Ya has completado esta evaluación", "info")
                return redirect(url_for('alumno.user_dashboard'))
        
        # Obtener las preguntas de la evaluación
        preguntas = evaluacion_data.get("preguntas", [])
        
        # Preparar datos para la plantilla
        evaluacion = {
            "nombre": evaluacion_data.get("nombre", "Evaluación del Taller"),
            "descripcion": evaluacion_data.get("descripcion", ""),
            "instrucciones": evaluacion_data.get("estructura", {}).get("escala", 
                           "(1) Muy mal (2) Mal (3) Regular (4) Bien (5) Muy Bien (6) Excelente"),
            "_id": str(curso.get("_id"))
        }
        
        return render_template(
            'alumno/tomar_evaluacion.html',
            evaluacion=evaluacion,
            preguntas=preguntas,
            curso_nombre=curso.get("nombre"),
            evento_id=evento_id,
            curso_id=curso_id
        )
        
    except Exception as e:
        print(f"ERROR en tomar_evaluacion: {str(e)}")
        flash("Error al cargar la evaluación", "error")
        return redirect(url_for('alumno.user_dashboard'))


#Procesar la evaluación
@alumno_bp.route('/procesar_evaluacion/<evento_id>/<curso_id>', methods=['POST'])
@login_required
def procesar_evaluacion(evento_id, curso_id):
    """Procesa las respuestas de la evaluación y guarda en el Evento"""

    try:
        user_email = session.get('user')
        user_nombre = session.get('nombre')

        # Obtener respuestas del formulario
        respuestas = request.form.to_dict()

        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash("Evento no encontrado", "error")
            return redirect(url_for('alumno.user_dashboard'))

        # Obtener el curso y evaluación
        curso = db.get_curso_by_id(curso_id)
        if not curso or not curso.get("evaluacion"):
            flash("Curso o evaluación no encontrada", "error")
            return redirect(url_for('alumno.user_dashboard'))

        # Calcular puntuación promedio
        preguntas = curso.get("evaluacion", {}).get("preguntas", [])
        total_puntuacion = 0
        preguntas_escala = 0
        comentarios = ""
        respuestas_detalle = []

        for pregunta in preguntas:
            pregunta_id = f"pregunta_{pregunta.get('numero')}" if pregunta.get('numero') else "comentario"
            respuesta_usuario = respuestas.get(pregunta_id, "").strip()

            # Procesar según el tipo de pregunta
            if pregunta.get('tipo') == 'escala' and respuesta_usuario:
                try:
                    puntuacion = int(respuesta_usuario)
                    total_puntuacion += puntuacion
                    preguntas_escala += 1

                    # Obtener texto descriptivo de la escala
                    escala_texto = ESCALA_EVALUACION.get(puntuacion, str(puntuacion))

                    respuestas_detalle.append({
                        'pregunta': pregunta.get('pregunta'),
                        'respuesta': respuesta_usuario,
                        'escala_texto': escala_texto,
                        'tipo': 'escala',
                        'seccion': pregunta.get('seccion')
                    })
                except ValueError:
                    pass
            elif pregunta.get('tipo') == 'texto_largo':
                comentarios = respuesta_usuario
                respuestas_detalle.append({
                    'pregunta': pregunta.get('pregunta'),
                    'respuesta': respuesta_usuario,
                    'tipo': 'texto_largo',
                    'seccion': pregunta.get('seccion')
                })

        # Calcular promedio
        promedio = total_puntuacion / preguntas_escala if preguntas_escala > 0 else 0

        # Crear objeto de detalle de la evaluación
        detalle_evaluacion = {
            "email": user_email,
            "nombre": user_nombre,
            "fecha_respuesta": datetime.utcnow(),
            "respuestas": respuestas,
            "respuestas_detalle": respuestas_detalle,
            "puntuacion_promedio": promedio,
            "comentarios": comentarios,
            "total_preguntas": len(preguntas),
            "preguntas_escala": preguntas_escala,
            "estatus": "completado"
        }

        # Obtener conexión directa a MongoDB
        mongo_db = db._get_db()

        # Primero: Agregar la evaluación del alumno
        result = mongo_db.Eventos.update_one(
            {
                "_id": ObjectId(evento_id),
                "alumnos_asignados.email": user_email
            },
            {
                "$push": {"evaluaciones_detalle": detalle_evaluacion},
                "$set": {
                    "fecha_actualizacion": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            # Recalcular métricas globales para evaluaciones
            evento_actualizado = mongo_db.Eventos.find_one({"_id": ObjectId(evento_id)})
            
            if evento_actualizado and 'evaluaciones_detalle' in evento_actualizado:
                evaluaciones = evento_actualizado['evaluaciones_detalle']
                total_evaluaciones = len(evaluaciones)
                
                if total_evaluaciones > 0:
                    # Calcular el promedio REAL de todas las evaluaciones
                    suma_puntuaciones = sum(e.get('puntuacion_promedio', 0) for e in evaluaciones)
                    promedio_real = suma_puntuaciones / total_evaluaciones
                    
                    # Actualizar con los valores correctos
                    mongo_db.Eventos.update_one(
                        {"_id": ObjectId(evento_id)},
                        {
                            "$set": {
                                "evaluaciones_contestadas": total_evaluaciones,
                                "promedio_evaluaciones": promedio_real
                            }
                        }
                    )
                else:
                    # No hay evaluaciones
                    mongo_db.Eventos.update_one(
                        {"_id": ObjectId(evento_id)},
                        {
                            "$set": {
                                "evaluaciones_contestadas": 0,
                                "promedio_evaluaciones": 0
                            }
                        }
                    )
            
            # Mostrar resultados inmediatamente
            return render_template('alumno/resultado_evaluacion.html',
                promedio=promedio,
                puntuacion_total=total_puntuacion,
                preguntas_escala=preguntas_escala,
                respuestas=respuestas_detalle,
                comentarios=comentarios,
                curso_nombre=curso.get('nombre'),
                evento_id=evento_id)
        else:
            flash("No se pudo guardar la evaluación. Verifica que estés inscrito en el evento.", "warning")
            return redirect(url_for('alumno.user_dashboard'))
    except Exception as e:
        print(f"ERROR en procesar_evaluacion: {str(e)}")
        flash("Error al procesar la evaluación", "error")
        return redirect(url_for('alumno.user_dashboard'))

#Ver evaluación

# User Evaluación
@alumno_bp.route('/evaluaciones')
@login_required
def user_evaluaciones():
    """Muestra todas las evaluaciones completadas por el alumno (desde Eventos)"""
    try:
        user_email = session.get('user')
        
        # Obtener la conexión a la base de datos
        mongo_db = db._get_db()
        
        # Buscar eventos donde el alumno haya completado evaluaciones
        eventos = mongo_db.Eventos.find({
            "alumnos_asignados.email": user_email,
            "evaluaciones_detalle": {
                "$elemMatch": {"email": user_email}
            }
        })
        
        evaluaciones_completadas = []
        for evento in eventos:
            # Encontrar el detalle de la evaluación del alumno
            for detalle in evento.get("evaluaciones_detalle", []):
                if detalle.get("email") == user_email:
                    # También obtener el curso para el nombre de la evaluación
                    curso = db.get_curso_by_id(str(evento.get("curso_id", "")))
                    evaluacion_nombre = "Evaluación del Taller"
                    if curso and curso.get("evaluacion"):
                        evaluacion_nombre = curso.get("evaluacion", {}).get("nombre", "Evaluación del Taller")
                    
                    evaluaciones_completadas.append({
                        "evento_id": str(evento.get("_id")),
                        "curso_nombre": evento.get("curso_nombre", "Curso sin nombre"),
                        "evaluacion_nombre": evaluacion_nombre,
                        "fecha_evento": evento.get("fecha_evento"),
                        "fecha_evaluacion": detalle.get("fecha_respuesta"),
                        "puntuacion_promedio": detalle.get("puntuacion_promedio", 0),
                        "comentarios": detalle.get("comentarios", ""),
                        "estatus": "completado",
                        "respuestas_detalle": detalle.get("respuestas_detalle", [])
                    })
        
        # Ordenar por fecha más reciente
        evaluaciones_completadas.sort(key=lambda x: x.get("fecha_evaluacion", datetime.min), reverse=True)
        
        return render_template(
            'alumno/mis_evaluaciones.html',
            evaluaciones=evaluaciones_completadas
        )
        
    except Exception as e:
        print(f"ERROR en user_evaluaciones: {str(e)}")
        flash("Error al cargar las evaluaciones", "error")
        return redirect(url_for('alumno.user_dashboard'))



@alumno_bp.route('/evaluacion_taller/<examen_id>/enviar', methods=['POST'])
@alumno_required
def enviar_evaluacion_taller(examen_id):
    try:
        # ✅ Cambio: Usar db en lugar de Database
        examen = db.get_examen_by_id(examen_id)
        if not examen:
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('alumno.user_examenes'))

        respuestas = request.form
        # ✅ Cambio: Usar db en lugar de Database
        curso = db.get_curso_by_id(str(examen['curso_id']))
        if not curso:
            flash('Error: Curso no encontrado', 'error')
            return redirect(url_for('alumno.user_examenes'))

        resultados = {
            'informacion_general': {
                'nombre_taller': respuestas.get('nombre_taller', ''),
                'nombre_instructor': respuestas.get('nombre_instructor', '')
            },
            'respuestas_taller': {},
            'respuestas_instructor': {},
            'comentarios': respuestas.get('comentarios', '')
        }

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
                except ValueError:
                    puntaje = 0

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
                except ValueError:
                    puntaje = 0

        promedio_taller = sum(puntajes_taller) / len(puntajes_taller) if puntajes_taller else 0
        promedio_instructor = sum(puntajes_instructor) / len(puntajes_instructor) if puntajes_instructor else 0
        promedio_general = (promedio_taller + promedio_instructor) / 2 if puntajes_taller and puntajes_instructor else 0

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

        # ✅ Cambio: Usar db en lugar de Database
        db.insert_evaluacion(evaluacion_data)

        examen = db.get_examen_by_id(examen_id)
        if examen:
            # ✅ Cambio: Usar db en lugar de Database
            eventos = list(db.get_eventos_by_curso(str(examen['curso_id'])))
            for evento in eventos:
                alumnos_evento = evento.get('alumnos_asignados', [])
                if any(alumno['email'] == session['user'] for alumno in alumnos_evento):
                    from routes_eventos import actualizar_metricas_evento
                    actualizar_metricas_evento(str(evento['_id']))
                    break
        
        flash(f'Evaluación enviada exitosamente! Promedio general: {promedio_general:.2f}/6', 'success')
        return redirect(url_for('alumno.user_dashboard'))

    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        flash(f'Error al enviar evaluación: {str(e)}', 'error')
        return redirect(url_for('alumno.user_examenes'))

# =============================================================================
# VER RESULTADOS
# =============================================================================

@alumno_bp.route('/ver_evaluacion/<evento_id>')
@login_required
def ver_evaluacion(evento_id):
    """Muestra los detalles de una evaluación específica desde Eventos"""
    try:
        user_email = session.get('user')
        
        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash("Evento no encontrado", "error")
            return redirect(url_for('alumno.user_evaluaciones'))
        
        # Buscar el detalle de la evaluación del alumno
        evaluacion_detalle = None
        for detalle in evento.get("evaluaciones_detalle", []):
            if detalle.get("email") == user_email:
                evaluacion_detalle = detalle
                break
        
        if not evaluacion_detalle:
            flash("No se encontraron resultados para esta evaluación", "error")
            return redirect(url_for('alumno.user_evaluaciones'))
        
        # Obtener información del curso
        curso = db.get_curso_by_id(str(evento.get("curso_id", "")))
        
        # Formatear las respuestas si no están en el formato esperado
        respuestas_formateadas = evaluacion_detalle.get("respuestas_detalle", [])
        if not respuestas_formateadas and evaluacion_detalle.get("respuestas"):
            # Intentar formatear desde respuestas crudas
            respuestas = evaluacion_detalle.get("respuestas", {})
            for clave, valor in respuestas.items():
                if clave.startswith("pregunta_"):
                    respuestas_formateadas.append({
                        'pregunta': f"Pregunta {clave.replace('pregunta_', '')}",
                        'respuesta': valor,
                        'escala_texto': valor
                    })
        
        return render_template(
            'alumno/ver_evaluacion.html',
            evaluacion={
                "nombre": curso.get("evaluacion", {}).get("nombre", "Evaluación") if curso else "Evaluación",
                "curso_nombre": curso.get("nombre", "Curso sin nombre") if curso else "Curso sin nombre",
                "fecha_realizacion": evaluacion_detalle.get("fecha_respuesta"),
                "puntuacion_promedio": evaluacion_detalle.get("puntuacion_promedio", 0),
                "comentarios": evaluacion_detalle.get("comentarios", ""),
                "respuestas": respuestas_formateadas
            }
        )
        
    except Exception as e:
        print(f"ERROR en ver_evaluacion: {str(e)}")
        flash("Error al cargar la evaluación", "error")
        return redirect(url_for('alumno.user_evaluaciones'))


@alumno_bp.route('/ver_cuestionario/<evento_id>')
@login_required
def ver_cuestionario(evento_id):
    """Muestra los detalles de un cuestionario específico"""
    try:
        user_email = session.get('user')
        
        # Obtener el evento
        evento = db.get_evento_by_id(evento_id)
        if not evento:
            flash("Evento no encontrado", "error")
            return redirect(url_for('alumno.user_examenes'))
        
        # Buscar el detalle del cuestionario del alumno
        cuestionario_detalle = None
        for detalle in evento.get("cuestionarios_detalle", []):
            if detalle.get("email") == user_email:
                cuestionario_detalle = detalle
                break
        
        if not cuestionario_detalle:
            flash("No se encontraron resultados para este cuestionario", "error")
            return redirect(url_for('alumno.user_examenes'))
        
        # Obtener información del curso
        curso = db.get_curso_by_id(str(evento.get("curso_id", "")))
        
        return render_template(
            'alumno/ver_cuestionario.html',
            cuestionario={
                "examen_nombre": curso.get("cuestionario", {}).get("nombre", "Cuestionario") if curso else "Cuestionario",
                "curso_nombre": curso.get("nombre", "Curso sin nombre") if curso else "Curso sin nombre",
                "calificacion": cuestionario_detalle.get("calificacion", 0),
                "respuestas_correctas": cuestionario_detalle.get("respuestas_correctas", 0),
                "total_preguntas": cuestionario_detalle.get("total_preguntas", 0),
                "fecha_realizacion": cuestionario_detalle.get("fecha_respuesta"),
                "resultados": cuestionario_detalle.get("resultados_detalle", [])
            }
        )
        
    except Exception as e:
        print(f"ERROR en ver_cuestionario: {str(e)}")
        flash("Error al cargar el cuestionario", "error")
        return redirect(url_for('alumno.user_examenes'))