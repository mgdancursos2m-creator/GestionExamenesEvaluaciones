from flask import Flask, Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from bson import ObjectId
from datetime import datetime
from config import config
from models import Database  # SOLO importar Database

app = Flask(__name__)
app.config.from_object(config['default'])

# Importar blueprints
from routes_admin import admin_bp
from routes_instructor import instructor_bp
from routes_alumno import alumno_bp
from routes_eventos import eventos_bp
from decorators import login_required, admin_required, instructor_required, alumno_required

# Registrar blueprints
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(instructor_bp, url_prefix='/instructor')
app.register_blueprint(alumno_bp, url_prefix='/user')
app.register_blueprint(eventos_bp)  # Sin url_prefix

# Registro de routes
@app.before_request
def log_routes():
    if request.endpoint:
        print(f"Ruta accedida: {request.endpoint}")

# Agregar filtro para fecha actual en templates
@app.context_processor
def utility_processor():
    # Función para convertir escala de cuestionarios (0-10) a texto
    def convertir_escala_cuestionario(puntaje):
        if puntaje >= 9:
            return "Excelente"
        elif puntaje >= 8:
            return "Muy Bien"
        elif puntaje >= 7:
            return "Bien"
        elif puntaje >= 6:
            return "Regular"
        else:
            return "Necesita mejorar"
    
    # Función para convertir escala de evaluaciones (0-6) a texto
    def convertir_escala_evaluacion(puntaje):
        if puntaje >= 5.5:
            return "Excelente"
        elif puntaje >= 4.5:
            return "Muy Bien"
        elif puntaje >= 3.5:
            return "Bien"
        elif puntaje >= 2.5:
            return "Regular"
        else:
            return "Necesita mejorar"
    
    return {
        'now': datetime.now,
        'convertir_escala_cuestionario': convertir_escala_cuestionario,
        'convertir_escala_evaluacion': convertir_escala_evaluacion
    }

# =============================================================================
# RUTAS PÚBLICAS
# =============================================================================

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

        # Validación para admin
        if email == 'admin' and password == 'nimda':
            session['user'] = 'admin'
            session['role'] = 'admin'
            session['nombre'] = 'Administrador'
            session.permanent = True
            return redirect(url_for('admin.admin_dashboard'))  # ✅ Corregido

        # Para usuarios normales
        if not email or '@' not in email:
            flash('Por favor, ingresa un correo electrónico válido', 'error')
            return render_template('login.html')

        if not password or len(password) < 4:
            flash('La contraseña debe tener al menos 4 caracteres', 'error')
            return render_template('login.html')

        # Verificar alumno existente
        alumno = db.get_alumno_by_email(email)
        if alumno:
            session['user'] = email
            session['role'] = 'alumno'
            session['nombre'] = alumno.get('nombre')
            session.permanent = True
            return redirect(url_for('alumno.user_dashboard'))  # ✅ Corregido

        # Verificar instructor
        instructor = db.get_instructor_by_email(email)
        if instructor:
            session['user'] = email
            session['role'] = 'instructor'
            session['nombre'] = instructor.get('nombre')
            session.permanent = True
            return redirect(url_for('instructor.user_dashboard'))  # ✅ Corregido

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
            
            if not email or not nombre or not curso:
                flash('Todos los campos son requeridos', 'error')
                cursos = list(Database.get_cursos_activos_con_instructor())
                return render_template('registro_alumno.html', email=email, cursos=cursos)

            alumno_existente = Database.get_alumno_by_email(email)
            if alumno_existente:
                flash('El alumno con este email ya existe', 'error')
                return redirect(url_for('login'))

            alumno_data = {
                'email': email,
                'nombre': nombre,
                'curso': curso,
                'fecha_registro': datetime.now()
            }

            result = Database.insert_alumno(alumno_data)

            session['user'] = email
            session['role'] = 'alumno'
            session['nombre'] = nombre
            session.permanent = True

            flash(f'¡Registro exitoso! Bienvenido/a {nombre}', 'success')
            return redirect(url_for('alumno.user_dashboard'))

        except Exception as e:
            print(f"ERROR al registrar alumno: {e}")
            flash(f'Error al registrar alumno: {str(e)}', 'error')
            cursos = list(Database.get_cursos_activos_con_instructor())
            return render_template('registro_alumno.html', email=email, cursos=cursos)

    cursos = list(Database.get_cursos_activos_con_instructor())
    return render_template('registro_alumno.html', email=email, cursos=cursos)

