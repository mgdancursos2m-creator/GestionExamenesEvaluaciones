import os
import sys
import random
from datetime import datetime
from bson import ObjectId

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
import config

# Configuración de conexión a MongoDB
client = MongoClient(config.Config.MONGODB_URI)
db = client.exam_db

def obtener_examenes_taller():
    """Obtener todos los exámenes de tipo evaluación_taller"""
    return list(db.Exámenes.find({"tipo_examen": "evaluacion_taller"}))

def obtener_alumno_por_email(email):
    """Obtener información del alumno por email"""
    return db.Alumnos.find_one({"email": email})

def generar_respuestas_aleatorias(examen):
    """Generar respuestas aleatorias para todas las preguntas"""
    resultados = {
        'informacion_general': {
            'nombre_taller': '',
            'nombre_instructor': ''
        },
        'respuestas_taller': {},
        'respuestas_instructor': {},
        'comentarios': ''
    }
    
    # Generar respuestas para la sección TALLER
    if 'estructura' in examen and 'secciones' in examen['estructura']:
        for pregunta in examen['estructura']['secciones']['taller']:
            puntaje = random.randint(3, 6)  # Valores entre 3 y 6 (más realistas)
            resultados['respuestas_taller'][pregunta['numero']] = {
                'pregunta': pregunta['texto'],
                'puntaje': puntaje
            }
    
    # Generar respuestas para la sección INSTRUCTOR
    if 'estructura' in examen and 'secciones' in examen['estructura']:
        for pregunta in examen['estructura']['secciones']['instructor']:
            puntaje = random.randint(4, 6)  # Instructores suelen tener mejores puntajes
            resultados['respuestas_instructor'][pregunta['numero']] = {
                'pregunta': pregunta['texto'],
                'puntaje': puntaje
            }
    
    return resultados

def calcular_promedios(resultados):
    """Calcular promedios basados en las respuestas"""
    puntajes_taller = [resp['puntaje'] for resp in resultados['respuestas_taller'].values()]
    puntajes_instructor = [resp['puntaje'] for resp in resultados['respuestas_instructor'].values()]
    
    promedio_taller = sum(puntajes_taller) / len(puntajes_taller) if puntajes_taller else 0
    promedio_instructor = sum(puntajes_instructor) / len(puntajes_instructor) if puntajes_instructor else 0
    promedio_general = (promedio_taller + promedio_instructor) / 2 if puntajes_taller and puntajes_instructor else 0
    
    return round(promedio_taller, 2), round(promedio_instructor, 2), round(promedio_general, 2)

