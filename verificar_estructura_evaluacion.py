from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"

def verificar_evaluacion():
    client = MongoClient(MONGODB_URI)
    db = client.exam_db
    
    evaluaciones = list(db.Exámenes.find({"tipo_examen": "evaluacion_taller"}))
    
    for eval in evaluaciones:
        print(f"Evaluación: {eval['nombre']}")
        print(f"Tiene estructura: {'estructura' in eval}")
        if 'estructura' in eval:
            estructura = eval['estructura']
            print(f" - Secciones: {list(estructura['secciones'].keys())}")
            print(f" - Preguntas taller: {len(estructura['secciones']['taller'])}")
            print(f" - Preguntas instructor: {len(estructura['secciones']['instructor'])}")
            print(f" - Comentarios: {estructura['comentarios']}")
        print("---")
    
    client.close()

verificar_evaluacion()