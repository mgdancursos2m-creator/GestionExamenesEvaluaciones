# verificar_metodos_database.py
from models import Database

def verificar_metodos():
    print("🔍 Verificando métodos de Database...")
    
    metodos_requeridos = [
        'get_cursos_activos',
        'get_instructores', 
        'get_examenes_by_curso',  # ¡Este es el que faltaba!
        'get_examen_by_id',
        'get_curso_by_id',
        'insert_evaluacion',
        'get_evaluaciones_by_alumno'
    ]
    
    for metodo in metodos_requeridos:
        if hasattr(Database, metodo):
            print(f"✅ {metodo} - EXISTE")
        else:
            print(f"❌ {metodo} - NO EXISTE")
    
    # Probar métodos críticos
    try:
        cursos = list(Database.get_cursos_activos())
        print(f"✅ get_cursos_activos() - FUNCIONA (encontró {len(cursos)} cursos)")
    except Exception as e:
        print(f"❌ get_cursos_activos() - ERROR: {e}")
    
    try:
        instructores = list(Database.get_instructores())
        print(f"✅ get_instructores() - FUNCIONA (encontró {len(instructores)} instructores)")
    except Exception as e:
        print(f"❌ get_instructores() - ERROR: {e}")

if __name__ == "__main__":
    verificar_metodos()