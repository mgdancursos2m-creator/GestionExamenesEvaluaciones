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
