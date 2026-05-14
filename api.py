# api.py - Servidor API para Arduino (con interfaz web)
from flask import Flask, request, jsonify, render_template  # ← AGREGADO render_template
import psycopg2
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os

app = Flask(__name__)

# ========== NUEVA RUTA PARA LA PÁGINA WEB ==========
@app.route('/')
def index():
    """Página principal con la interfaz web"""
    return render_template('index.html')

# ========== CONFIGURACIÓN ==========
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

# ========== ENDPOINTS PARA ARDUINO ==========

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

# ========== NUEVOS ENDPOINTS PARA LA INTERFAZ WEB ==========

@app.route('/ranking', methods=['GET'])
def ranking():
    """Obtiene el top 10 de usuarios con más puntos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(nombre, 'Usuario ' || id::text), puntos_totales, 
                   (SELECT COUNT(*) FROM registros_reciclaje WHERE id_usuario = u.id) as reciclajes
            FROM usuarios u
            ORDER BY puntos_totales DESC
            LIMIT 10
        """)
        ranking = [{'nombre': r[0], 'puntos': r[1], 'reciclajes': r[2] or 0} for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(ranking)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/estadisticas/<int:usuario_id>', methods=['GET'])
def estadisticas_usuario(usuario_id):
    """Obtiene estadísticas de un usuario específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COALESCE(nombre, 'Usuario ' || id::text),
                puntos_totales,
                (SELECT COUNT(*) FROM registros_reciclaje WHERE id_usuario = %s) as total_reciclajes,
                (SELECT COUNT(*) FROM registros_reciclaje r JOIN tipos_residuo t ON r.id_tipo_residuo = t.id WHERE r.id_usuario = %s AND t.nombre = 'plastico') as plasticos,
                (SELECT COUNT(*) FROM registros_reciclaje r JOIN tipos_residuo t ON r.id_tipo_residuo = t.id WHERE r.id_usuario = %s AND t.nombre = 'vidrio') as vidrios,
                (SELECT COUNT(*) FROM registros_reciclaje r JOIN tipos_residuo t ON r.id_tipo_residuo = t.id WHERE r.id_usuario = %s AND t.nombre = 'lata') as latas
            FROM usuarios u
            WHERE u.id = %s
        """, (usuario_id, usuario_id, usuario_id, usuario_id, usuario_id))
        
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if resultado:
            return jsonify({
                'nombre': resultado[0],
                'puntos_totales': resultado[1],
                'total_reciclajes': resultado[2] or 0,
                'plasticos': resultado[3] or 0,
                'vidrios': resultado[4] or 0,
                'latas': resultado[5] or 0
            })
        return jsonify({'error': 'Usuario no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 SERVIDOR API PARA ARDUINO")
    print("=" * 50)
    print("\n📌 Endpoints disponibles:")
    print("   GET  /                 - Interfaz web")
    print("   POST /reciclar         - Registrar reciclaje")
    print("   GET  /usuarios         - Listar usuarios")
    print("   POST /crear_usuario    - Crear usuario")
    print("   GET  /ranking          - Top 10 usuarios")
    print("   GET  /estadisticas/<id> - Estadísticas")
    print("\n🚀 Servidor en http://127.0.0.1:5000")
    print("🌍 Interfaz web en http://127.0.0.1:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)