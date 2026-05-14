# src/api/servidor.py
from flask import Flask, request, jsonify
from src.bd.conexion import Database
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os

app = Flask(__name__)

# Cargar modelo entrenado
modelo = tf.keras.models.load_model('modelos_guardados/clasificador_botellas.h5')
CLASSES = ['glass', 'metal', 'plastic']

# Mapeo de clases en inglés a español
MAPEO = {
    'glass': 'vidrio',
    'metal': 'lata',
    'plastic': 'plastico'
}

# Conectar a la base de datos
db = Database()
db.conectar()

@app.route('/reciclar', methods=['POST'])
def registrar_reciclaje():
    """
    Endpoint para que Arduino registre un reciclaje
    Ejemplo de llamada:
    POST /reciclar
    {
        "usuario_id": 1,
        "tipo": "plastic",
        "confianza": 0.95
    }
    """
    try:
        datos = request.get_json()
        usuario_id = datos.get('usuario_id')
        tipo_ia = datos.get('tipo')  # glass, metal, plastic
        confianza = datos.get('confianza', 0.95)
        
        if not usuario_id or not tipo_ia:
            return jsonify({'error': 'Faltan datos: usuario_id y tipo son requeridos'}), 400
        
        # Mapear a español
        tipo_es = MAPEO.get(tipo_ia, tipo_ia)
        
        # Buscar puntos del tipo de residuo
        cursor = db.conn.cursor()
        cursor.execute("SELECT id, puntos_base FROM tipos_residuo WHERE nombre = %s", (tipo_es,))
        resultado = cursor.fetchone()
        
        if not resultado:
            return jsonify({'error': f'Tipo de residuo {tipo_es} no válido'}), 400
        
        tipo_id, puntos = resultado
        
        # Insertar registro
        cursor.execute("""
            INSERT INTO registros_reciclaje (id_usuario, id_tipo_residuo, puntos_ganados, confianza_ia)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (usuario_id, tipo_id, puntos, confianza))
        
        registro_id = cursor.fetchone()[0]
        
        # Actualizar puntos del usuario
        cursor.execute("""
            UPDATE usuarios SET puntos_totales = puntos_totales + %s
            WHERE id = %s
            RETURNING puntos_totales
        """, (puntos, usuario_id))
        
        nuevos_puntos = cursor.fetchone()[0]
        db.conn.commit()
        
        return jsonify({
            'status': 'ok',
            'mensaje': f'¡Reciclaste {tipo_es}! Ganaste {puntos} puntos',
            'puntos_ganados': puntos,
            'puntos_totales': nuevos_puntos
        }), 200
        
    except Exception as e:
        db.conn.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    """Obtener lista de usuarios con sus puntos"""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, nombre, puntos_totales 
            FROM usuarios 
            ORDER BY puntos_totales DESC
        """)
        usuarios = [
            {'id': u[0], 'nombre': u[1], 'puntos': u[2]}
            for u in cursor.fetchall()
        ]
        return jsonify(usuarios), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/usuario/<int:usuario_id>', methods=['GET'])
def obtener_usuario(usuario_id):
    """Obtener información de un usuario específico"""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, nombre, email, puntos_totales, fecha_registro
            FROM usuarios 
            WHERE id = %s
        """, (usuario_id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'id': usuario[0],
            'nombre': usuario[1],
            'email': usuario[2],
            'puntos': usuario[3],
            'fecha_registro': usuario[4]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ranking', methods=['GET'])
def ranking():
    """Top 10 usuarios con más puntos"""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT u.nombre, u.puntos_totales, COUNT(r.id) as reciclajes
            FROM usuarios u
            LEFT JOIN registros_reciclaje r ON u.id = r.id_usuario
            GROUP BY u.id, u.nombre, u.puntos_totales
            ORDER BY u.puntos_totales DESC
            LIMIT 10
        """)
        ranking = [
            {'nombre': r[0], 'puntos': r[1], 'reciclajes': r[2] or 0}
            for r in cursor.fetchall()
        ]
        return jsonify(ranking), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/crear_usuario', methods=['POST'])
def crear_usuario():
    """Crear un nuevo usuario"""
    try:
        datos = request.get_json()
        nombre = datos.get('nombre')
        email = datos.get('email')
        
        if not nombre or not email:
            return jsonify({'error': 'Nombre y email son requeridos'}), 400
        
        cursor = db.conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, puntos_totales)
            VALUES (%s, %s, 0)
            RETURNING id, puntos_totales
        """, (nombre, email))
        
        usuario_id, puntos = cursor.fetchone()
        db.conn.commit()
        
        return jsonify({
            'status': 'ok',
            'id': usuario_id,
            'nombre': nombre,
            'email': email,
            'puntos': puntos
        }), 201
    except Exception as e:
        db.conn.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 SERVIDOR API PARA ARDUINO")
    print("=" * 50)
    print("\n📌 Endpoints disponibles:")
    print("   POST   /reciclar     - Registrar reciclaje")
    print("   GET    /usuarios     - Listar usuarios")
    print("   GET    /usuario/<id> - Obtener usuario")
    print("   GET    /ranking      - Top 10 usuarios")
    print("   POST   /crear_usuario - Crear usuario")
    print("\n🚀 Servidor iniciado en http://127.0.0.1:5000")
    print("   Presiona Ctrl+C para detener")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)