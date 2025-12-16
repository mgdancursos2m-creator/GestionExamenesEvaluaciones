# verificar_conteo.py
from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"

def verificar_conteo_preguntas():
    try:
        client = MongoClient(MONGODB_URI)
        db = client.exam_db
        
        evaluaciones = list(db.Exámenes.find({"tipo_examen": "evaluacion_taller"}))
        
        for eval in evaluaciones:
            print(f"Evaluación: {eval['nombre']}")
            print(f"Preguntas en array 'preguntas': {len(eval.get('preguntas', []))}")
            print(f"Estructura específica: {eval.get('formato_especifico', False)}")
            print("---")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verificar_conteo_preguntas()