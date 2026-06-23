# api.py - Servidor API con YOLO + MobileNet + Login + Roles + Sensor automático
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from functools import wraps
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
import cv2
from ultralytics import YOLO
import hashlib
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_muy_segura_123456789'  # CAMBIAR EN PRODUCCIÓN

# ========== CONFIGURACIÓN ==========
PUERTO_ARDUINO = 'COM3'
VELOCIDAD_ARDUINO = 9600
USUARIO_POR_DEFECTO = 1
TIPO_POR_DEFECTO = 'plastic'

DB_CONFIG = {
    'host': 'localhost',
    'database': 'reciclaje_ia',
    'user': 'postgres',
    'password': 'vanship77',
    'port': '5432'
}

# ========== FUNCIÓN DE HASH PARA CONTRASEÑAS ==========
def hash_contrasena(contrasena):
    """Genera un hash SHA-256 de la contraseña"""
    return hashlib.sha256(contrasena.encode()).hexdigest()

# ========== DECORADOR PARA VERIFICAR SESIÓN ==========
def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login_page'))
        if session.get('rol') != 'admin':
            return render_template('error.html', mensaje='Acceso denegado. Se requieren permisos de administrador.')
        return f(*args, **kwargs)
    return decorated_function

# ========== CARGAR MODELOS ==========
print("🔄 Cargando modelos...")
try:
    modelo_yolo = YOLO('yolov8n.pt')
    print("✅ YOLO cargado")
except:
    modelo_yolo = None
    print("⚠️ YOLO no disponible")

try:
    # Cargar EfficientNetB0
    modelo_efficientnet = tf.keras.models.load_model('modelos_guardados/clasificador_efficientnet.h5')
    print("✅ EfficientNetB0 cargado")
except:
    modelo_efficientnet = None
    print("⚠️ EfficientNetB0 no disponible")

CLASSES = ['glass', 'metal', 'plastic']
MAPEO = {'glass': 'vidrio', 'metal': 'lata', 'plastic': 'plastico'}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ========== FUNCIONES DE DETECCIÓN ==========
def detectar_y_recortar_botella(imagen_cv2):
    if modelo_yolo is None:
        return imagen_cv2
    
    h, w = imagen_cv2.shape[:2]
    if w > 640:
        escala = 640 / w
        imagen_cv2 = cv2.resize(imagen_cv2, (640, int(h * escala)))
    
    resultados = modelo_yolo(imagen_cv2, verbose=False)
    mejor_botella = None
    mejor_confianza = 0
    
    for caja in resultados[0].boxes:
        clase = int(caja.cls[0])
        confianza = float(caja.conf[0])
        if clase == 39 and confianza > 0.5 and confianza > mejor_confianza:
            mejor_confianza = confianza
            x1, y1, x2, y2 = map(int, caja.xyxy[0])
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(imagen_cv2.shape[1], x2), min(imagen_cv2.shape[0], y2)
            mejor_botella = imagen_cv2[y1:y2, x1:x2]
    
    return mejor_botella

def preprocesar_para_mobilenet(imagen_cv2):
    img_rgb = cv2.cvtColor(imagen_cv2, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (224, 224))
    img_array = np.array(img_resized) / 255.0
    return np.expand_dims(img_array, axis=0)

# ========== FUNCIÓN PARA ARDUINO ==========
def leer_arduino():
    try:
        arduino = serial.Serial(PUERTO_ARDUINO, VELOCIDAD_ARDUINO, timeout=1)
        time.sleep(2)
        print(f"✅ Conectado a Arduino en {PUERTO_ARDUINO}")

        while True:
            if arduino.in_waiting > 0:
                linea = arduino.readline().decode('utf-8').strip()
                print(f"📨 Arduino: {linea}")
                
                if linea == "BOTELLA_DETECTADA":
                    print("🔴 ¡Botella detectada!")
                    datos = {"usuario_id": USUARIO_POR_DEFECTO, "tipo": TIPO_POR_DEFECTO, "confianza": 99.9}
                    try:
                        r = requests.post('http://127.0.0.1:5000/reciclar', json=datos)
                        if r.status_code == 200:
                            data = r.json()
                            print(f"✅ +{data.get('puntos_ganados', 0)} pts")
                    except:
                        pass
            time.sleep(0.1)
    except:
        print(f"❌ No se pudo conectar a Arduino en {PUERTO_ARDUINO}")

