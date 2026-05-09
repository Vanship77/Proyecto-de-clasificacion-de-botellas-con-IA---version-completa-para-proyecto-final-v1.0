# config.py - Configuración del proyecto

# Configuración de PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'database': 'reciclaje_ia',
    'user': 'postgres',
    'password': 'vanship77',  # CAMBIA ESTO por tu contraseña real
    'port': '5432'
}

# Configuración de la IA
IA_CONFIG = {
    'modelo_path': 'modelos_guardados/clasificador_botellas.h5',
    'tamano_imagen': (224, 224),
    'clases': ['plastico', 'vidrio', 'lata'],
    'umbral_confianza': 0.7
}

# Configuración de la API
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}

# Puntos por tipo de residuo
PUNTOS_POR_TIPO = {
    'plastico': 10,
    'vidrio': 15,
    'lata': 10
}