from pymongo import MongoClient
from bson import ObjectId

# Configuración de conexión
MONGODB_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"

def actualizar_estructura_bd():
    try:
        client = MongoClient(MONGODB_URI)
        db = client.exam_db
        
        print("🔄 Actualizando estructura de la base de datos...")
        
        # Actualizar cursos existentes con nuevos campos
        cursos_actualizados = db.Cursos.update_many(
            {"asignado": {"$exists": False}}, 
            {"$set": {
                "asignado": False, 
                "instructor_id": None, 
                "instructor_email": None,
                "instructor_nombre": None,
                "horas_totales": 40,
                "descripcion": "Curso de programación"
            }}
        )
        print(f"✅ Cursos actualizados: {cursos_actualizados.modified_count}")
        
        # Actualizar instructores existentes con campo de cursos
        instructores_actualizados = db.Instructores.update_many(
            {"cursos": {"$exists": False}}, 
            {"$set": {"cursos": []}}
        )
        print(f"✅ Instructores actualizados: {instructores_actualizados.modified_count}")
        
        # Agregar campo descripcion a cursos si no existe
        db.Cursos.update_many(
            {"descripcion": {"$exists": False}},
            {"$set": {"descripcion": "Curso de programación"}}
        )
        
        # Verificar estado actual
        print("\n📊 ESTADO ACTUAL DE LA BASE DE DATOS:")
        
        cursos_count = db.Cursos.count_documents({})
        print(f"   📚 Total de cursos: {cursos_count}")
        
        cursos_no_asignados = db.Cursos.count_documents({"asignado": False})
        print(f"   📋 Cursos sin asignar: {cursos_no_asignados}")
        
        instructores_count = db.Instructores.count_documents({})
        print(f"   👨‍🏫 Total de instructores: {instructores_count}")
        
        client.close()
        print("\n🎉 Estructura actualizada correctamente!")
        
    except Exception as e:
        print(f"❌ Error al actualizar estructura: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    actualizar_estructura_bd()