def insertar_evaluacion(alumno_email, examen_id):
    """Insertar una evaluación de prueba en la base de datos"""
    try:
        # Obtener información del alumno
        alumno = obtener_alumno_por_email(alumno_email)
        if not alumno:
            print(f"❌ ERROR: No se encontró el alumno con email: {alumno_email}")
            return False
        
        # Obtener información del examen
        examen = db.Exámenes.find_one({"_id": ObjectId(examen_id)})
        if not examen:
            print(f"❌ ERROR: No se encontró el examen con ID: {examen_id}")
            return False
        
        # Obtener información del curso
        curso = db.Cursos.find_one({"_id": examen['curso_id']})
        if not curso:
            print(f"❌ ERROR: No se encontró el curso asociado al examen")
            return False
        
        print(f"📋 Información obtenida:")
        print(f"   👤 Alumno: {alumno['nombre']} ({alumno_email})")
        print(f"   📚 Curso: {curso['nombre']}")
        print(f"   🎓 Instructor: {curso.get('instructor_nombre', 'No asignado')}")
        print(f"   📝 Examen: {examen['nombre']}")
        
        # Generar respuestas aleatorias
        print("\n🎲 Generando respuestas aleatorias...")
        resultados = generar_respuestas_aleatorias(examen)
        
        # Actualizar información general
        resultados['informacion_general'] = {
            'nombre_taller': curso['nombre'],
            'nombre_instructor': curso.get('instructor_nombre', 'Instructor no asignado')
        }
        
        # Generar comentario personalizado
        resultados['comentarios'] = f"Evaluación generada automáticamente para {alumno_email}. Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}. Comentario de prueba: El taller fue muy informativo y el instructor demostró gran conocimiento del tema."
        
        # Calcular promedios
        promedio_taller, promedio_instructor, promedio_general = calcular_promedios(resultados)
        
        # Crear documento de evaluación
        evaluacion_data = {
            'alumno_email': alumno_email,
            'alumno_nombre': alumno['nombre'],
            'examen_id': examen['_id'],
            'examen_nombre': examen['nombre'],
            'curso_id': examen['curso_id'],
            'curso_nombre': curso['nombre'],
            'instructor_email': curso.get('instructor_email', 'N/A'),
            'instructor_nombre': curso.get('instructor_nombre', 'N/A'),
            'tipo_evaluacion': 'evaluacion_taller',
            'resultados': resultados,
            'promedio_taller': promedio_taller,
            'promedio_instructor': promedio_instructor,
            'promedio_general': promedio_general,
            'fecha_realizacion': datetime.now()
        }
        
        # Insertar en la base de datos
        print("\n💾 Insertando evaluación en la base de datos...")
        result = db.evaluaciones.insert_one(evaluacion_data)
        
        print(f"✅ ¡ÉXITO! Evaluación insertada correctamente")
        print(f"   📊 ID de la evaluación: {result.inserted_id}")
        print(f"   📈 Promedio general: {promedio_general}/6")
        print(f"   📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def mostrar_estadisticas():
    """Mostrar estadísticas de la colección evaluaciones"""
    try:
        total_evaluaciones = db.evaluaciones.count_documents({})
        print(f"\n📊 ESTADÍSTICAS ACTUALES:")
        print(f"   Total de evaluaciones en la base de datos: {total_evaluaciones}")
        
        if total_evaluaciones > 0:
            # Mostrar las 3 evaluaciones más recientes
            print(f"\n📋 Últimas evaluaciones:")
            evaluaciones_recientes = db.evaluaciones.find().sort("fecha_realizacion", -1).limit(3)
            for eval in evaluaciones_recientes:
                print(f"   • {eval['alumno_nombre']} - {eval['examen_nombre']} - {eval['promedio_general']}/6")
        
        return total_evaluaciones
        
    except Exception as e:
        print(f"❌ ERROR al obtener estadísticas: {e}")
        return 0

def main():
    """Función principal"""
    print("=" * 60)
    print("🎯 GENERADOR DE EVALUACIONES DE PRUEBA")
    print("=" * 60)
    
    # Verificar conexión
    try:
        client.admin.command('ping')
        print("✅ Conexión a MongoDB establecida correctamente")
    except Exception as e:
        print(f"❌ Error de conexión a MongoDB: {e}")
        return
    
    # Mostrar estadísticas actuales
    total_antes = mostrar_estadisticas()
    
    # Obtener exámenes disponibles
    print(f"\n🔍 Buscando exámenes de taller disponibles...")
    examenes = obtener_examenes_taller()
    
    if not examenes:
        print("❌ No se encontraron exámenes de tipo 'evaluacion_taller'")
        return
    
    print(f"\n📚 Exámenes de taller disponibles:")
    for i, examen in enumerate(examenes, 1):
        curso = db.Cursos.find_one({"_id": examen['curso_id']})
        curso_nombre = curso['nombre'] if curso else "Curso no encontrado"
        print(f"   {i}. {examen['nombre']} - {curso_nombre} (ID: {examen['_id']})")
    
    # Solicitar datos al usuario
    print(f"\n📝 Ingrese los datos para generar la evaluación:")
    
    # Email del alumno
    alumno_email = input("   👤 Correo del alumno: ").strip()
    if not alumno_email:
        print("❌ Debe ingresar un correo electrónico")
        return
    
    # Seleccionar examen
    try:
        seleccion = int(input(f"   📚 Seleccione el examen (1-{len(examenes)}): "))
        if seleccion < 1 or seleccion > len(examenes):
            print("❌ Selección inválida")
            return
        examen_seleccionado = examenes[seleccion - 1]
    except ValueError:
        print("❌ Debe ingresar un número válido")
        return
    
    # Confirmar
    confirmar = input(f"\n¿Generar evaluación para {alumno_email}? (s/n): ").strip().lower()
    if confirmar != 's':
        print("❌ Operación cancelada")
        return
    
    # Generar e insertar evaluación
    print(f"\n🚀 Generando evaluación...")
    éxito = insertar_evaluacion(alumno_email, str(examen_seleccionado['_id']))
    
    if éxito:
        # Mostrar estadísticas después de la inserción
        total_despues = mostrar_estadisticas()
        if total_despues > total_antes:
            print(f"\n🎉 ¡Evaluación agregada exitosamente! Se agregó 1 nueva evaluación.")
        else:
            print(f"\n⚠️  La evaluación no parece haberse agregado. Verifique la base de datos.")
    else:
        print(f"\n💥 No se pudo insertar la evaluación")

if __name__ == "__main__":
    main()
    input("\nPresione Enter para salir...")