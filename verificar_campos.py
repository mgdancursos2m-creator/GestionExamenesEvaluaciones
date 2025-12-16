from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"

def verificar_campos_examenes():
    try:
        client = MongoClient(MONGODB_URI)
        db = client.exam_db
        
        print("=== VERIFICANDO CAMPOS PARA EXÁMENES ===")
        
        # Verificar si la colección Exámenes existe y tiene documentos
        if 'Exámenes' not in db.list_collection_names():
            print("❌ La colección 'Exámenes' no existe")
            # Crear la colección si no existe
            db.Exámenes.insert_one({
                "nombre": "Examen de prueba",
                "tipo_examen": "cuestionario",
                "curso_id": None,
                "preguntas": [],
                "fecha_creacion": None
            })
            print("✅ Colección 'Exámenes' creada")
            db.Exámenes.delete_many({"nombre": "Examen de prueba"})
        else:
            print("✅ Colección 'Exámenes' existe")
        
        # Verificar campos en cursos para exámenes
        print("\n📚 VERIFICANDO CURSOS:")
        cursos = list(db.Cursos.find().limit(2))
        for i, curso in enumerate(cursos):
            print(f"Curso {i+1}: {curso.get('nombre', 'Sin nombre')}")
            campos_requeridos = ['asignado', 'estatus', 'instructor_id', 'instructor_nombre']
            for campo in campos_requeridos:
                if campo in curso:
                    valor = curso[campo]
                    if valor:
                        print(f"  ✅ {campo}: {valor}")
                    else:
                        print(f"  ⚠️  {campo}: {valor} (vacío)")
                else:
                    print(f"  ❌ {campo}: NO EXISTE")
        
        # Verificar cursos activos con instructor
        cursos_activos_con_instructor = list(db.Cursos.find({
            "estatus": "activo", 
            "asignado": True,
            "instructor_id": {"$ne": None}
        }))
        
        print(f"\n🎯 CURSOS ACTIVOS CON INSTRUCTOR: {len(cursos_activos_con_instructor)}")
        for curso in cursos_activos_con_instructor:
            print(f"  - {curso['nombre']} - {curso.get('instructor_nombre', 'Sin instructor')}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_campos_examenes()