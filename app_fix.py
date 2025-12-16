@app.route('/admin/examenes')
@login_required(role='admin')
def gestion_examenes():
    try:
        # Obtener cursos activos con instructor
        cursos = list(db.Cursos.find({
            "estatus": "activo", 
            "asignado": True,
            "instructor_id": {"$ne": None}
        }))
        
        # Obtener exámenes de forma simple
        examenes = list(db.Exámenes.find())
        examenes_procesados = []
        
        for examen in examenes:
            # Información básica del examen
            examenes_procesados.append({
                '_id': examen['_id'],
                'nombre': examen.get('nombre', 'Sin nombre'),
                'tipo_examen': examen.get('tipo_examen', 'regular'),
                'curso_nombre': 'Curso',  # Placeholder
                'instructor_nombre': 'Instructor',  # Placeholder
                'preguntas_count': len(examen.get('preguntas', [])),
                'fecha_creacion': examen.get('fecha_creacion', datetime.now())
            })
        
        return render_template('admin/examenes_simple.html', examenes=examenes_procesados, cursos=cursos)
    
    except Exception as e:
        print(f"ERROR: {e}")
        return render_template('admin/examenes_simple.html', examenes=[], cursos=[])