# ========== RUTAS DE AUTENTICACIÓN ==========
@app.route('/login')
def login_page():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/registro')
def registro_page():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('registro.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        datos = request.get_json()
        email = datos.get('email')
        contrasena = datos.get('contrasena')
        
        if not email or not contrasena:
            return jsonify({'error': 'Email y contraseña requeridos'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, email, contrasena, rol, puntos_totales
            FROM usuarios WHERE email = %s
        """, (email,))
        usuario = cursor.fetchone()
        conn.close()
        
        if not usuario:
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        contrasena_hash = hash_contrasena(contrasena)
        if usuario[3] != contrasena_hash:
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        session['usuario_id'] = usuario[0]
        session['nombre'] = usuario[1]
        session['email'] = usuario[2]
        session['rol'] = usuario[4]
        session['puntos'] = usuario[5]
        
        return jsonify({
            'status': 'ok',
            'usuario': {
                'id': usuario[0],
                'nombre': usuario[1],
                'email': usuario[2],
                'rol': usuario[4],
                'puntos': usuario[5]
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/registro', methods=['POST'])
def api_registro():
    try:
        datos = request.get_json()
        nombre = datos.get('nombre')
        email = datos.get('email')
        contrasena = datos.get('contrasena')
        
        if not nombre or not email or not contrasena:
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        
        if len(contrasena) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        contrasena_hash = hash_contrasena(contrasena)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, contrasena, rol, puntos_totales)
            VALUES (%s, %s, %s, 'usuario', 0) RETURNING id
        """, (nombre, email, contrasena_hash))
        
        usuario_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'ok', 'mensaje': 'Usuario registrado', 'id': usuario_id}), 201
    except Exception as e:
        if 'duplicate key' in str(e).lower():
            return jsonify({'error': 'El email ya está registrado'}), 400
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ========== RUTAS DE INTERFAZ ==========
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_requerido
def dashboard():
    return render_template('dashboard_usuario.html')

@app.route('/admin')
@admin_requerido
def admin_panel():
    return render_template('dashboard_admin.html')

# ========== ENDPOINTS EXISTENTES (CON PROTECCIÓN) ==========
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
        cursor.execute("SELECT id, nombre, puntos_totales, rol FROM usuarios WHERE rol != 'admin' ORDER BY nombre ASC")
        usuarios = [{'id': u[0], 'nombre': u[1], 'puntos': u[2], 'rol': u[3]} for u in cursor.fetchall()]
        conn.close()
        return jsonify(usuarios), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/crear_usuario', methods=['POST'])
