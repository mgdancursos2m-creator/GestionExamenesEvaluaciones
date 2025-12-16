from pymongo import MongoClient
from datetime import datetime

# Configuración de conexión
MONGODB_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"

def inicializar_base_datos():
    try:
        client = MongoClient(MONGODB_URI)
        db = client.exam_db
        
        print("=== INICIALIZACIÓN DE BASE DE DATOS ===")
        
        # Crear colección Instructores si no existe
        if 'Instructores' not in db.list_collection_names():
            print("📝 Creando colección 'Instructores'...")
            instructores_data = [
                {
                    'email': 'instructor1@taller.com',
                    'nombre': 'Profesor Juan Pérez',
                    'especialidad': 'Programación Python',
                    'fecha_registro': datetime.now()
                },
                {
                    'email': 'instructor2@taller.com',
                    'nombre': 'Ingeniera María García',
                    'especialidad': 'Base de Datos',
                    'fecha_registro': datetime.now()
                }
            ]
            db.Instructores.insert_many(instructores_data)
            print("✅ Colección 'Instructores' creada con datos de ejemplo")
        
        # Crear colección Exámenes si no existe
        if 'Exámenes' not in db.list_collection_names():
            print("📝 Creando colección 'Exámenes'...")
            # Primero necesitamos un curso
            if db.Cursos.count_documents({}) == 0:
                curso_data = {
                    'nombre': 'Python Básico',
                    'instructor_email': 'instructor1@taller.com',
                    'fecha_inicio': datetime(2024, 1, 15),
                    'dias_duracion': 30,
                    'estatus': 'activo',
                    'fecha_creacion': datetime.now()
                }
                curso_result = db.Cursos.insert_one(curso_data)
                curso_id = curso_result.inserted_id
            else:
                curso = db.Cursos.find_one()
                curso_id = curso['_id']
            
            examen_data = {
                'curso_id': curso_id,
                'nombre': 'Examen Final Python Básico',
                'descripcion': 'Evaluación de conceptos básicos de Python',
                'preguntas': [
                    {
                        'pregunta': '¿Qué es Python?',
                        'opciones': ['Un lenguaje de programación', 'Una serpiente', 'Un tipo de café', 'Un país'],
                        'respuesta_correcta': 'Un lenguaje de programación'
                    },
                    {
                        'pregunta': '¿Cómo se define una función en Python?',
                        'opciones': ['function miFuncion()', 'def miFuncion():', 'func miFuncion()', 'define miFuncion()'],
                        'respuesta_correcta': 'def miFuncion():'
                    }
                ],
                'fecha_creacion': datetime.now()
            }
            db.Exámenes.insert_one(examen_data)
            print("✅ Colección 'Exámenes' creada con datos de ejemplo")
        
        # Agregar algunos alumnos de ejemplo si no existen
        if db.Alumnos.count_documents({}) == 0:
            print("📝 Agregando alumnos de ejemplo...")
            alumnos_data = [
                {
                    'email': 'alumno1@taller.com',
                    'nombre': 'Carlos Rodríguez',
                    'curso': 'Python Básico',
                    'fecha_registro': datetime.now()
                },
                {
                    'email': 'alumno2@taller.com',
                    'nombre': 'Ana Martínez',
                    'curso': 'Python Básico',
                    'fecha_registro': datetime.now()
                }
            ]
            db.Alumnos.insert_many(alumnos_data)
            print("✅ Alumnos de ejemplo agregados")
        
        # Verificar estado final
        print("\n📊 ESTADO FINAL DE LA BASE DE DATOS:")
        collections = db.list_collection_names()
        for collection in collections:
            count = db[collection].count_documents({})
            print(f"   ✅ {collection}: {count} documentos")
        
        print("\n🎉 ¡Base de datos inicializada correctamente!")
        print("📧 Credenciales para prueba:")
        print("   Admin: usuario 'admin', contraseña 'nimda'")
        print("   Alumno: 'alumno1@taller.com' (sin contraseña)")
        print("   Instructor: 'instructor1@taller.com' (sin contraseña)")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")

if __name__ == "__main__":
    inicializar_base_datos()