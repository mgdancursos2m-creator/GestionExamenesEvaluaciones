#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para actualizar y recalcular métricas de cuestionarios en la colección Eventos
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import sys

# Configuración de conexión a MongoDB
MONGO_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "exam_db"

def connect_to_mongodb():
    """Conecta a MongoDB y retorna la colección Eventos"""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        return db.Eventos
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        sys.exit(1)

def recalcular_metricas_evento(evento_id):
    """Recalcula todas las métricas de un evento específico"""
    
    # Convertir string a ObjectId
    if isinstance(evento_id, str):
        evento_id = ObjectId(evento_id)
    
    eventos_collection = connect_to_mongodb()
    
    # Obtener el evento
    evento = eventos_collection.find_one({"_id": evento_id})
    if not evento:
        print(f"Error: Evento con ID {evento_id} no encontrado")
        return None
    
    print(f"Recalculando métricas para evento: {evento.get('curso_nombre')}")
    
    # 1. Calcular total de alumnos
    alumnos_asignados = evento.get('alumnos_asignados', [])
    total_alumnos = len(alumnos_asignados)
    print(f"Total de alumnos: {total_alumnos}")
    
    # 2. Calcular métricas de cuestionarios
    cuestionarios_detalle = evento.get('cuestionarios_detalle', [])
    total_cuestionarios = len(cuestionarios_detalle)
    
    if total_cuestionarios > 0:
        # Calcular promedio de cuestionarios
        suma_calificaciones = sum(q.get('calificación', 0) for q in cuestionarios_detalle)
        promedio_cuestionarios = round(suma_calificaciones / total_cuestionarios, 2)
        
        print(f"Cuestionarios contestados: {total_cuestionarios}")
        print(f"Suma de calificaciones: {suma_calificaciones}")
        print(f"Promedio de cuestionarios: {promedio_cuestionarios}")
        
        # Actualizar cada cuestionario con datos más detallados
        for i, cuestionario in enumerate(cuestionarios_detalle):
            # Calcular porcentaje de aciertos
            respuestas_correctas = cuestionario.get('respuestas_correctas', 0)
            total_preguntas = cuestionario.get('total_preguntas', 0)
            
            if total_preguntas > 0:
                porcentaje_aciertos = round((respuestas_correctas / total_preguntas) * 100, 2)
                cuestionario['calificacion_porcentaje'] = porcentaje_aciertos
                
                # Clasificar resultado
                if porcentaje_aciertos >= 90:
                    cuestionario['nivel_desempeno'] = 'Excelente'
                elif porcentaje_aciertos >= 80:
                    cuestionario['nivel_desempeno'] = 'Muy Bien'
                elif porcentaje_aciertos >= 70:
                    cuestionario['nivel_desempeno'] = 'Bien'
                elif porcentaje_aciertos >= 60:
                    cuestionario['nivel_desempeno'] = 'Regular'
                else:
                    cuestionario['nivel_desempeno'] = 'Necesita mejorar'
                    
                cuestionario['fecha_actualizacion'] = datetime.now()
    else:
        promedio_cuestionarios = 0
        print("No hay cuestionarios contestados")
    
    # 3. Calcular métricas de evaluaciones
    evaluaciones_detalle = evento.get('evaluaciones_detalle', [])
    total_evaluaciones = len(evaluaciones_detalle)
    
    if total_evaluaciones > 0:
        suma_puntuaciones = sum(e.get('puntuacion_promedio', 0) for e in evaluaciones_detalle)
        promedio_evaluaciones = round(suma_puntuaciones / total_evaluaciones, 2)
        
        print(f"Evaluaciones contestadas: {total_evaluaciones}")
        print(f"Promedio de evaluaciones: {promedio_evaluaciones}")
    else:
        promedio_evaluaciones = 0
        print("No hay evaluaciones contestadas")
    
    # 4. Preparar los datos de actualización
    update_data = {
        'total_alumnos': total_alumnos,
        'cuestionarios_contestados': total_cuestionarios,
        'promedio_cuestionarios': promedio_cuestionarios,
        'evaluaciones_contestadas': total_evaluaciones,
        'promedio_evaluaciones': promedio_evaluaciones,
        'cuestionarios_detalle': cuestionarios_detalle,  # Con los nuevos campos
        'fecha_actualizacion': datetime.now()
    }
    
    # 5. Actualizar el evento en la base de datos
    try:
        result = eventos_collection.update_one(
            {"_id": evento_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"✓ Evento actualizado exitosamente")
            print(f"  - Modificado: {result.modified_count} documento(s)")
            print(f"  - Coincidencias: {result.matched_count}")
            return True
        else:
            print("⚠️ No se modificó ningún documento (posiblemente ya está actualizado)")
            return False
            
    except Exception as e:
        print(f"✗ Error actualizando el evento: {e}")
        return False

def generar_estadisticas_detalladas(evento_id):
    """Genera estadísticas detalladas del evento"""
    
    if isinstance(evento_id, str):
        evento_id = ObjectId(evento_id)
    
    eventos_collection = connect_to_mongodb()
    evento = eventos_collection.find_one({"_id": evento_id})
    
    if not evento:
        return None
    
    print("\n" + "="*60)
    print("ESTADÍSTICAS DETALLADAS DEL EVENTO")
    print("="*60)
    
    # Información básica
    print(f"\n📊 CURSO: {evento.get('curso_nombre')}")
    print(f"📅 Fecha del evento: {evento.get('fecha_evento').strftime('%d/%m/%Y')}")
    print(f"👨‍🏫 Instructor: {evento.get('instructor_nombre', 'No asignado')}")
    print(f"📊 Estatus: {evento.get('estatus', 'No definido')}")
    
    # Estadísticas de alumnos
    print(f"\n👥 ALUMNOS:")
    print(f"  • Total inscritos: {evento.get('total_alumnos', 0)}")
    
    for i, alumno in enumerate(evento.get('alumnos_asignados', []), 1):
        print(f"  {i}. {alumno.get('nombre')} ({alumno.get('email')})")
    
    # Estadísticas de cuestionarios
    cuestionarios = evento.get('cuestionarios_detalle', [])
    print(f"\n📝 CUESTIONARIOS:")
    print(f"  • Total contestados: {len(cuestionarios)}")
    print(f"  • Promedio general: {evento.get('promedio_cuestionarios', 0)}%")
    
    for i, cuestionario in enumerate(cuestionarios, 1):
        print(f"\n  📋 Cuestionario {i}:")
        print(f"    👤 Alumno: {cuestionario.get('nombre')}")
        print(f"    📧 Email: {cuestionario.get('email')}")
        print(f"    📅 Fecha: {cuestionario.get('fecha_respuesta').strftime('%d/%m/%Y %H:%M')}")
        print(f"    🎯 Calificación: {cuestionario.get('calificacion', 0)}%")
        print(f"    ✅ Correctas: {cuestionario.get('respuestas_correctas', 0)}/{cuestionario.get('total_preguntas', 0)}")
        
        # Calcular estadísticas por pregunta
        resultados = cuestionario.get('resultados_detalle', [])
        if resultados:
            correctas = sum(1 for r in resultados if r.get('es_correcta', False))
            incorrectas = len(resultados) - correctas
            print(f"    📊 Desglose: {correctas} correctas, {incorrectas} incorrectas")
            
            # Mostrar preguntas incorrectas
            incorrectas_lista = [r for r in resultados if not r.get('es_correcta', False)]
            if incorrectas_lista:
                print(f"    ❌ Preguntas incorrectas:")
                for r in incorrectas_lista:
                    print(f"      - {r.get('pregunta', 'Sin pregunta')[:50]}...")
    
    # Estadísticas de evaluaciones
    evaluaciones = evento.get('evaluaciones_detalle', [])
    print(f"\n⭐ EVALUACIONES:")
    print(f"  • Total contestadas: {len(evaluaciones)}")
    print(f"  • Promedio general: {evento.get('promedio_evaluaciones', 0):.1f}/6")
    
    return evento

def actualizar_todos_los_eventos():
    """Recalcula métricas para todos los eventos"""
    
    eventos_collection = connect_to_mongodb()
    eventos = eventos_collection.find({})
    total_eventos = eventos_collection.count_documents({})
    
    print(f"Recalculando métricas para {total_eventos} eventos...")
    print("-" * 60)
    
    eventos_actualizados = 0
    for i, evento in enumerate(eventos, 1):
        print(f"\n[{i}/{total_eventos}] Procesando: {evento.get('curso_nombre', 'Sin nombre')}")
        
        if recalcular_metricas_evento(evento['_id']):
            eventos_actualizados += 1
    
    print(f"\n✅ Proceso completado:")
    print(f"   • Total eventos procesados: {total_eventos}")
    print(f"   • Eventos actualizados: {eventos_actualizados}")
    print(f"   • Eventos sin cambios: {total_eventos - eventos_actualizados}")

def main():
    """Función principal"""
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║  SCRIPT DE ACTUALIZACIÓN DE MÉTRICAS DE EVENTOS      ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    while True:
        print("\n" + "="*60)
        print("MENÚ PRINCIPAL")
        print("="*60)
        print("1. Actualizar un evento específico")
        print("2. Ver estadísticas detalladas de un evento")
        print("3. Actualizar todos los eventos")
        print("4. Salir")
        
        opcion = input("\nSeleccione una opción (1-4): ").strip()
        
        if opcion == "1":
            evento_id = input("Ingrese el ID del evento a actualizar: ").strip()
            if evento_id:
                recalcular_metricas_evento(evento_id)
        
        elif opcion == "2":
            evento_id = input("Ingrese el ID del evento para ver estadísticas: ").strip()
            if evento_id:
                generar_estadisticas_detalladas(evento_id)
        
        elif opcion == "3":
            confirmacion = input("¿Está seguro de actualizar TODOS los eventos? (s/n): ").strip().lower()
            if confirmacion == 's':
                actualizar_todos_los_eventos()
        
        elif opcion == "4":
            print("¡Hasta pronto!")
            break
        
        else:
            print("Opción no válida. Intente de nuevo.")

if __name__ == "__main__":
    main()
```

## Versión simple para actualizar solo el evento específico:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple para actualizar el evento específico
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# Configuración
MONGO_URI = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "exam_db"

# ID del evento a actualizar
EVENTO_ID = "692cbe154775a5cd18b897e0"

def actualizar_evento():
    """Actualiza el evento específico con métricas recalculadas"""
    
    try:
        # Conectar a MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        eventos_collection = db.Eventos
        
        print(f"Conectado a MongoDB - Base de datos: {DB_NAME}")
        
        # Obtener el evento
        evento = eventos_collection.find_one({"_id": ObjectId(EVENTO_ID)})
        
        if not evento:
            print(f"✗ Evento con ID {EVENTO_ID} no encontrado")
            return
        
        print(f"✓ Evento encontrado: {evento.get('curso_nombre')}")
        
        # Recalcular métricas
        cuestionarios = evento.get('cuestionarios_detalle', [])
        total_cuestionarios = len(cuestionarios)
        
        if total_cuestionarios > 0:
            # Calcular promedio
            suma_calificaciones = sum(q.get('calificación', 0) for q in cuestionarios)
            promedio_cuestionarios = suma_calificaciones / total_cuestionarios
            
            print(f"📊 Métricas calculadas:")
            print(f"   • Cuestionarios contestados: {total_cuestionarios}")
            print(f"   • Suma calificaciones: {suma_calificaciones}")
            print(f"   • Promedio: {promedio_cuestionarios:.2f}%")
            
            # Enriquecer cada cuestionario con más datos
            for cuestionario in cuestionarios:
                resp_correctas = cuestionario.get('respuestas_correctas', 0)
                total_preguntas = cuestionario.get('total_preguntas', 0)
                
                if total_preguntas > 0:
                    # Calcular porcentaje
                    porcentaje = (resp_correctas / total_preguntas) * 100
                    cuestionario['porcentaje_aciertos'] = round(porcentaje, 2)
                    
                    # Determinar nivel de desempeño
                    if porcentaje >= 90:
                        nivel = "Excelente"
                    elif porcentaje >= 80:
                        nivel = "Muy Bien"
                    elif porcentaje >= 70:
                        nivel = "Bien"
                    elif porcentaje >= 60:
                        nivel = "Regular"
                    else:
                        nivel = "Necesita mejorar"
                    
                    cuestionario['nivel_desempeno'] = nivel
                    cuestionario['fecha_analisis'] = datetime.now()
        
        # Preparar datos de actualización
        update_data = {
            'cuestionarios_contestados': total_cuestionarios,
            'promedio_cuestionarios': promedio_cuestionarios if total_cuestionarios > 0 else 0,
            'cuestionarios_detalle': cuestionarios,
            'fecha_actualizacion': datetime.now()
        }
        
        # Actualizar en la base de datos
        result = eventos_collection.update_one(
            {"_id": ObjectId(EVENTO_ID)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"\n✅ EVENTO ACTUALIZADO EXITOSAMENTE")
            print(f"   • Documentos modificados: {result.modified_count}")
            print(f"   • Documentos coincidentes: {result.matched_count}")
            
            # Mostrar resumen
            evento_actualizado = eventos_collection.find_one({"_id": ObjectId(EVENTO_ID)})
            print(f"\n📋 RESUMEN FINAL:")
            print(f"   • Curso: {evento_actualizado.get('curso_nombre')}")
            print(f"   • Cuestionarios contestados: {evento_actualizado.get('cuestionarios_contestados', 0)}")
            print(f"   • Promedio cuestionarios: {evento_actualizado.get('promedio_cuestionarios', 0)}%")
            print(f"   • Última actualización: {evento_actualizado.get('fecha_actualizacion')}")
            
        else:
            print("⚠️ No se realizaron cambios (posiblemente ya estaba actualizado)")
    
    except Exception as e:
        print(f"✗ Error durante la actualización: {e}")
        import traceback
        traceback.print_exc()

def verificar_actualizacion():
    """Verifica que la actualización se realizó correctamente"""
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        evento = db.Eventos.find_one({"_id": ObjectId(EVENTO_ID)})
        
        if evento:
            print("\n" + "="*60)
            print("VERIFICACIÓN DE ACTUALIZACIÓN")
            print("="*60)
            
            print(f"\n📋 Información del evento:")
            print(f"   • ID: {EVENTO_ID}")
            print(f"   • Curso: {evento.get('curso_nombre')}")
            print(f"   • Fecha evento: {evento.get('fecha_evento').strftime('%d/%m/%Y')}")
            
            print(f"\n📊 Métricas de cuestionarios:")
            print(f"   • Cuestionarios contestados: {evento.get('cuestionarios_contestados', 0)}")
            print(f"   • Promedio cuestionarios: {evento.get('promedio_cuestionarios', 0)}%")
            print(f"   • Última actualización: {evento.get('fecha_actualizacion')}")
            
            cuestionarios = evento.get('cuestionarios_detalle', [])
            print(f"\n👥 Detalle de cuestionarios ({len(cuestionarios)}):")
            
            for i, cuestionario in enumerate(cuestionarios, 1):
                print(f"\n   [{i}] {cuestionario.get('nombre')}")
                print(f"       • Email: {cuestionario.get('email')}")
                print(f"       • Calificación: {cuestionario.get('calificacion', 0)}%")
                print(f"       • Respuestas correctas: {cuestionario.get('respuestas_correctas', 0)}/{cuestionario.get('total_preguntas', 0)}")
                print(f"       • Porcentaje aciertos: {cuestionario.get('porcentaje_aciertos', 'N/A')}%")
                print(f"       • Nivel: {cuestionario.get('nivel_desempeno', 'N/A')}")
                print(f"       • Fecha respuesta: {cuestionario.get('fecha_respuesta').strftime('%d/%m/%Y %H:%M')}")
        else:
            print("✗ Evento no encontrado para verificación")
    
    except Exception as e:
        print(f"✗ Error en verificación: {e}")

if __name__ == "__main__":
    print("Script de actualización de métricas de cuestionarios")
    print("-" * 50)
    
    # Ejecutar actualización
    actualizar_evento()
    
    # Verificar
    print("\n" + "-" * 50)
    confirmar = input("¿Desea verificar la actualización? (s/n): ").strip().lower()
    if confirmar == 's':
        verificar_actualizacion()
    
    print("\n✅ Proceso completado")