@app.route('/dashboard')
@login_required
def dashboard():
    # Obtener email del usuario actual desde la sesión
    user_email = session.get('email')
    
    # 1. Buscar eventos donde el alumno está asignado
    eventos_query = {
        "alumnos_asignados": {
            "$elemMatch": {"email": user_email}
        }
    }
    
    eventos_cursor = db.Eventos.find(eventos_query)
    eventos_list = list(eventos_cursor)
    
    eventos_procesados = []
    
    for evento in eventos_list:
        # 2. Obtener el curso relacionado
        curso = db.Cursos.find_one({"_id": evento["curso_id"]})
        
        # 3. Determinar si el curso tiene cuestionario y evaluación
        tiene_cuestionario = False
        tiene_evaluacion = False
        cuestionario_completado = False
        evaluacion_completada = False
        
        if curso:
            # Verificar si el curso tiene cuestionario definido
            tiene_cuestionario = bool(curso.get("cuestionario") and len(curso.get("cuestionario", [])) > 0)
            
            # Verificar si el curso tiene evaluación definida
            tiene_evaluacion = bool(curso.get("evaluacion") and len(curso.get("evaluacion", [])) > 0)
            
            # 4. Verificar si el alumno ya completó el cuestionario
            if tiene_cuestionario and "cuestionarios_detalle" in evento:
                for detalle in evento["cuestionarios_detalle"]:
                    if detalle.get("email") == user_email:
                        cuestionario_completado = True
                        break
            
            # 5. Verificar si el alumno ya completó la evaluación
            if tiene_evaluacion and "evaluaciones_detalle" in evento:
                for detalle in evento["evaluaciones_detalle"]:
                    if detalle.get("email") == user_email:
                        evaluacion_completada = True
                        break
        
        # 6. Construir objeto para el template
        evento_dict = {
            "_id": str(evento["_id"]),
            "curso_id": str(evento["curso_id"]),
            "curso_nombre": evento.get("curso_nombre", "Sin nombre"),
            "fecha_evento": evento.get("fecha_evento"),
            "tiene_cuestionario": tiene_cuestionario,
            "cuestionario_completado": cuestionario_completado,
            "tiene_evaluacion": tiene_evaluacion,
            "evaluacion_completada": evaluacion_completada,
            # Para los enlaces, necesitamos tanto el evento_id como el curso_id
            "evento_id": str(evento["_id"]),
            "curso_id": str(evento["curso_id"])
        }
        
        eventos_procesados.append(evento_dict)
    
    # 7. Obtener actividades recientes del alumno
    actividades = []
    # Aquí puedes consultar las respuestas del alumno en todos los eventos
    # y ordenarlas por fecha
    
    return render_template('user/dashboard.html', 
                         eventos=eventos_procesados, 
                         actividades=actividades)

# =============================================================================
# MANEJO DE ERRORES
# =============================================================================

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template('error.html', error='Página no encontrada'), 404

@app.errorhandler(500)
def error_servidor(error):
    return render_template('error.html', error='Error interno del servidor'), 500

# =============================================================================
# INICIALIZACIÓN
# =============================================================================

# INICIALIZACIÓN
if __name__ == '__main__': 
    port=int(os.environ.get('PORT',5000))    
    app.run(debug=False, host='0.0.0.0', port=port)