# config.py - Configuración del proyecto

# Configuración de PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'database': 'reciclaje_ia',
    'user': 'postgres',
    'password': 'vanship77',  # CAMBIA ESTO por tu contraseña real
    'port': '5432'
}

# Configuración de la IA (EfficientNetB0)
IA_CONFIG = {
    'modelo_path': 'modelo_residuos.keras',  # <--- CAMBIADO
    'modelo_path_backup': 'modelos_guardados/clasificador_efficientnet.keras',
    'tamano_imagen': (224, 224),
    'clases': ['glass', 'metal', 'plastic'],  # <--- CAMBIADO (inglés)
    'clases_es': {'glass': 'vidrio', 'metal': 'lata', 'plastic': 'plastico'},  # <--- NUEVO
    'clases_display': {'glass': 'VIDRIO', 'metal': 'LATA', 'plastic': 'PLÁSTICO'},  # <--- NUEVO
    'umbral_confianza': 0.75  # <--- CAMBIADO (de 0.7 a 0.75)
}

# Configuración de la API
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}

# Puntos por tipo de residuo (en español, para la BD)
PUNTOS_POR_TIPO = {
    'plastico': 10,
    'vidrio': 15,
    'lata': 10
}