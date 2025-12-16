from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import config

client = MongoClient(config.Config.MONGODB_URI)
db = client.exam_db

class Database:
    # Colección Alumnos
    @staticmethod
    def get_alumnos():
        return db.Alumnos.find()

    @staticmethod
    def get_alumno_by_email(email):
        return db.Alumnos.find_one({"email": email})

    @staticmethod
    def insert_alumno(alumno_data):
        return db.Alumnos.insert_one(alumno_data)

    @staticmethod
    def update_alumno(email, update_data):
        return db.Alumnos.update_one({"email": email}, {"$set": update_data})

    @staticmethod
    def delete_alumno(email):
        return db.Alumnos.delete_one({"email": email})

    # Colección Instructores
    @staticmethod
    def get_instructores():
        return db.Instructores.find()

    @staticmethod
    def get_instructor_by_email(email):
        return db.Instructores.find_one({"email": email})

    @staticmethod
    def get_instructor_by_id(instructor_id):
        """Obtener instructor por ID"""
        try:
            if isinstance(instructor_id, str):
                return db.Instructores.find_one({"_id": ObjectId(instructor_id)})
            else:
                return db.Instructores.find_one({"_id": instructor_id})
        except Exception as e:
            print(f"ERROR en get_instructor_by_id: {e}")
            return None

    @staticmethod
    def insert_instructor(instructor_data):
        return db.Instructores.insert_one(instructor_data)

    @staticmethod
    def update_instructor(email, update_data):
        return db.Instructores.update_one({"email": email}, {"$set": update_data})

    @staticmethod
    def delete_instructor(email):
        return db.Instructores.delete_one({"email": email})

    # Coleccion Cursos
    @staticmethod
    def get_cursos_activos():
        return db.Cursos.find({"estatus": "activo"})

    @staticmethod
    def get_curso_by_id(curso_id):
        try:
            # Asegurarse de que curso_id es string y crear ObjectId
            if isinstance(curso_id, str):
                return db.Cursos.find_one({"_id": ObjectId(curso_id)})
            else:
                return db.Cursos.find_one({"_id": curso_id})
        except Exception as e:
            print(f"ERROR en get_curso_by_id: {e} - curso_id: {curso_id} - tipo: {type(curso_id)}")
            return None

    @staticmethod
    def insert_curso(curso_data):
        return db.Cursos.insert_one(curso_data)

    @staticmethod
    def get_cursos_no_asignados():
        return db.Cursos.find({"asignado": False, "estatus": "activo"})

    @staticmethod
    def update_curso(curso_id, update_data):
        try:
            print(f"DEBUG [update_curso]: Actualizando curso {curso_id} con datos: {update_data}")
            result = db.Cursos.update_one({"_id": ObjectId(curso_id)}, {"$set": update_data})
            print(f"DEBUG [update_curso]: Resultado - Modified count: {result.modified_count}")
            return result
        except Exception as e:
            print(f"ERROR en update_curso: {e}")
            raise e

    @staticmethod
    def get_curso_by_name(nombre):
        return db.Cursos.find_one({"nombre": nombre})

    @staticmethod
    def get_cursos_activos_con_instructor():
        """Obtener cursos activos que tienen instructor asignado"""
        return db.Cursos.find({
            "estatus": "activo",
            "asignado": True,
            "instructor_id": {"$ne": None}
        })

    # Colección Cuestionarios (exámenes de aprendizaje)
    @staticmethod
    def insert_cuestionario(cuestionario_data):
        """Insertar un cuestionario resuelto (examen de aprendizaje)"""
        try:
            print(f"DEBUG [models.py]: Insertando cuestionario en colección 'cuestionarios'")
            print(f"DEBUG [models.py]: Calificacion: {cuestionario_data.get('calificacion')}")
            result = db.cuestionarios.insert_one(cuestionario_data)
            print(f"DEBUG [models.py]: Cuestionario insertado con ID: {result.inserted_id}")
            return result
        except Exception as e:
            print(f"ERROR [models.py] en insert_cuestionario: {e}")
            raise e

    @staticmethod
    def get_cuestionarios_by_examen(examen_id):
        """Obtener todos los cuestionarios de un examen específico"""
        try:
            return db.cuestionarios.find({"examen_id": ObjectId(examen_id)})
        except Exception as e:
            print(f"ERROR en get_cuestionarios_by_examen: {e}")
            return []

    @staticmethod
    def get_cuestionarios_by_alumno(alumno_email):
        """Obtener todos los cuestionarios de un alumno"""
        try:
            return db.cuestionarios.find({"alumno_email": alumno_email}).sort("fecha_realizacion", -1)
        except Exception as e:
            print(f"ERROR en get_cuestionarios_by_alumno: {e}")
            return []

    @staticmethod
    def get_cuestionario_by_id(cuestionario_id):
        """Obtener un cuestionario por su ID"""
        try:
            return db.cuestionarios.find_one({"_id": ObjectId(cuestionario_id)})
        except Exception as e:
            print(f"ERROR en get_cuestionario_by_id: {e}")
            return None

    @staticmethod
    def get_cuestionarios_by_curso(curso_id):
        """Obtener todos los cuestionarios de un curso específico"""
        try:
            return db.cuestionarios.find({"curso_id": ObjectId(curso_id)})
        except Exception as e:
            print(f"ERROR en get_cuestionarios_by_curso: {e}")
            return []

    # Colección Evaluaciones (evaluaciones de opinión del curso)
    @staticmethod
    def insert_evaluacion(evaluacion_data):
        """Insertar una evaluación de opinión en la colección evaluaciones"""
        try:
            print("DEBUG [models.py]: Insertando evaluación de opinión...")
            result = db.evaluaciones.insert_one(evaluacion_data)
            print(f"DEBUG [models.py]: Evaluación de opinión insertada con ID: {result.inserted_id}")
            return result
        except Exception as e:
            print(f"ERROR [models.py] en insert_evaluacion: {e}")
            raise e
 
    @staticmethod
    def get_evaluaciones_by_alumno(alumno_email):
        """Obtener todas las evaluaciones de opinión de un alumno"""
        try:
            return db.evaluaciones.find({"alumno_email": alumno_email}).sort("fecha_realizacion", -1)
        except Exception as e:
            print(f"ERROR en get_evaluaciones_by_alumno: {e}")
            return []

    @staticmethod
    def get_evaluacion_by_id(evaluacion_id):
        """Obtener una evaluación por su ID"""
        try:
            return db.evaluaciones.find_one({"_id": ObjectId(evaluacion_id)})
        except Exception as e:
            print(f"ERROR en get_evaluacion_by_id: {e}")
            return None

    @staticmethod
    def get_evaluaciones_by_curso(curso_id):
        """Obtener todas las evaluaciones completadas de un curso específico"""
        try:
            return db.evaluaciones.find({"curso_id": ObjectId(curso_id)})
        except Exception as e:
            print(f"ERROR en get_evaluaciones_by_curso: {e}")
            return []

    @staticmethod
    def insert_evaluacion_taller(evaluacion_data):
        """Insertar evaluación específica para taller"""
        return db.evaluaciones.insert_one(evaluacion_data)

    @staticmethod
    def get_evaluaciones_taller_by_curso(curso_id):
        """Obtener evaluaciones de taller por curso""" 
        return db.evaluaciones.find({
            "tipo_evaluacion": "evaluacion_taller",
            "curso_id": ObjectId(curso_id)
        })

    # Coleccion Exámenes
    @staticmethod
    def get_examenes_by_curso(curso_id):
        """Obtener todos los exámenes de un curso específico"""
        try:
            return db.Exámenes.find({"curso_id": ObjectId(curso_id)})
        except Exception as e:
            print(f"ERROR en get_examenes_by_curso: {e}")
            return []

    @staticmethod
    def get_examen_by_id(examen_id):
        try:
            return db.Exámenes.find_one({"_id": ObjectId(examen_id)})
        except Exception as e:
            print(f"ERROR en get_examen_by_id: {e}")
            return None

    @staticmethod
    def insert_examen(examen_data):
        return db.Exámenes.insert_one(examen_data)

    @staticmethod
    def get_examenes_by_curso_and_tipo(curso_id, tipo_examen):
        """Obtener exámenes de un curso por tipo específico"""
        try:
            examenes = list(db.Exámenes.find({
                "curso_id": ObjectId(curso_id),
                "tipo_examen": tipo_examen
            }))
            print(f"DEBUG [get_examenes_by_curso_and_tipo]: Curso {curso_id}, tipo {tipo_examen} -> {len(examenes)} exámenes")
            return examenes
        except Exception as e:
            print(f"ERROR en get_examenes_by_curso_and_tipo: {e}")
            return []

    @staticmethod
    def get_examen_by_curso_and_tipo(curso_id, tipo_examen):
        try:
            return db.Exámenes.find_one({
                "curso_id": ObjectId(curso_id),
                "tipo_examen": tipo_examen
            })
        except Exception as e:
            print(f"ERROR en get_examen_by_curso_and_tipo: {e}")
            return None

    @staticmethod
    def get_examenes_completos():
        """Obtener exámenes con información del curso"""
        pipeline = [
            {
                "$lookup": {
                    "from": "Cursos",
                    "localField": "curso_id",
                    "foreignField": "_id",
                    "as": "curso_info"
                }
            },
            {
                "$unwind": "$curso_info"
            },
            {
                "$project": {
                    "nombre": 1,
                    "tipo_examen": 1,
                    "curso_nombre": "$curso_info.nombre",
                    "instructor_nombre": "$curso_info.instructor_nombre",
                    "preguntas": 1,
                    "estructura": 1,
                    "formato_especifico": 1,
                    "fecha_creacion": 1,
                    "descripcion": 1
                }
            }
        ]
        return db.Exámenes.aggregate(pipeline)

    @staticmethod
    def delete_examen(examen_id):
        return db.Exámenes.delete_one({"_id": ObjectId(examen_id)})

    # Métodos adicionales para la gestión de instructores y cursos
    @staticmethod
    def get_instructores_with_cursos():
        pipeline = [
            {
                "$lookup": {
                    "from": "Cursos",
                    "localField": "cursos",
                    "foreignField": "_id",
                    "as": "cursos_info"
                }
            }
        ]
        return db.Instructores.aggregate(pipeline)

    @staticmethod
    def update_instructor_cursos(email, cursos_array):
        return db.Instructores.update_one(
            {"email": email},
            {"$set": {"cursos": cursos_array}}
        )

    @staticmethod
    def get_cursos_count():
        return db.Cursos.count_documents({})

    @staticmethod
    def get_instructores_count():
        return db.Instructores.count_documents({})

    @staticmethod
    def delete_curso(curso_id):
        return db.Cursos.delete_one({"_id": ObjectId(curso_id)})

    # Colección Eventos
    @staticmethod
    def get_eventos():
        """Obtener todos los eventos"""
        try:
            return list(db.Eventos.find())
        except Exception as e:
            print(f"ERROR en get_eventos: {e}")
            return []

    @staticmethod
    def get_eventos_by_curso(curso_id):
        """Obtener eventos por curso"""
        try:
            return db.Eventos.find({"curso_id": ObjectId(curso_id)})
        except Exception as e:
            print(f"ERROR en get_eventos_by_curso: {e}")
            return []

    @staticmethod
    def get_eventos_proximos():
        """Obtener eventos del mes actual"""
        try:
            hoy = datetime.now()
            inicio_mes = datetime(hoy.year, hoy.month, 1)
            if hoy.month == 12:
                fin_mes = datetime(hoy.year + 1, 1, 1)
            else:
                fin_mes = datetime(hoy.year, hoy.month + 1, 1)
        
            return db.Eventos.find({
                "fecha_evento": {"$gte": inicio_mes, "$lt": fin_mes}
            }).sort("fecha_evento", 1)
        except Exception as e:
            print(f"ERROR en get_eventos_proximos: {e}")
            return []

    @staticmethod
    def get_eventos_abiertos_by_curso(curso_id):
        """Obtener eventos abiertos por curso"""
        try:
            return list(db.Eventos.find({
                "curso_id": ObjectId(curso_id),
                "estatus": "abierto"
            }).sort("fecha_evento", 1))
        except Exception as e:
            print(f"ERROR en get_eventos_abiertos_by_curso: {e}")
            return []

    @staticmethod
    def get_eventos_by_instructor_id(instructor_id):
        """Obtener eventos por ID de instructor"""
        try:
            return list(db.Eventos.find({"instructor_id": instructor_id}))
        except Exception as e:
            print(f"ERROR en get_eventos_by_instructor_id: {e}")
            return []

    @staticmethod
    def insert_evento(evento_data):
        """Insertar un nuevo evento"""
        return db.Eventos.insert_one(evento_data)

    @staticmethod
    def get_eventos_abiertos():
        """Obtener todos los eventos abiertos"""
        try:
            return db.Eventos.find({"estatus": "abierto"}).sort("fecha_evento", 1)
        except Exception as e:
            print(f"ERROR en get_eventos_abiertos: {e}")
            return []

    @staticmethod
    def get_eventos_by_instructor(instructor_email):
        """Obtener eventos asignados a un instructor"""
        try:
            return db.Eventos.find({
                "instructor_email": instructor_email
            }).sort("fecha_evento", 1)
        except Exception as e:
            print(f"ERROR en get_eventos_by_instructor: {e}")
            return []

    @staticmethod
    def get_evento_by_id(evento_id):
        try:
            return db.Eventos.find_one({"_id": ObjectId(evento_id)})
        except Exception as e:
            print(f"ERROR en get_evento_by_id: {e}")
            return None

    @staticmethod
    def get_eventos_by_mes(year, month):
        """Obtener eventos de un mes y año específicos"""
        try:
            inicio_mes = datetime(year, month, 1)
            if month == 12:
                fin_mes = datetime(year + 1, 1, 1)
            else:
                fin_mes = datetime(year, month + 1, 1)
        
            return db.Eventos.find({
                "fecha_evento": {"$gte": inicio_mes, "$lt": fin_mes}
            }).sort("fecha_evento", 1)
        except Exception as e:
           print(f"ERROR en get_eventos_by_mes: {e}")
           return []

    @staticmethod
    def update_evento(evento_id, update_data):
        return db.Eventos.update_one({"_id": ObjectId(evento_id)}, {"$set": update_data})

    @staticmethod
    def delete_evento(evento_id):
        return db.Eventos.delete_one({"_id": ObjectId(evento_id)})

    # Métodos adicionales para alumnos y evaluaciones
    @staticmethod
    def get_alumnos_by_curso(curso_nombre):
        """Obtener alumnos por nombre de curso"""
        try:
            return db.Alumnos.find({"curso": curso_nombre})
        except Exception as e:
            print(f"ERROR en get_alumnos_by_curso: {e}")
            return []

    @staticmethod
    def get_evaluaciones_by_alumno_and_curso(alumno_email, curso_id):
        """Obtener evaluaciones de un alumno en un curso específico"""
        try:
            return db.evaluaciones.find({
                "alumno_email": alumno_email,
                "curso_id": ObjectId(curso_id)
            })
        except Exception as e:
            print(f"ERROR en get_evaluaciones_by_alumno_and_curso: {e}")
            return []

    @staticmethod
    def get_total_alumnos_by_curso(curso_nombre):
        """Obtener el total de alumnos por curso"""
        try:
            count = db.Alumnos.count_documents({"curso": curso_nombre})
            print(f"DEBUG [get_total_alumnos_by_curso]: Curso '{curso_nombre}' tiene {count} alumnos")
            return count
        except Exception as e:
            print(f"ERROR en get_total_alumnos_by_curso: {e}")
            return 0

    @staticmethod
    def get_evaluaciones_by_examen(examen_id):
        """Obtener todas las evaluaciones de un examen específico"""
        try:
            return db.evaluaciones.find({"examen_id": ObjectId(examen_id)})
        except Exception as e:
            print(f"ERROR en get_evaluaciones_by_examen: {e}")
            return []