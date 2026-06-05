# api.py - Servidor API para Arduino (con interfaz web y sensor infrarrojo)
from flask import Flask, request, jsonify, render_template
import psycopg2
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import serial
import threading
import time
import requests
from PIL import Image
import io

app = Flask(__name__)

# ========== CONFIGURACIÓN DEL PUERTO SERIAL PARA ARDUINO ==========
PUERTO_ARDUINO = 'COM3'
VELOCIDAD_ARDUINO = 9600
USUARIO_POR_DEFECTO = 1
TIPO_POR_DEFECTO = 'plastic'

# ========== CONFIGURACIÓN DE BASE DE DATOS ==========
DB_CONFIG = {
    'host': 'localhost',
    'database': 'reciclaje_ia',
    'user': 'postgres',
    'password': 'vanship77',
    'port': '5432'
}

# Cargar modelo entrenado
try:
    modelo = tf.keras.models.load_model('modelos_guardados/clasificador_botellas.h5')
    print("✅ Modelo de IA cargado correctamente")
except Exception as e:
    print(f"⚠️ No se pudo cargar el modelo: {e}")
    modelo = None

CLASSES = ['glass', 'metal', 'plastic']

MAPEO = {
    'glass': 'vidrio',
    'metal': 'lata',
    'plastic': 'plastico'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ========== RUTA PARA LA PÁGINA WEB ==========
@app.route('/')
def index():
    return render_template('index.html')

# ========== ENDPOINTS PARA ARDUINO ==========

@app.route('/reciclar', methods=['POST'])
def registrar_reciclaje():
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
            'puntos_totales': nuevos_puntos,
            'tipo': tipo_es
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, puntos_totales FROM usuarios ORDER BY nombre ASC")
        usuarios = [{'id': u[0], 'nombre': u[1], 'puntos': u[2]} for u in cursor.fetchall()]
        conn.close()
        print(f"📋 Usuarios encontrados: {len(usuarios)}")
        return jsonify(usuarios), 200
    except Exception as e:
        print(f"❌ Error en listar_usuarios: {e}")
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
        print(f"❌ Error en crear_usuario: {e}")
        return jsonify({'error': str(e)}), 500

# ========== ENDPOINTS PARA LA INTERFAZ WEB ==========

@app.route('/ranking', methods=['GET'])
def ranking():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, puntos_totales, 
                   (SELECT COUNT(*) FROM registros_reciclaje WHERE id_usuario = u.id) as reciclajes
            FROM usuarios u
            ORDER BY puntos_totales DESC
            LIMIT 10
        """)
        ranking = [{'nombre': r[0], 'puntos': r[1], 'reciclajes': r[2] or 0} for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(ranking), 200
    except Exception as e:
        print(f"Error en ranking: {e}")
        return jsonify({'error': str(e)}), 500

# ========== ENDPOINT DE ESTADÍSTICAS (AGREGADO) ==========
@app.route('/estadisticas/<int:usuario_id>', methods=['GET'])
def estadisticas_usuario(usuario_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                nombre,
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
        
        if resultado and resultado[0]:
            return jsonify({
                'nombre': resultado[0],
                'puntos_totales': resultado[1] or 0,
                'total_reciclajes': resultado[2] or 0,
                'plasticos': resultado[3] or 0,
                'vidrios': resultado[4] or 0,
                'latas': resultado[5] or 0
            })
        return jsonify({'error': 'Usuario no encontrado'}), 404
    except Exception as e:
        print(f"Error en estadisticas: {e}")
        return jsonify({'error': str(e)}), 500

# ========== ENDPOINTS PARA ELIMINAR USUARIOS ==========

@app.route('/eliminar_usuario/<int:usuario_id>', methods=['DELETE'])
def eliminar_usuario(usuario_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, nombre FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            conn.close()
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        nombre_usuario = usuario[1]
        
        cursor.execute("DELETE FROM registros_reciclaje WHERE id_usuario = %s", (usuario_id,))
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'mensaje': f'Usuario "{nombre_usuario}" (ID: {usuario_id}) eliminado correctamente'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/eliminar_todos_usuarios', methods=['DELETE'])
def eliminar_todos_usuarios():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cursor.fetchone()[0]
        
        if total_usuarios == 0:
            conn.close()
            return jsonify({
                'status': 'ok',
                'mensaje': 'No hay usuarios para eliminar'
            }), 200
        
        cursor.execute("DELETE FROM registros_reciclaje")
        cursor.execute("DELETE FROM usuarios")
        
        cursor.execute("ALTER SEQUENCE usuarios_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE registros_reciclaje_id_seq RESTART WITH 1")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'mensaje': f'Se eliminaron {total_usuarios} usuarios y todos sus reciclajes'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/configurar_sensor', methods=['POST'])
def configurar_sensor():
    try:
        datos = request.get_json()
        global USUARIO_POR_DEFECTO, TIPO_POR_DEFECTO
        
        if 'usuario_id' in datos:
            USUARIO_POR_DEFECTO = datos['usuario_id']
        if 'tipo' in datos and datos['tipo'] in ['plastic', 'glass', 'metal']:
            TIPO_POR_DEFECTO = datos['tipo']
        
        return jsonify({
            'status': 'ok',
            'mensaje': 'Configuración actualizada',
            'usuario_id': USUARIO_POR_DEFECTO,
            'tipo': TIPO_POR_DEFECTO
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/estado_sensor', methods=['GET'])
def estado_sensor():
    return jsonify({
        'conectado': True,
        'usuario_id': USUARIO_POR_DEFECTO,
        'tipo': TIPO_POR_DEFECTO,
        'tipo_nombre': MAPEO.get(TIPO_POR_DEFECTO, TIPO_POR_DEFECTO)
    }), 200

# ========== ENDPOINT PARA CLASIFICAR CON CÁMARA WEB ==========
@app.route('/clasificar_webcam', methods=['POST'])
def clasificar_webcam():
    """Clasifica una imagen enviada desde la webcam"""
    try:
        if 'imagen' not in request.files:
            return jsonify({'error': 'No se recibió ninguna imagen'}), 400
        
        usuario_id = request.form.get('usuario_id')
        if not usuario_id:
            return jsonify({'error': 'ID de usuario requerido'}), 400
        
        # Leer la imagen
        archivo = request.files['imagen']
        imagen_bytes = archivo.read()
        
        # Convertir a formato que TensorFlow pueda procesar
        img = Image.open(io.BytesIO(imagen_bytes))
        img = img.convert('RGB')
        img = img.resize((224, 224))
        
        # Convertir a array
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        # Predecir con el modelo
        if modelo is None:
            return jsonify({'error': 'Modelo no cargado. Entrena primero el modelo.'}), 500
        
        prediccion = modelo.predict(img_array, verbose=0)
        clase_idx = np.argmax(prediccion[0])
        confianza = float(prediccion[0][clase_idx]) * 100
        clase = CLASSES[clase_idx]
        
        # Obtener puntos
        tipo_es = MAPEO.get(clase, clase)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT puntos_base FROM tipos_residuo WHERE nombre = %s", (tipo_es,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return jsonify({'error': 'Tipo no válido'}), 400
        
        puntos = resultado[0]
        
        # Registrar reciclaje
        cursor.execute("""
            INSERT INTO registros_reciclaje (id_usuario, id_tipo_residuo, puntos_ganados, confianza_ia)
            VALUES (%s, (SELECT id FROM tipos_residuo WHERE nombre = %s), %s, %s) RETURNING id
        """, (usuario_id, tipo_es, puntos, confianza / 100))
        
        cursor.execute("""
            UPDATE usuarios SET puntos_totales = puntos_totales + %s
            WHERE id = %s RETURNING puntos_totales
        """, (puntos, usuario_id))
        
        nuevos_puntos = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        # Mapear nombre para mostrar
        mapa_nombres = {'glass': 'VIDRIO', 'metal': 'LATA', 'plastic': 'PLÁSTICO'}
        
        return jsonify({
            'status': 'ok',
            'tipo': clase,
            'tipo_es': tipo_es,
            'tipo_nombre': mapa_nombres.get(clase, tipo_es.upper()),
            'confianza': round(confianza, 2),
            'puntos': puntos,
            'puntos_totales': nuevos_puntos,
            'mensaje': f'Botella de {tipo_es} detectada con {confianza:.1f}% de confianza'
        }), 200
        
    except Exception as e:
        print(f"Error en clasificar_webcam: {e}")
        return jsonify({'error': str(e)}), 500

# ========== FUNCIÓN PARA LEER EL ARDUINO EN SEGUNDO PLANO ==========
def leer_arduino():
    try:
        arduino = serial.Serial(PUERTO_ARDUINO, VELOCIDAD_ARDUINO, timeout=1)
        time.sleep(2)
        print(f"✅ Conectado a Arduino en {PUERTO_ARDUINO}")
        print("📡 Escuchando al sensor infrarrojo...")

        while True:
            if arduino.in_waiting > 0:
                linea = arduino.readline().decode('utf-8').strip()
                print(f"📨 Mensaje recibido: {linea}")
                
                if linea == "BOTELLA_DETECTADA":
                    print("🔴 ¡Botella detectada por sensor infrarrojo!")
                    
                    datos_reciclaje = {
                        "usuario_id": USUARIO_POR_DEFECTO,
                        "tipo": TIPO_POR_DEFECTO,
                        "confianza": 99.9
                    }
                    
                    try:
                        response = requests.post('http://127.0.0.1:5000/reciclar', json=datos_reciclaje)
                        if response.status_code == 200:
                            data = response.json()
                            print(f"✅ Reciclaje registrado exitosamente!")
                            print(f"   📦 Tipo: {data.get('tipo', TIPO_POR_DEFECTO)}")
                            print(f"   ⭐ Puntos ganados: {data.get('puntos_ganados', 0)}")
                            print(f"   🏆 Total acumulado: {data.get('puntos_totales', 0)}")
                        else:
                            print(f"❌ Error al registrar reciclaje: {response.status_code}")
                    except requests.exceptions.ConnectionError:
                        print("❌ Error: No se pudo conectar al servidor Flask")
                    except Exception as e:
                        print(f"❌ Error inesperado: {e}")
            
            time.sleep(0.1)

    except serial.SerialException:
        print(f"❌ No se pudo conectar al Arduino en el puerto {PUERTO_ARDUINO}")
        print("   Verifica la conexión y el puerto")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

# ========== INICIO DEL SERVIDOR ==========
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
    print("   DELETE /eliminar_usuario/<id> - Eliminar usuario")
    print("   DELETE /eliminar_todos_usuarios - Eliminar todos")
    print("   POST /configurar_sensor - Configurar sensor")
    print("   GET  /estado_sensor    - Estado del sensor")
    print("   POST /clasificar_webcam - Clasificar desde cámara")
    print("\n🔌 Configuración del sensor infrarrojo:")
    print(f"   Puerto Arduino: {PUERTO_ARDUINO}")
    print(f"   Usuario por defecto: {USUARIO_POR_DEFECTO}")
    print(f"   Tipo por defecto: {TIPO_POR_DEFECTO} ({MAPEO.get(TIPO_POR_DEFECTO, TIPO_POR_DEFECTO)})")
    print("\n🚀 Servidor en http://127.0.0.1:5000")
    print("🌍 Interfaz web en http://127.0.0.1:5000")
    print("=" * 50)
    print("\n📡 Iniciando comunicación con Arduino...")
    
    try:
        hilo_arduino = threading.Thread(target=leer_arduino, daemon=True)
        hilo_arduino.start()
    except Exception as e:
        print(f"⚠️ No se pudo iniciar hilo de Arduino: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)