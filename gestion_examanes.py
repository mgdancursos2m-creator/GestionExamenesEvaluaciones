@app.route('/admin/examenes')
@login_required(role='admin')
def gestion_examenes():
    try:
        cursos = list(Database.get_cursos_activos_con_instructor())
        
        # Obtener todos los exámenes y procesarlos
        todos_examenes = list(db.Exámenes.find())
        examenes_procesados = []
        
        for examen in todos_examenes:
            # Obtener información del curso para cada examen
            curso = Database.get_curso_by_id(str(examen['curso_id']))
            
            examen_procesado = {
                '_id': examen['_id'],
                'nombre': examen['nombre'],
                'tipo_examen': examen.get('tipo_examen', 'regular'),
                'curso_nombre': curso['nombre'] if curso else 'Curso no encontrado',
                'instructor_nombre': curso['instructor_nombre'] if curso else 'N/A',
                'fecha_creacion': examen.get('fecha_creacion', datetime.now()),
                'descripcion': examen.get('descripcion', '')
            }
            
            # Calcular número de preguntas
            if examen.get('tipo_examen') == 'evaluacion_taller' and examen.get('estructura'):
                estructura = examen['estructura']
                total_preguntas = 0
                if 'secciones' in estructura:
                    if 'taller' in estructura['secciones']:
                        total_preguntas += len(estructura['secciones']['taller'])
                    if 'instructor' in estructura['secciones']:
                        total_preguntas += len(estructura['secciones']['instructor'])
                    total_preguntas += 1  # Sección de comentarios
                examen_procesado['preguntas_count'] = total_preguntas
            else:
                examen_procesado['preguntas_count'] = len(examen.get('preguntas', []))
            
            examenes_procesados.append(examen_procesado)
        
        return render_template('admin/examenes.html', examenes=examenes_procesados, cursos=cursos)
    
    except Exception as e:
        print(f"ERROR en gestión de exámenes: {e}")
        flash(f'Error al cargar los exámenes: {str(e)}', 'error')
        # Asegurémonos de pasar las variables necesarias al template incluso en caso de error
        return render_template('admin/examenes.html', examenes=[], cursos=[])