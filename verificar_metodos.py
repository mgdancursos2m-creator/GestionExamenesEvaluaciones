from pymongo import MongoClient
from bson import ObjectId
import sys
import os

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Database

def verificar_metodos():
    print("=== VERIFICANDO MÉTODOS DE DATABASE ===")
    
    metodos_requeridos = [
        'get_cursos_activos_con_instructor',
        'get_examenes_completos', 
        'get_examen_by_curso_and_tipo',
        'insert_examen',
        'get_curso_by_id'
    ]
    
    for metodo in metodos_requeridos:
        if hasattr(Database, metodo):
            print(f"✅ {metodo}")
        else:
            print(f"❌ {metodo} - FALTANTE")
    
    print("\n=== VERIFICANDO COLECCIONES ===")
    try:
        client = MongoClient("mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0")
        db = client.exam_db
        
        colecciones = db.list_collection_names()
        colecciones_requeridas = ['Alumnos', 'Cursos', 'Exámenes', 'evaluaciones', 'Instructores']
        
        for coleccion in colecciones_requeridas:
            if coleccion in colecciones:
                count = db[coleccion].count_documents({})
                print(f"✅ {coleccion}: {count} documentos")
            else:
                print(f"❌ {coleccion}: NO EXISTE")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    verificar_metodos()