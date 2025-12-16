def reparar_alumnos_vacios():
    from bson import ObjectId
    import re
    
    eventos = mongo.db.eventos.find({"alumnos_asignados": {"$elemMatch": {"$eq": {}}}})
    
    for evento in eventos:
        print(f"Reparando evento: {evento.get('curso_nombre', 'Sin nombre')}")
        
        alumnos_reparados = []
        alumnos_originales = evento.get('alumnos_asignados', [])
        
        for i, alumno in enumerate(alumnos_originales):
            if alumno == {}:  # Si es un objeto vacío
                # Crear datos temporales
                alumno_reparado = {
                    'nombre': 'Alumno',
                    'apellido': f'Reparado {i+1}',
                    'email': f'alumno.reparado.{i+1}@evento{evento["_id"]}.com',
                    'telefono': 'No especificado',
                    'empresa': 'No especificada'
                }
                alumnos_reparados.append(alumno_reparado)
                print(f"  - Reparado alumno vacío {i+1}")
            else:
                alumnos_reparados.append(alumno)
        
        # Actualizar en la base de datos
        mongo.db.eventos.update_one(
            {"_id": evento["_id"]},
            {"$set": {"alumnos_asignados": alumnos_reparados}}
        )
    
    print("Reparación completada")

# Ejecutar una vez
# reparar_alumnos_vacios()