@admin_requerido
def crear_usuario():
    try:
        datos = request.get_json()
        nombre = datos.get('nombre')
        email = datos.get('email')
        contrasena = datos.get('contrasena', '123456')
        rol = datos.get('rol', 'usuario')
        
        if not nombre or not email:
            return jsonify({'error': 'Nombre y email requeridos'}), 400
        
        contrasena_hash = hash_contrasena(contrasena)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, contrasena, rol, puntos_totales)
            VALUES (%s, %s, %s, %s, 0) RETURNING id, puntos_totales
        """, (nombre, email, contrasena_hash, rol))
        
        usuario_id, puntos = cursor.fetchone()
        conn.commit()
        conn.close()
        
        return jsonify({'id': usuario_id, 'nombre': nombre, 'puntos': puntos, 'rol': rol}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ranking', methods=['GET'])
def ranking():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, puntos_totales, 
                   (SELECT COUNT(*) FROM registros_reciclaje WHERE id_usuario = u.id) as reciclajes
            FROM usuarios u
            WHERE u.rol != 'admin'
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
        return jsonify({'error': str(e)}), 500

@app.route('/eliminar_usuario/<int:usuario_id>', methods=['DELETE'])
@admin_requerido
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
@admin_requerido
def eliminar_todos_usuarios():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol != 'admin'")
        total_usuarios = cursor.fetchone()[0]
        
        if total_usuarios == 0:
            conn.close()
            return jsonify({
                'status': 'ok',
                'mensaje': 'No hay usuarios para eliminar (el admin no se elimina)'
            }), 200
        
        cursor.execute("DELETE FROM registros_reciclaje WHERE id_usuario IN (SELECT id FROM usuarios WHERE rol != 'admin')")
        cursor.execute("DELETE FROM usuarios WHERE rol != 'admin'")
        
        cursor.execute("ALTER SEQUENCE usuarios_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE registros_reciclaje_id_seq RESTART WITH 1")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'mensaje': f'Se eliminaron {total_usuarios} usuarios'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clasificar_webcam', methods=['POST'])
def clasificar_webcam():
    try:
        from PIL import Image
        import io

        if 'imagen' not in request.files:
            return jsonify({'error': 'No se recibió imagen'}), 400
        
        usuario_id = request.form.get('usuario_id')
        if not usuario_id:
            return jsonify({'error': 'Usuario requerido'}), 400
        
        archivo = request.files['imagen']
        imagen_bytes = archivo.read()
        nparr = np.frombuffer(imagen_bytes, np.uint8)
        img_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_cv2 is None:
            return jsonify({'error': 'No se pudo procesar'}), 400
        
        recorte = detectar_y_recortar_botella(img_cv2)
        
        if recorte is None:
            return jsonify({
                'status': 'error',
                'error': 'no_bottle',
                'mensaje': '📷 No se detectó ninguna botella'
            }), 200
        
        h, w = recorte.shape[:2]
        if h < 30 or w < 30:
            return jsonify({
                'status': 'error',
                'error': 'bottle_too_small',
                'mensaje': '🔍 Botella muy pequeña'
            }), 200
        
        if modelo_efficientnet is None:
            return jsonify({'error': 'Modelo no cargado'}), 500
        
        img_efficientnet  = preprocesar_para_mobilenet(recorte)
        prediccion = modelo_efficientnet.predict(img_efficientnet, verbose=0)
        clase_idx = np.argmax(prediccion[0])
        confianza = float(prediccion[0][clase_idx]) * 100
        clase = CLASSES[clase_idx]
        
        tipo_es = MAPEO.get(clase, clase)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT puntos_base FROM tipos_residuo WHERE nombre = %s", (tipo_es,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return jsonify({'error': 'Tipo no válido'}), 400
        
        puntos = resultado[0]
        
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
        
        mapa_nombres = {'glass': 'VIDRIO', 'metal': 'LATA', 'plastic': 'PLÁSTICO'}
        
        return jsonify({
            'status': 'ok',
            'tipo': clase,
            'tipo_es': tipo_es,
            'tipo_nombre': mapa_nombres.get(clase, tipo_es.upper()),
            'confianza': round(confianza, 2),
            'puntos': puntos,
            'puntos_totales': nuevos_puntos
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/estado_sensor', methods=['GET'])
def estado_sensor():
    return jsonify({
        'conectado': True,
        'usuario_id': USUARIO_POR_DEFECTO,
        'tipo': TIPO_POR_DEFECTO,
        'tipo_nombre': MAPEO.get(TIPO_POR_DEFECTO, TIPO_POR_DEFECTO)
    }), 200

@app.route('/mi_perfil', methods=['GET'])
@login_requerido
def mi_perfil():
    return jsonify({
        'id': session.get('usuario_id'),
        'nombre': session.get('nombre'),
        'email': session.get('email'),
        'rol': session.get('rol'),
        'puntos': session.get('puntos')
    }), 200

# ========== INICIO DEL SERVIDOR ==========
if __name__ == '__main__':
    print("=" * 50)
    print("🌐 SERVICIO DE RECICLAJE INTELIGENTE")
    print("=" * 50)
    print(f"🔌 Arduino: {PUERTO_ARDUINO}")
    print(f"🚀 Servidor: http://127.0.0.1:5000")
    print("=" * 50)
    
    try:
        hilo_arduino = threading.Thread(target=leer_arduino, daemon=True)
        hilo_arduino.start()
    except:
        print("⚠️ Arduino no disponible")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)