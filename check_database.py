from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"

def verificar_estructura():
    try:
        client = MongoClient(MONGODB_URI)
        db = client.exam_db
        
        print("=== VERIFICANDO ESTRUCTURA DE LA BASE DE DATOS ===")
        
        # Verificar colección Cursos
        print("\n📚 COLECCIÓN CURSOS:")
        cursos = list(db.Cursos.find().limit(1))
        if cursos:
            curso = cursos[0]
            print("Campos encontrados:")
            for campo in curso.keys():
                print(f"  ✅ {campo}")
            
            # Verificar campos requeridos
            campos_requeridos = ['asignado', 'estatus', 'horas_totales']
            for campo in campos_requeridos:
                if campo in curso:
                    print(f"  ✅ Campo '{campo}': {curso[campo]}")
                else:
                    print(f"  ❌ Falta campo: {campo}")
        else:
            print("  No hay cursos en la base de datos")
        
        # Verificar colección Instructores
        print("\n👨‍🏫 COLECCIÓN INSTRUCTORES:")
        instructores = list(db.Instructores.find().limit(1))
        if instructores:
            instructor = instructores[0]
            print("Campos encontrados:")
            for campo in instructor.keys():
                print(f"  ✅ {campo}")
            
            if 'cursos' in instructor:
                print(f"  ✅ Campo 'cursos': {instructor['cursos']}")
            else:
                print("  ❌ Falta campo: cursos")
        else:
            print("  No hay instructores en la base de datos")
        
        # Verificar cursos no asignados
        print("\n📋 CURSOS NO ASIGNADOS:")
        cursos_no_asignados = list(db.Cursos.find({"asignado": False, "estatus": "activo"}))
        print(f"  Total: {len(cursos_no_asignados)} cursos")
        for curso in cursos_no_asignados:
            print(f"  - {curso['nombre']}")
        
        client.close()
        print("\n🎉 Verificación completada!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_estructura()