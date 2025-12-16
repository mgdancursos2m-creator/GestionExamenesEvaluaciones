# fix_all_broken_links.py
import os
import re

def fix_all_broken_links():
    templates_dir = 'templates'
    
    # Mapeo completo basado en los enlaces rotos encontrados
    replacements = {
        # Enlaces de administrador
        r"url_for\('admin\.gestion_examenes'\)": "url_for('admin.gestion_cursos')",
        r"url_for\('admin_dashboard'\)": "url_for('admin.admin_dashboard')",
        r"url_for\('gestion_cursos'\)": "url_for('admin.gestion_cursos')",
        r"url_for\('gestion_instructores'\)": "url_for('admin.gestion_instructores')",
        r"url_for\('gestion_alumnos'\)": "url_for('admin.gestion_alumnos')",
        r"url_for\('asignar_instructor_evento'\)": "url_for('admin.asignar_instructor_evento')",
        r"url_for\('agregar_instructor'\)": "url_for('admin.agregar_instructor')",
        r"url_for\('admin_examenes'\)": "url_for('admin.gestion_cursos')",
        r"url_for\('admin_cursos'\)": "url_for('admin.gestion_cursos')",
        r"url_for\('asignar_curso_instructor'\)": "url_for('admin.asignar_instructor_evento')",
        r"url_for\('gestion_examenes'\)": "url_for('admin.gestion_cursos')",
        
        # Enlaces de usuario/alumno
        r"url_for\('user_dashboard'\)": "url_for('alumno.user_dashboard')",
        r"url_for\('user_examenes'\)": "url_for('alumno.user_examenes')",
        
        # Enlaces de instructor
        r"url_for\('instructor_agenda'\)": "url_for('instructor.instructor_agenda')",
    }
    
    updated_files = 0
    total_replacements = 0
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                updated_content = content
                file_replacements = 0
                
                for old_pattern, new_pattern in replacements.items():
                    # Contar cuántas veces aparece el patrón
                    count_before = len(re.findall(re.escape(old_pattern), updated_content))
                    if count_before > 0:
                        updated_content = re.sub(re.escape(old_pattern), new_pattern, updated_content)
                        file_replacements += count_before
                        total_replacements += count_before
                
                if updated_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    print(f"✅ Actualizado: {filepath} ({file_replacements} cambios)")
                    updated_files += 1
                else:
                    print(f"⚠️  Sin cambios: {filepath}")
    
    print(f"\n📊 RESUMEN FINAL:")
    print(f"   Archivos actualizados: {updated_files}")
    print(f"   Total de reemplazos: {total_replacements}")
    
    # Verificar si hay archivos que probablemente no se usen
    print(f"\n🔍 ARCHIVOS QUE PODRÍAN ESTAR OBSOLETOS:")
    potential_obsolete = ['templates/admin/dashboardX.html', 'templates/admin/instructores.html']
    for filepath in potential_obsolete:
        if os.path.exists(filepath):
            print(f"   {filepath} - Considera eliminar si no se usa")

if __name__ == '__main__':
    fix_all_broken_links()