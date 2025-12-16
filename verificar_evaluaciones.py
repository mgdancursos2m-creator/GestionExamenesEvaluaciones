from pymongo import MongoClient
import config

def verificar_estado():
    client = MongoClient(config.Config.MONGODB_URI)
    db = client.exam_db
    
    print("=" * 50)
    print("🔍 VERIFICACIÓN DE ESTADO - EVALUACIONES")
    print("=" * 50)
    
    # Verificar colección
    collections = db.list_collection_names()
    print(f"📚 Colecciones en la base de datos: {collections}")
    
    if 'evaluaciones' in collections:
        count = db.evaluaciones.count_documents({})
        print(f"📊 Total de evaluaciones: {count}")
        
        if count > 0:
            print(f"\n📋 Últimas evaluaciones:")
            evaluaciones = db.evaluaciones.find().sort("_id", -1).limit(3)
            for i, eval in enumerate(evaluaciones, 1):
                print(f"  {i}. {eval.get('alumno_nombre')} - {eval.get('examen_nombre')} - {eval.get('promedio_general', 'N/A')}/6")
    else:
        print("❌ La colección 'evaluaciones' NO existe")
    
    # Verificar exámenes de taller
    examenes_taller = list(db.Exámenes.find({"tipo_examen": "evaluacion_taller"}))
    print(f"\n🎯 Exámenes de taller encontrados: {len(examenes_taller)}")
    for examen in examenes_taller:
        print(f"  - {examen.get('nombre')} (ID: {examen.get('_id')})")
    
    print("=" * 50)

if __name__ == "__main__":
    verificar_estado()