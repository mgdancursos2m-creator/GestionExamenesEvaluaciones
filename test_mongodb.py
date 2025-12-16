from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import sys

def test_mongodb_connection():
    # Configuración de conexión
    username = "T4ll3r_HQ"
    password = "T4ll3r_HQ"
    cluster_url = "cluster0.7a1upj8.mongodb.net"
    database_name = "exam_db"
    
    # URI de conexión
    MONGODB_URI = f"mongodb+srv://{username}:{password}@{cluster_url}/{database_name}?retryWrites=true&w=majority&appName=Cluster0"
    
    print("=== PRUEBA DE CONEXIÓN MONGODB ===")
    print(f"Usuario: {username}")
    print(f"Cluster: {cluster_url}")
    print(f"Base de datos: {database_name}")
    print("=" * 40)
    
    try:
        # Intentar conexión
        print("🔄 Conectando a MongoDB Atlas...")
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        
        # Verificar conexión
        print("✅ Conexión establecida exitosamente!")
        
        # Obtener información del servidor
        server_info = client.server_info()
        print(f"📊 Versión de MongoDB: {server_info.get('version', 'N/A')}")
        
        # Listar bases de datos
        print("\n🗃️ Bases de datos disponibles:")
        databases = client.list_database_names()
        for db in databases:
            print(f"   - {db}")
        
        # Acceder a la base de datos exam_db
        db = client[database_name]
        print(f"\n📁 Accediendo a la base de datos: {database_name}")
        
        # Listar colecciones
        print("\n📂 Colecciones en exam_db:")
        collections = db.list_collection_names()
        for collection in collections:
            print(f"   - {collection}")
            
            # Mostrar algunos documentos de cada colección
            try:
                docs = list(db[collection].find().limit(2))
                print(f"     Documentos de muestra: {len(docs)}")
                for doc in docs:
                    # Mostrar información básica del documento
                    doc_id = str(doc.get('_id', ''))[:8] + "..." if doc.get('_id') else 'N/A'
                    if 'email' in doc:
                        print(f"       📧 {doc.get('email')} - {doc.get('nombre', 'N/A')}")
                    elif 'nombre' in doc:
                        print(f"       📝 {doc.get('nombre', 'N/A')}")
            except Exception as e:
                print(f"     ❌ Error al leer documentos: {e}")
        
        # Probar operaciones CRUD básicas
        print("\n🧪 Probando operaciones básicas...")
        
        # Probar la colección Alumnos
        alumnos_collection = db['Alumnos']
        alumnos_count = alumnos_collection.count_documents({})
        print(f"   👥 Total de alumnos: {alumnos_count}")
        
        # Probar la colección Cursos
        cursos_collection = db['Cursos']
        cursos_count = cursos_collection.count_documents({})
        print(f"   📚 Total de cursos: {cursos_count}")
        
        # Probar la colección Instructores
        instructores_collection = db['Instructores']
        instructores_count = instructores_collection.count_documents({})
        print(f"   👨‍🏫 Total de instructores: {instructores_count}")
        
        # Probar insertar un documento de prueba (opcional)
        test_doc = {
            "test": "conexion_exitosa",
            "timestamp": "2024",
            "aplicacion": "sistema_examenes"
        }
        
        # Insertar en una colección temporal
        test_collection = db['test_connection']
        result = test_collection.insert_one(test_doc)
        print(f"   ✅ Documento de prueba insertado: {result.inserted_id}")
        
        # Limpiar documento de prueba
        test_collection.delete_one({"_id": result.inserted_id})
        print("   🧹 Documento de prueba eliminado")
        
        print("\n🎉 ¡Todas las pruebas completadas exitosamente!")
        
        # Cerrar conexión
        client.close()
        print("🔌 Conexión cerrada correctamente")
        
        return True
        
    except ServerSelectionTimeoutError as e:
        print(f"❌ Error de tiempo de espera: {e}")
        print("   Posibles causas:")
        print("   - La contraseña es incorrecta")
        print("   - El usuario no existe")
        print("   - Problemas de red/firewall")
        print("   - La IP no está en la whitelist de MongoDB Atlas")
        return False
        
    except ConnectionFailure as e:
        print(f"❌ Error de conexión: {e}")
        print("   Verifica:")
        print("   - Tu conexión a internet")
        print("   - La URI de conexión")
        print("   - Las credenciales de acceso")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
        return False

def test_specific_collections():
    """Prueba específica para las colecciones que necesitamos"""
    print("\n" + "="*50)
    print("PRUEBA ESPECÍFICA DE COLECCIONES REQUERIDAS")
    print("="*50)
    
    username = "T4ll3r_HQ"
    password = "T4ll3r_HQ"
    MONGODB_URI = f"mongodb+srv://{username}:{password}@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"
    
    try:
        client = MongoClient(MONGODB_URI)
        db = client['exam_db']
        
        # Lista de colecciones requeridas
        required_collections = ['Alumnos', 'Cursos', 'Exámenes', 'evaluaciones', 'Instructores']
        
        print("\n🔍 Verificando colecciones requeridas:")
        existing_collections = db.list_collection_names()
        
        for collection in required_collections:
            if collection in existing_collections:
                count = db[collection].count_documents({})
                print(f"   ✅ {collection}: {count} documentos")
                
                # Mostrar estructura de un documento de ejemplo
                sample_doc = db[collection].find_one()
                if sample_doc:
                    print(f"      Estructura: {list(sample_doc.keys())}")
            else:
                print(f"   ❌ {collection}: NO EXISTE")
                
        client.close()
        
    except Exception as e:
        print(f"❌ Error en prueba específica: {e}")

if __name__ == "__main__":
    # Ejecutar prueba principal
    success = test_mongodb_connection()
    
    # Ejecutar prueba específica de colecciones
    test_specific_collections()
    
    print("\n" + "="*50)
    if success:
        print("🎊 ¡LA CONEXIÓN ESTÁ LISTA PARA USARSE!")
        print("Puedes proceder con la aplicación Flask")
    else:
        print("💡 SOLUCIÓN DE PROBLEMAS:")
        print("1. Verifica tu contraseña en MongoDB Atlas")
        print("2. Asegúrate de que tu IP esté en la whitelist")
        print("3. Verifica que el cluster esté activo")
        print("4. Revisa que el usuario tenga los permisos correctos")
    
    print("="*50)