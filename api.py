# api.py - Servidor API para Arduino (versión simplificada)
from flask import Flask, request, jsonify
import psycopg2
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os

app = Flask(__name__)

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'reciclaje_ia',
    'user': 'postgres',
    'password': 'vanship77',
    'port': '5432'
}

# Cargar modelo entrenado
modelo = tf.keras.models.load_model('modelos_guardados/clasificador_botellas.h5')
CLASSES = ['glass', 'metal', 'plastic']

# Mapeo de clases en inglés a español
MAPEO = {
    'glass': 'vidrio',
    'metal': 'lata',
    'plastic': 'plastico'
}

def get_db_connection():
    """Retorna una conexión a la base de datos"""
    return psycopg2.connect(**DB_CONFIG)

@app.route('/reciclar', methods=['POST'])
def registrar_reciclaje():
    """Endpoint para que Arduino registre un reciclaje"""
    try:
        datos = request.get_json()
        usuario_id = datos.get('usuario_id')
        tipo_ia = datos.get('tipo')
        confianza = datos.get('confianza', 0.95)
        
        if not usuario_id or not tipo_ia:
            return jsonify({'error': 'Faltan datos'}), 400
        
        tipo_es = MAPEO.get(tipo_ia, tipo_ia)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, puntos_base FROM tipos_residuo WHERE nombre = %s", (tipo_es,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return jsonify({'error': 'Tipo no válido'}), 400
        
        tipo_id, puntos = resultado
        
        cursor.execute("""
            INSERT INTO registros_reciclaje (id_usuario, id_tipo_residuo, puntos_ganados, confianza_ia)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (usuario_id, tipo_id, puntos, confianza))
        
        cursor.execute("""
            UPDATE usuarios SET puntos_totales = puntos_totales + %s
            WHERE id = %s RETURNING puntos_totales
        """, (puntos, usuario_id))
        
        nuevos_puntos = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'mensaje': f'Ganaste {puntos} puntos',
            'puntos_ganados': puntos,
            'puntos_totales': nuevos_puntos
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, puntos_totales FROM usuarios ORDER BY puntos_totales DESC")
        usuarios = [{'id': u[0], 'nombre': u[1], 'puntos': u[2]} for u in cursor.fetchall()]
        conn.close()
        return jsonify(usuarios), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/crear_usuario', methods=['POST'])
def crear_usuario():
    try:
        datos = request.get_json()
        nombre = datos.get('nombre')
        email = datos.get('email')
        
        if not nombre or not email:
            return jsonify({'error': 'Nombre y email requeridos'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, puntos_totales)
            VALUES (%s, %s, 0) RETURNING id, puntos_totales
        """, (nombre, email))
        
        usuario_id, puntos = cursor.fetchone()
        conn.commit()
        conn.close()
        
        return jsonify({'id': usuario_id, 'nombre': nombre, 'puntos': puntos}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 SERVIDOR API PARA ARDUINO")
    print("=" * 50)
    print("\n📌 Endpoints:")
    print("   POST /reciclar - Registrar reciclaje")
    print("   GET /usuarios - Listar usuarios")
    print("   POST /crear_usuario - Crear usuario")
    print("\n🚀 Servidor en http://127.0.0.1:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)