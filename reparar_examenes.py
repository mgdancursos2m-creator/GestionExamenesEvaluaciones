from pymongo import MongoClient
from bson import ObjectId

MONGODB_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"

def reparar_evaluaciones_existentes():
    try:
        client = MongoClient(MONGODB_URI)
        db = client.exam_db
        
        print("🔧 REPARANDO EVALUACIONES EXISTENTES...")
        
        # Buscar todas las evaluaciones de taller
        evaluaciones = list(db.Exámenes.find({"tipo_examen": "evaluacion_taller"}))
        
        for evaluacion in evaluaciones:
            print(f"Procesando: {evaluacion['nombre']}")
            
            if 'estructura' in evaluacion and 'preguntas' not in evaluacion:
                estructura = evaluacion['estructura']
                preguntas_estandar = []
                
                # Agregar preguntas del taller
                if 'taller' in estructura['secciones']:
                    for pregunta in estructura['secciones']['taller']:
                        preguntas_estandar.append({
                            'tipo': 'escala',
                            'seccion': 'taller',
                            'numero': pregunta['numero'],
                            'pregunta': pregunta['texto'],
                            'opciones': ['1', '2', '3', '4', '5', '6']
                        })
                
                # Agregar preguntas del instructor
                if 'instructor' in estructura['secciones']:
                    for pregunta in estructura['secciones']['instructor']:
                        preguntas_estandar.append({
                            'tipo': 'escala',
                            'seccion': 'instructor',
                            'numero': pregunta['numero'],
                            'pregunta': pregunta['texto'],
                            'opciones': ['1', '2', '3', '4', '5', '6']
                        })
                
                # Agregar pregunta de comentarios
                if 'comentarios' in estructura:
                    preguntas_estandar.append({
                        'tipo': 'texto_largo',
                        'seccion': 'comentarios',
                        'numero': '',
                        'pregunta': estructura['comentarios']
                    })
                
                # Actualizar la evaluación
                db.Exámenes.update_one(
                    {'_id': evaluacion['_id']},
                    {'$set': {'preguntas': preguntas_estandar}}
                )
                
                print(f"✅ Reparada: {evaluacion['nombre']} - {len(preguntas_estandar)} preguntas agregadas")
        
        print("🎉 Reparación completada!")
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reparar_evaluaciones_existentes()