from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"

def verificar_evaluacion_taller():
    try:
        client = MongoClient(MONGODB_URI)
        db = client.exam_db
        
        print("=== VERIFICANDO EVALUACIONES DE TALLER ===")
        
        # Buscar evaluaciones de taller
        evaluaciones = list(db.Exámenes.find({"tipo_examen": "evaluacion_taller"}))
        
        if not evaluaciones:
            print("❌ No hay evaluaciones de taller creadas")
            return
        
        for eval in evaluaciones:
            print(f"\n📋 EVALUACIÓN: {eval['nombre']}")
            print(f"📚 Curso ID: {eval['curso_id']}")
            print(f"🔄 Tipo: {eval.get('tipo_examen', 'N/A')}")
            
            if 'estructura' in eval:
                print("✅ Tiene estructura específica")
                estructura = eval['estructura']
                
                print(f"📊 Escala: {estructura.get('escala', 'N/A')}")
                
                if 'secciones' in estructura:
                    secciones = estructura['secciones']
                    print(f"🏫 Preguntas Taller: {len(secciones.get('taller', []))}")
                    print(f"👨‍🏫 Preguntas Instructor: {len(secciones.get('instructor', []))}")
                    
                    # Mostrar preguntas del taller
                    print("\n📝 PREGUNTAS TALLER:")
                    for pregunta in secciones.get('taller', []):
                        print(f"   {pregunta['numero']}.- {pregunta['texto']}")
                    
                    # Mostrar preguntas del instructor
                    print("\n📝 PREGUNTAS INSTRUCTOR:")
                    for pregunta in secciones.get('instructor', []):
                        print(f"   {pregunta['numero']}.- {pregunta['texto']}")
                
                print(f"💬 Comentarios: {estructura.get('comentarios', 'N/A')}")
            else:
                print("❌ NO tiene estructura específica")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_evaluacion_taller()