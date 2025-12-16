import os
import re

def fix_final_issues():
    templates_dir = 'templates'
    
    # Mapeo de problemas específicos encontrados
    replacements = {
        # En templates/admin/alumnos.html
        r"url_for\('admin_dashboard'\)": "url_for('admin.admin_dashboard')",
        
        # En templates/admin/gestion_instructores.html
        r"url_for\('asignar_instructor_evento'\)": "url_for('admin.asignar_instructor_evento')",
        
        # En templates/user/dashboard_instructor.html
        r"url_for\('instructor_agenda'\)": "url_for('instructor.instructor_agenda')",
        
        # En templates/user/dashboard.html
        r"url_for\('user_examenes'\)": "url_for('alumno.user_examenes')",
        
        # En templates/user/tomar_evaluacion_taller.html
        r"url_for\('user_examenes'\)": "url_for('alumno.user_examenes')",
        
        # En templates/user/tomar_examen.html
        r"url_for\('user_examenes'\)": "url_for('alumno.user_examenes')",
        
        # En templates/user/ver_cuestionario.html
        r"url_for\('user_dashboard'\)": "url_for('alumno.user_dashboard')",
        
        # En templates/user/ver_evaluacion.html
        r"url_for\('user_dashboard'\)": "url_for('alumno.user_dashboard')",
    }
    
    files_to_fix = [
        'templates/admin/alumnos.html',
        'templates/admin/gestion_instructores.html',
        'templates/user/dashboard_instructor.html',
        'templates/user/dashboard.html',
        'templates/user/tomar_evaluacion_taller.html',
        'templates/user/tomar_examen.html',
        'templates/user/ver_cuestionario.html',
        'templates/user/ver_evaluacion.html'
    ]
    
    updated_files = 0
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            updated_content = content
            file_replacements = 0
            
            for old_pattern, new_pattern in replacements.items():
                count_before = len(re.findall(re.escape(old_pattern), updated_content))
                if count_before > 0:
                    updated_content = re.sub(re.escape(old_pattern), new_pattern, updated_content)
                    file_replacements += count_before
            
            if updated_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"✅ Actualizado: {filepath} ({file_replacements} cambios)")
                updated_files += 1
            else:
                print(f"⚠️  Sin cambios: {filepath}")
        else:
            print(f"❌ No encontrado: {filepath}")
    
    print(f"\n📊 RESUMEN: {updated_files} archivos actualizados")

if __name__ == '__main__':
    fix_final_issues()