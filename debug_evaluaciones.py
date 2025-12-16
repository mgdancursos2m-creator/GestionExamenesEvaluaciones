from pymongo import MongoClient
from bson import ObjectId

MONGODB_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"

def verificar_estado():
    try:
        client = MongoClient(MONGODB_URI)
        db = client.exam_db
        
        print("=== VERIFICACIÓN DEL SISTEMA ===")
        
        # Verificar cursos
        print("\n📚 CURSOS:")
        cursos = list(db.Cursos.find())
        for curso in cursos:
            print(f"  - {curso['nombre']} (ID: {curso['_id']})")
            print(f"    Asignado: {curso.get('asignado', 'NO')}, Instructor: {curso.get('instructor_nombre', 'Ninguno')}")
        
        # Verificar exámenes
        print("\n📝 EXÁMENES:")
        examenes = list(db.Exámenes.find())
        for examen in examenes:
            print(f"  - {examen['nombre']} (Tipo: {examen.get('tipo_examen', 'regular')})")
            print(f"    Preguntas: {len(examen.get('preguntas', []))}")
            if 'preguntas' in examen:
                for i, pregunta in enumerate(examen['preguntas'][:3]):  # Mostrar primeras 3
                    print(f"      {i+1}. {pregunta.get('pregunta', 'Sin texto')}")
        
        # Verificar alumnos
        print("\n👥 ALUMNOS:")
        alumnos = list(db.Alumnos.find())
        for alumno in alumnos:
            print(f"  - {alumno['nombre']} ({alumno['email']}) - Curso: {alumno.get('curso', 'No asignado')}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_estado()