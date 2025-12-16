import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables del entorno
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-temporal'
    
    # Configuración de MongoDB desde variable de entorno
    MONGODB_URI = os.environ.get('MONGODB_URI') or "mongodb+srv://T4ll3r_HQ:T4ll3r_HQ@cluster0.7a1upj8.mongodb.net/exam_db?retryWrites=true&w=majority&appName=Cluster0"
    
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

ESCALA_EVALUACION = {
    1: "Muy mal",
    2: "Mal", 
    3: "Regular",
    4: "Bien",
    5: "Muy Bien",
    6: "Excelente"
}