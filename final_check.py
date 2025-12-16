# final_check.py
from app import app

def final_check():
    print("🔍 VERIFICACIÓN FINAL DE ENDPOINTS CRÍTICOS:")
    
    critical_endpoints = {
        'admin.admin_dashboard': 'Dashboard Admin',
        'admin.gestion_cursos': 'Gestión Cursos', 
        'admin.gestion_instructores': 'Gestión Instructores',
        'admin.gestion_alumnos': 'Gestión Alumnos',
        'admin.asignar_instructor_evento': 'Asignar Instructor',
        'eventos.agenda_eventos': 'Agenda Eventos',
        'alumno.user_dashboard': 'Dashboard Alumno',
        'alumno.user_examenes': 'Exámenes Alumno',
        'instructor.user_dashboard': 'Dashboard Instructor',
        'instructor.instructor_agenda': 'Agenda Instructor'
    }
    
    all_ok = True
    
    for endpoint, description in critical_endpoints.items():
        try:
            with app.test_request_context():
                url = app.url_map.bind('').build(endpoint)
                print(f"✅ {description:25} -> {endpoint:45} ✓")
        except Exception as e:
            print(f"❌ {description:25} -> {endpoint:45} ✗ ERROR: {e}")
            all_ok = False
    
    if all_ok:
        print("\n🎉 ¡TODOS LOS ENDPOINTS CRÍTICOS FUNCIONAN CORRECTAMENTE!")
    else:
        print("\n⚠️  Hay endpoints que necesitan atención")
    
    return all_ok

if __name__ == '__main__':
    final_check()
