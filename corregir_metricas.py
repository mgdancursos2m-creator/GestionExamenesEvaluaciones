from pymongo import MongoClient
from bson import ObjectId

# Conexión a MongoDB
client = MongoClient("mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0")
db = client.exam_db

# ID específico del evento
evento_id = ObjectId("6920f619fe3aafc0a7938324")

evento = db.Eventos.find_one({"_id": evento_id})

print(f"Procesando evento: {evento.get('curso_nombre')}")

# Calcular valores CORRECTOS para cuestionarios
cuestionarios = evento.get("cuestionarios_detalle", [])
total_cuestionarios = len(cuestionarios)  # Debería ser 2

suma_calificaciones = 0
for q in cuestionarios:
    # El campo está como 'calificacion' en tu documento
    calificacion = q.get("calificacion", 0)
    print(f"Calificación: {calificacion}")
    suma_calificaciones += calificacion

promedio_cuestionarios = suma_calificaciones / total_cuestionarios if total_cuestionarios > 0 else 0

# Calcular valores CORRECTOS para evaluaciones
evaluaciones = evento.get("evaluaciones_detalle", [])
total_evaluaciones = len(evaluaciones)  # Debería ser 2

suma_puntuaciones = 0
for e in evaluaciones:
    puntuacion = e.get("puntuacion_promedio", 0)
    print(f"Puntuación: {puntuacion}")
    suma_puntuaciones += puntuacion

promedio_evaluaciones = suma_puntuaciones / total_evaluaciones if total_evaluaciones > 0 else 0

print(f"\nResumen:")
print(f"Cuestionarios: {total_cuestionarios} registros")
print(f"  Suma calificaciones: {suma_calificaciones}")
print(f"  Promedio: {promedio_cuestionarios}")
print(f"Evaluaciones: {total_evaluaciones} registros")
print(f"  Suma puntuaciones: {suma_puntuaciones}")
print(f"  Promedio: {promedio_evaluaciones}")

# Actualizar el documento
db.Eventos.update_one(
    {"_id": evento_id},
    {
        "$set": {
            "cuestionarios_contestados": total_cuestionarios,  # Debería ser 2
            "promedio_cuestionarios": promedio_cuestionarios,  # (70 + 60) / 2 = 65
            "evaluaciones_contestadas": total_evaluaciones,    # Debería ser 2
            "promedio_evaluaciones": promedio_evaluaciones     # (5.333 + 6) / 2 = 5.6665
        }
    }
)

print("\n¡Documento actualizado correctamente!")