import os
import re

def update_url_for_in_templates():
    templates_dir = 'templates'
    
    # Mapeo completo de rutas antiguas a nuevas basado en la salida de check_routes
    replacements = {
        # Rutas de administrador
        r"url_for\('admin_dashboard'\)": "url_for('admin.admin_dashboard')",
        r"url_for\('gestion_cursos'\)": "url_for('admin.gestion_cursos')",
        r"url_for\('gestion_instructores'\)": "url_for('admin.gestion_instructores')",
        r"url_for\('gestion_alumnos'\)": "url_for('admin.gestion_alumnos')",
        r"url_for\('agregar_alumno'\)": "url_for('admin.agregar_alumno')",
        r"url_for\('eliminar_alumno'\)": "url_for('admin.eliminar_alumno')",
        r"url_for\('agregar_instructor'\)": "url_for('admin.agregar_instructor')",
        r"url_for\('eliminar_instructor'\)": "url_for('admin.eliminar_instructor')",
        r"url_for\('asignar_instructor_evento'\)": "url_for('admin.asignar_instructor_evento')",
        r"url_for\('agregar_curso'\)": "url_for('admin.agregar_curso')",
        r"url_for\('eliminar_curso'\)": "url_for('admin.eliminar_curso')",
        r"url_for\('cargar_cuestionario_curso'\)": "url_for('admin.cargar_cuestionario_curso')",
        r"url_for\('crear_evento_curso'\)": "url_for('admin.crear_evento_curso')",
        
        # Rutas de instructor
        r"url_for\('instructor_agenda'\)": "url_for('instructor.instructor_agenda')",
        r"url_for\('instructor_alumnos_evento'\)": "url_for('instructor.instructor_alumnos_evento')",
        r"url_for\('cerrar_evento_instructor'\)": "url_for('instructor.cerrar_evento_instructor')",
        
        # Rutas de alumno
        r"url_for\('user_dashboard'\)": "url_for('alumno.user_dashboard')",
        r"url_for\('user_examenes'\)": "url_for('alumno.user_examenes')",
        r"url_for\('tomar_examen'\)": "url_for('alumno.tomar_examen')",
        r"url_for\('evaluar_examen'\)": "url_for('alumno.evaluar_examen')",
        r"url_for\('tomar_evaluacion_taller'\)": "url_for('alumno.tomar_evaluacion_taller')",
        r"url_for\('enviar_evaluacion_taller'\)": "url_for('alumno.enviar_evaluacion_taller')",
        r"url_for\('ver_evaluacion_completada'\)": "url_for('alumno.ver_evaluacion_completada')",
        r"url_for\('ver_cuestionario_completado'\)": "url_for('alumno.ver_cuestionario_completado')",
        
        # Rutas de eventos
        r"url_for\('agenda_eventos'\)": "url_for('eventos.agenda_eventos')",
        r"url_for\('alumnos_evento'\)": "url_for('eventos.alumnos_evento')",
        r"url_for\('agregar_alumno_evento'\)": "url_for('eventos.agregar_alumno_evento')",
        r"url_for\('eliminar_alumno_evento'\)": "url_for('eventos.eliminar_alumno_evento')",
        r"url_for\('editar_evento'\)": "url_for('eventos.editar_evento')",
        
        # Rutas públicas (sin cambios)
        r"url_for\('index'\)": "url_for('index')",
        r"url_for\('login'\)": "url_for('login')",
        r"url_for\('logout'\)": "url_for('logout')",
        r"url_for\('registro_alumno'\)": "url_for('registro_alumno')",
        r"url_for\('dashboard'\)": "url_for('dashboard')",
    }
    
    updated_files = 0
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                updated_content = content
                for old_pattern, new_pattern in replacements.items():
                    # Usar re.escape para patrones con paréntesis
                    old_escaped = re.escape(old_pattern)
                    updated_content = re.sub(old_escaped, new_pattern, updated_content)
                
                if updated_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    print(f"✅ Actualizado: {filepath}")
                    updated_files += 1
                else:
                    print(f"⚠️  Sin cambios: {filepath}")
    
    print(f"\n📊 Resumen: {updated_files} archivos actualizados")

if __name__ == '__main__':
    update_url_for_in_templates()