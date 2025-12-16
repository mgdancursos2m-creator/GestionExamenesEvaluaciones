from flask import jsonify
from bson import ObjectId
from datetime import datetime

# Función para generar datos a graficar 
def generar_datos_graficas(evento):
    """Genera datos de gráficas para cualquier evento (reutilizable)"""
    try:
        # Obtener cuestionarios y evaluaciones del evento
        cuestionarios_detalle = evento.get('cuestionarios_detalle', [])
        evaluaciones_detalle = evento.get('evaluaciones_detalle', [])

        # Inicializar estructuras para gráficas
        datos_graficas = {
            'cuestionarios': None,
            'evaluaciones': None,
            'alumnos': None
        }

        # 1. GRÁFICA DE CUESTIONARIOS (Distribución de calificaciones)
        if cuestionarios_detalle and len(cuestionarios_detalle) > 0:
            # Crear rangos de calificación
            rangos = {
                "0-50%": 0,
                "51-70%": 0,
                "71-85%": 0,
                "86-100%": 0
            }

            for cuestionario in cuestionarios_detalle:
                calificacion = cuestionario.get('calificacion', 0)
                
                if calificacion <= 50:
                    rangos["0-50%"] += 1
                elif calificacion <= 70:
                    rangos["51-70%"] += 1
                elif calificacion <= 85:
                    rangos["71-85%"] += 1
                else:
                    rangos["86-100%"] += 1

            # Solo crear gráfica si hay datos
            if any(val > 0 for val in rangos.values()):
                datos_graficas["cuestionarios"] = {
                    "labels": list(rangos.keys()),
                    "datasets": [{
                        "data": list(rangos.values()),
                        "backgroundColor": ["#FF6384", "#FFCE56", "#36A2EB", "#4BC0C0"],
                        "hoverBackgroundColor": ["#FF6384", "#FFCE56", "#36A2EB", "#4BC0C0"],
                        "borderWidth": 1
                    }]
                }

        # 2. GRÁFICA DE EVALUACIONES (Promedio por pregunta)
        if evaluaciones_detalle and len(evaluaciones_detalle) > 0:
            # Procesar la primera evaluación para gráfica de líneas
            evaluacion = evaluaciones_detalle[0]
            respuestas_detalle = evaluacion.get('respuestas_detalle', [])

            if respuestas_detalle:
                respuestas_escala = []
                labels_escala = []

                for i, respuesta in enumerate(respuestas_detalle):
                    if respuesta.get('tipo') == 'escala':
                        try:
                            valor = int(respuesta.get('respuesta', 0))
                            respuestas_escala.append(valor)
                            # Crear etiqueta corta para la pregunta
                            pregunta = respuesta.get('pregunta', f'Preg {i+1}')
                            if len(pregunta) > 20:
                                pregunta = pregunta[:17] + "..."
                            labels_escala.append(pregunta)
                        except (ValueError, TypeError):
                            continue

                if respuestas_escala:
                    datos_graficas["evaluaciones"] = {
                        "labels": labels_escala,
                        "datasets": [{
                            "label": "Calificación por pregunta (1-6)",
                            "data": respuestas_escala,
                            "borderColor": "#36A2EB",
                            "backgroundColor": "rgba(54, 162, 235, 0.2)",
                            "fill": True,
                            "tension": 0.1,
                            "pointBackgroundColor": "#36A2EB",
                            "pointBorderColor": "#ffffff",
                            "pointBorderWidth": 2,
                            "pointRadius": 5
                        }]
                    }

        # 3. GRÁFICA DE ALUMNOS (Calificación por alumno)
        alumnos = evento.get('alumnos_asignados', [])
        if alumnos and cuestionarios_detalle:
            # Preparar datos para la gráfica de alumnos
            alumnos_data = []
            labels_alumnos = []
            data_alumnos = []
            
            for alumno in alumnos:
                email = alumno.get('email')
                nombre = alumno.get('nombre', 'Sin nombre')
                
                # Buscar calificación del alumno
                calificacion = 0
                for cuestionario in cuestionarios_detalle:
                    if cuestionario.get('email') == email:
                        calificacion = cuestionario.get('calificacion', 0)
                        break
                
                # Acortar nombre largo para mejor visualización
                nombre_corto = nombre if len(nombre) <= 15 else nombre[:12] + "..."
                
                alumnos_data.append({
                    'nombre': nombre,
                    'email': email,
                    'calificacion': calificacion
                })
                labels_alumnos.append(nombre_corto)
                data_alumnos.append(calificacion)
            
            # Definir colores según el rango de calificación
            backgroundColors = []
            for calificacion in data_alumnos:
                if calificacion <= 50:
                    backgroundColors.append('#dc3545')
                elif calificacion <= 70:
                    backgroundColors.append('#ffc107')
                elif calificacion <= 80:
                    backgroundColors.append('#17a2b8')
                else:
                    backgroundColors.append('#28a745')
            
            if data_alumnos:
                datos_graficas["alumnos"] = {
                    "labels": labels_alumnos,
                    "datasets": [{
                        "label": "Calificación (%)",
                        "data": data_alumnos,
                        "backgroundColor": backgroundColors,
                        "borderColor": backgroundColors,
                        "borderWidth": 1,
                        "barPercentage": 0.6,
                        "categoryPercentage": 0.8
                    }]
                }

        return datos_graficas

    except Exception as e:
        print(f"ERROR en generar_datos_graficas: {str(e)}")
        return {
            'cuestionarios': None,
            'evaluaciones': None,
            'alumnos': None
        }




