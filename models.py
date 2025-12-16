from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import config

class Database:
    def __init__(self, app=None):
        """Inicializa la conexión a MongoDB"""
        self.client = None
        self.db = None
        
        if app is not None:
            self.init_app(app)
        else:
            # Conexión directa como fallback
            self._connect_directly()

    def init_app(self, app):
        """Inicializa la conexión a MongoDB con la aplicación Flask"""
        try:
            # Usar la URI de tu configuración
            mongo_uri = app.config.get('MONGODB_URI')
            self.client = MongoClient(mongo_uri)
            # Extraer el nombre de la base de datos de la URI
            db_name = mongo_uri.split('/')[-1].split('?')[0]
            self.db = self.client[db_name]
            print(f"DEBUG: Conexión a MongoDB establecida - DB: {db_name}")
        except Exception as e:
            print(f"ERROR al conectar a MongoDB: {e}")
            # Intentar conexión directa como fallback
            self._connect_directly()

    def _connect_directly(self):
        """Conexión directa como fallback"""
        try:
            mongo_uri = "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"
            self.client = MongoClient(mongo_uri)
            self.db = self.client['exam_db']
            print("DEBUG: Conexión directa establecida como fallback")
        except Exception as e:
            print(f"ERROR al conectar directamente: {e}")
            raise

    def _get_db(self):
        """Método seguro para obtener la conexión a la base de datos"""
        if self.db is None:
            print("ERROR: Database no inicializada. Intentando reconectar...")
            self._connect_directly()
        return self.db

    # =============================================================================
    # MÉTODOS DE CONVERSIÓN Y VALIDACIÓN
    # =============================================================================
    
    def _to_object_id(self, id_value):
        """Convertir string a ObjectId de manera segura"""
        try:
            if isinstance(id_value, str):
                return ObjectId(id_value)
            return id_value
        except Exception as e:
            print(f"ERROR convirtiendo a ObjectId: {e} - valor: {id_value}")
            return None

    # =============================================================================
    # COLECCIÓN ALUMNOS - TODOS ACTUALIZADOS
    # =============================================================================

    def get_alumnos(self):
        db = self._get_db()
        if db is None:
            return []
        return db.Alumnos.find()

    def get_alumno_by_email(self, email):
        """Obtiene un alumno por email"""
        try:
            db = self._get_db()
            if db is None:
                print("ERROR: No se pudo obtener conexión a la base de datos")
                return None
            return db.Alumnos.find_one({'email': email})
        except Exception as e:
            print(f"ERROR en get_alumno_by_email: {e}")
            return None

    def get_alumnos_by_curso(self, curso_nombre):
        db = self._get_db()
        if db is None:
            return []
        return db.Alumnos.find({"curso": curso_nombre})

    def get_total_alumnos_by_curso(self, curso_nombre):
        try:
            db = self._get_db()
            if db is None:
                return 0
            count = db.Alumnos.count_documents({"curso": curso_nombre})
            print(f"DEBUG: Curso '{curso_nombre}' tiene {count} alumnos")
            return count
        except Exception as e:
            print(f"ERROR en get_total_alumnos_by_curso: {e}")
            return 0

    def insert_alumno(self, alumno_data):
        db = self._get_db()
        if db is None:
            return None
        return db.Alumnos.insert_one(alumno_data)

    def update_alumno(self, email_original, datos_actualizados):
        """Actualiza un alumno en la base de datos"""
        try:
            db = self._get_db()
            if db is None:
                print("ERROR: No se pudo obtener conexión a la base de datos")
                return False
                
            print(f"DEBUG: Actualizando alumno {email_original} con datos: {datos_actualizados}")
            
            result = db.Alumnos.update_one(
                {'email': email_original},
                {'$set': datos_actualizados}
            )
            
            print(f"DEBUG: update_alumno - Matched: {result.matched_count}, Modified: {result.modified_count}")
            
            if result.matched_count == 0:
                print(f"DEBUG: No se encontró alumno con email: {email_original}")
                return False
                
            return result.modified_count > 0
            
        except Exception as e:
            print(f"ERROR en update_alumno: {e}")
            return False

    def delete_alumno(self, email):
        db = self._get_db()
        if db is None:
            return None
        return db.Alumnos.delete_one({"email": email})

    # =============================================================================
    # COLECCIÓN INSTRUCTORES - TODOS ACTUALIZADOS
    # =============================================================================

    def get_instructores(self):
        """Obtener todos los instructores"""
        try:
            db = self._get_db()
            if db is None:
                return []
            return db.Instructores.find({})
        except Exception as e:
            print(f"ERROR al obtener instructores: {e}")
            return []

    def get_instructor_by_email(self, email):
        """
        Obtiene un instructor por su email
        """
        try:
            db = self._get_db()
            if db is None:
                return None
            instructor = db.Instructores.find_one({'email': email})
            if instructor and '_id' in instructor:
                instructor['_id'] = str(instructor['_id'])
            return instructor
        except Exception as e:
            print(f"Error en get_instructor_by_email: {e}")
            return None

    def get_instructor_by_id(self, instructor_id):
        try:
            db = self._get_db()
            if db is None:
                return None
            object_id = self._to_object_id(instructor_id)
            return db.Instructores.find_one({"_id": object_id}) if object_id else None
        except Exception as e:
            print(f"ERROR en get_instructor_by_id: {e}")
            return None

    def get_instructores_count(self):
        db = self._get_db()
        if db is None:
            return 0
        return db.Instructores.count_documents({})

    def insert_instructor(self, instructor_data):
        db = self._get_db()
        if db is None:
            return None
        return db.Instructores.insert_one(instructor_data)

    def update_instructor(self, email, update_data):
        db = self._get_db()
        if db is None:
            return None
        return db.Instructores.update_one({"email": email}, {"$set": update_data})

    def delete_instructor(self, email):
        db = self._get_db()
        if db is None:
            return None
        return db.Instructores.delete_one({"email": email})

    # =============================================================================
    # COLECCIÓN CURSOS - TODOS ACTUALIZADOS
    # =============================================================================

    def get_cursos_activos(self):
        """Obtener todos los cursos activos"""
        try:
            db = self._get_db()
            if db is None:
                return []
            return db.Cursos.find({'estatus': 'activo'})
        except Exception as e:
            print(f"ERROR al obtener cursos activos: {e}")
            return []

    def get_curso_by_id(self, curso_id):
        """Obtener curso por ID"""
        try:
            db = self._get_db()
            if db is None:
                return None
            return db.Cursos.find_one({'_id': ObjectId(curso_id)})
        except Exception as e:
            print(f"ERROR al obtener curso por ID: {e}")
            return None

    def get_curso_by_name(self, nombre):
        db = self._get_db()
        if db is None:
            return None
        return db.Cursos.find_one({"nombre": nombre})

    def insert_curso(self, curso_data):
        db = self._get_db()
        if db is None:
            return None
        return db.Cursos.insert_one(curso_data)

    def update_curso(self, curso_id, update_data):
        try:
            db = self._get_db()
            if db is None:
                return None
            object_id = self._to_object_id(curso_id)
            if not object_id:
                raise ValueError("ID de curso inválido")
                
            print(f"DEBUG: Actualizando curso {curso_id} con datos: {update_data}")
            result = db.Cursos.update_one({"_id": object_id}, {"$set": update_data})
            print(f"DEBUG: Resultado - Modified count: {result.modified_count}")
            return result
        except Exception as e:
            print(f"ERROR en update_curso: {e}")
            raise e

    def delete_curso(self, curso_id):
        db = self._get_db()
        if db is None:
            return None
        object_id = self._to_object_id(curso_id)
        return db.Cursos.delete_one({"_id": object_id}) if object_id else None

    # =============================================================================
    # COLECCIÓN EVENTOS - TODOS ACTUALIZADOS
    # =============================================================================

    def get_eventos(self):
        """Obtiene todos los eventos"""
        try:
            db = self._get_db()
            if db is None:
                print("ERROR: No se pudo obtener conexión a la base de datos")
                return []
            eventos = list(db.Eventos.find())
            print(f"DEBUG: get_eventos - Encontrados {len(eventos)} eventos")
            return eventos
        except Exception as e:
            print(f"ERROR en get_eventos: {e}")
            return []

    def get_evento_by_id(self, evento_id):
        """Obtener evento por ID"""
        try:
            db = self._get_db()
            if db is None:
                return None
        
            # Convertir string a ObjectId
            try:
                if isinstance(evento_id, str):
                    object_id = ObjectId(evento_id)
                else:
                    object_id = evento_id
            except Exception as e:
                print(f"ERROR convirtiendo ID: {e}")
                return None
        
            return db.Eventos.find_one({'_id': object_id})
        
        except Exception as e:
            print(f"ERROR al obtener evento por ID: {e}")
            return None

    def get_eventos_by_curso(self, curso_id):
        try:
            db = self._get_db()
            if db is None:
                return []
            object_id = self._to_object_id(curso_id)
            return db.Eventos.find({"curso_id": object_id}) if object_id else []
        except Exception as e:
            print(f"ERROR en get_eventos_by_curso: {e}")
            return []

    def get_eventos_by_mes(self, year, month):
        """Obtener eventos por mes y año"""
        try:
            db = self._get_db()
            if db is None:
                return []

            eventos_cursor = db.Eventos.find({
                "$expr": {
                    "$and": [
                        { "$eq": [{ "$year": "$fecha_evento" }, year] },
                        { "$eq": [{ "$month": "$fecha_evento" }, month] }
                    ]
                }
            })

            eventos_list = list(eventos_cursor)

            # Solo asegurar que los valores numéricos sean float
            for evento in eventos_list:
                if 'promedio_cuestionarios' in evento:
                    evento['promedio_cuestionarios'] = float(evento['promedio_cuestionarios'])
                if 'promedio_evaluaciones' in evento:
                    evento['promedio_evaluaciones'] = float(evento['promedio_evaluaciones'])

            print(f"DEBUG: Número de eventos encontrados por $expr: {len(eventos_list)}")
            return eventos_list
        except Exception as e:
            print(f"ERROR en get_eventos_by_mes: {e}")
            return []

    def insert_evento(self, evento_data):
        db = self._get_db()
        if db is None:
            return None
        return db.Eventos.insert_one(evento_data)

    def update_evento(self, evento_id, update_data):
        """Actualiza un evento por su ID"""
        try:
            db = self._get_db()
            if db is None:
                print("ERROR: No se pudo obtener conexión a la base de datos")
                return False
                
            result = db.Eventos.update_one(
                {'_id': ObjectId(evento_id)},
                {'$set': update_data}
            )
            print(f"DEBUG: update_evento - Matched: {result.matched_count}, Modified: {result.modified_count}")
            return result.modified_count > 0
        except Exception as e:
            print(f"ERROR en update_evento: {e}")
            return False

    def update_evento_instructor(self, evento_id, instructor_email, instructor_nombre):
        """
        Actualiza el instructor asignado a un evento
        """
        try:
            print(f"DEBUG DB: Actualizando evento {evento_id}")
            print(f"DEBUG DB: Con instructor - Email: {instructor_email}, Nombre: {instructor_nombre}")
        
            db = self._get_db()
            if db is None:
                print("DEBUG DB: Error - No se pudo obtener conexión a la base de datos")
                return False

            # Verificar que el evento_id sea válido
            if not evento_id:
                print("DEBUG DB: Error - evento_id está vacío")
                return False
            
            # Verificar que el ObjectId sea válido
            try:
                object_id = ObjectId(evento_id)
                print(f"DEBUG DB: ObjectId convertido: {object_id}")
            except Exception as e:
                print(f"DEBUG DB: Error convirtiendo ObjectId: {e}")
                return False
        
            # DEBUG: Verificar qué eventos existen en la base de datos
            print("DEBUG DB: Listando todos los eventos en la colección:")
            todos_eventos = list(db.Eventos.find({}, {'curso_nombre': 1, 'fecha_evento': 1}).limit(5))
            for ev in todos_eventos:
                print(f"DEBUG DB: - Evento ID: {ev.get('_id')}, Curso: {ev.get('curso_nombre')}")
        
            # Verificar si el evento existe
            print(f"DEBUG DB: Buscando específicamente evento con _id: {object_id}")
            evento_existente = db.Eventos.find_one({'_id': object_id})
        
            if not evento_existente:
                print(f"DEBUG DB: Error - No se encontró evento con id {object_id}")
                print(f"DEBUG DB: Tipo del _id en la consulta: {type(object_id)}")
            
                # Intentar una búsqueda más amplia para debug
                evento_alternativo = db.Eventos.find_one({'curso_nombre': 'Lenguaje Estructurado de Consultas'})
                if evento_alternativo:
                    print(f"DEBUG DB: Pero SÍ existe un evento con mismo nombre: {evento_alternativo.get('_id')}")
                return False
            
            print(f"DEBUG DB: Evento encontrado: {evento_existente.get('curso_nombre', 'Sin nombre')}")
        
            # Actualizar el evento
            result = db.Eventos.update_one(
                {'_id': object_id},
                {
                    '$set': {
                        'instructor_email': instructor_email,
                        'instructor_nombre': instructor_nombre,
                        'fecha_actualizacion': datetime.now()
                    }
                }
            )
        
            print(f"DEBUG DB: Resultado MongoDB - matched: {result.matched_count}, modified: {result.modified_count}")
        
            if result.matched_count == 0:
                print("DEBUG DB: No se encontró el evento para actualizar")
                return False
            
            if result.modified_count == 0:
                print("DEBUG DB: El evento se encontró pero no se modificó")
                return True  # Aún así retornamos True porque el evento existe
            
            print("DEBUG DB: Actualización exitosa")
            return True
        
        except Exception as e:
            print(f"DEBUG DB: Error en update_evento_instructor: {str(e)}")
            import traceback
            print(f"DEBUG DB: Traceback: {traceback.format_exc()}")
            return False

    def get_eventos_abiertos_by_curso(self, curso_nombre):
        """Obtiene todos los eventos abiertos de un curso específico"""
        try:
            db = self._get_db()
            if db is None:
                return []
            query = {
                'curso_nombre': curso_nombre,
                'estatus': 'abierto'
            }
            eventos = list(db.Eventos.find(query))
         
            # Convertir ObjectId a string para serialización JSON
            for evento in eventos:
                if '_id' in evento:
                    evento['_id'] = str(evento['_id'])
                   
            return eventos
        except Exception as e:
            print(f"Error en get_eventos_abiertos_by_curso: {e}")
            return []

    def delete_evento(self, evento_id):
        db = self._get_db()
        if db is None:
            return None
        object_id = self._to_object_id(evento_id)
        return db.Eventos.delete_one({"_id": object_id}) if object_id else None

    def get_eventos_by_instructor(self, instructor_email):
        """Obtiene todos los eventos asignados a un instructor por su email"""
        try:
            db = self._get_db()
            if db is None:
                print("ERROR: No se pudo obtener conexión a la base de datos")
                return []
            eventos = list(db.Eventos.find({'instructor_email': instructor_email}))
            # Convertir ObjectId a string para serialización
            for evento in eventos:
                if '_id' in evento:
                    evento['_id'] = str(evento['_id'])
            print(f"DEBUG: get_eventos_by_instructor - Encontrados {len(eventos)} eventos para {instructor_email}")
            return eventos
        except Exception as e:
            print(f"ERROR en get_eventos_by_instructor: {e}")
            return []

    def actualizar_metricas_evento(self, evento_id):
        """Actualiza todas las métricas de un evento (cuestionarios y evaluaciones)"""
        try:
            db = self._get_db()
            if db is None:
                return False
            
            evento = db.Eventos.find_one({"_id": ObjectId(evento_id)})
            if not evento:
                return False
        
            # Actualizar métricas de cuestionarios
            cuestionarios = evento.get('cuestionarios_detalle', [])
            total_cuestionarios = len(cuestionarios)
            if total_cuestionarios > 0:
                suma_calificaciones = sum(q.get('calificacion', 0) for q in cuestionarios)
                promedio_cuestionarios = suma_calificaciones / total_cuestionarios
            else:
                promedio_cuestionarios = 0
        
            # Actualizar métricas de evaluaciones
            evaluaciones = evento.get('evaluaciones_detalle', [])
            total_evaluaciones = len(evaluaciones)
            if total_evaluaciones > 0:
                suma_puntuaciones = sum(e.get('puntuacion_promedio', 0) for e in evaluaciones)
                promedio_evaluaciones = suma_puntuaciones / total_evaluaciones
            else:
                promedio_evaluaciones = 0
         
            # Actualizar el evento con las métricas correctas
            db.Eventos.update_one(
                {"_id": ObjectId(evento_id)},
                {
                    "$set": {
                        "cuestionarios_contestados": total_cuestionarios,
                        "promedio_cuestionarios": promedio_cuestionarios,
                        "evaluaciones_contestadas": total_evaluaciones,
                        "promedio_evaluaciones": promedio_evaluaciones,
                        "total_alumnos": len(evento.get('alumnos_asignados', []))
                    }
                }
            )
            return True
        
        except Exception as e:
            print(f"ERROR en actualizar_metricas_evento: {e}")
            return False


    # =============================================================================
    # MÉTODOS SIMPLIFICADOS - PARA EVITAR COMPLICACIONES TEMPORALES
    # =============================================================================

    def get_cuestionarios_by_alumno_and_curso(self, alumno_email, curso_id):
        """Versión simplificada - devuelve lista vacía por ahora"""
        print(f"DEBUG: get_cuestionarios_by_alumno_and_curso - {alumno_email}, {curso_id}")
        return []

    def get_evaluaciones_by_alumno_and_curso(self, alumno_email, curso_id):
        """Versión simplificada - devuelve lista vacía por ahora"""
        print(f"DEBUG: get_evaluaciones_by_alumno_and_curso - {alumno_email}, {curso_id}")
        return []

# Instancia global
db = Database()