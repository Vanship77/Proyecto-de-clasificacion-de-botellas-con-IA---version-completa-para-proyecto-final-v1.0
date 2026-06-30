# api.py - Servidor API con EfficientNetB0 + Login + Roles + Sensor automático
# CON FILTRO DE FORMA MEJORADO - Detecta solo botellas
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from functools import wraps
import psycopg2
import psycopg2.extras
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input
import numpy as np
import os
import serial
import threading
import time
import requests
from PIL import Image
import io
import cv2
import hashlib
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_muy_segura_123456789'

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
    return hashlib.sha256(contrasena.encode()).hexdigest()

# ========== DECORADORES ==========
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

# ========== CARGAR MODELO EFFICIENTNETB0 ==========
print("🔄 Cargando modelo EfficientNetB0...")

rutas_modelo = [
    'modelo_residuos.keras',
    'modelos_guardados/clasificador_efficientnet.keras'
]

modelo_efficientnet = None
for ruta in rutas_modelo:
    if os.path.exists(ruta):
        try:
            modelo_efficientnet = tf.keras.models.load_model(ruta)
            print(f"✅ EfficientNetB0 cargado desde: {ruta}")
            break
        except Exception as e:
            print(f"⚠️ Error cargando {ruta}: {e}")

if modelo_efficientnet is None:
    print("❌ No se encontró modelo EfficientNetB0")
    print("   Ejecuta: python entrenar_modelo.py")

CLASSES = ['glass', 'metal', 'plastic']
MAPEO = {'glass': 'vidrio', 'metal': 'lata', 'plastic': 'plastico'}
MAPEO_DISPLAY = {'glass': 'VIDRIO', 'metal': 'LATA', 'plastic': 'PLÁSTICO'}

# ========== CONEXIÓN A BD CON UTF-8 ==========
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    return conn

# ========== FUNCIONES DE CLASIFICACIÓN ==========
def preprocesar_para_efficientnet(imagen_cv2):
    img_rgb = cv2.cvtColor(imagen_cv2, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (224, 224))
    img_array = np.array(img_resized, dtype=np.float32)
    img_array = preprocess_input(img_array)
    return np.expand_dims(img_array, axis=0)

def clasificar_botella(imagen_cv2):
    if modelo_efficientnet is None:
        return None, 0.0, None
    
    img_procesada = preprocesar_para_efficientnet(imagen_cv2)
    prediccion = modelo_efficientnet.predict(img_procesada, verbose=0)
    clase_idx = np.argmax(prediccion[0])
    confianza = float(prediccion[0][clase_idx]) * 100
    clase = CLASSES[clase_idx]
    
    return clase, confianza, prediccion[0]

# ========== FILTRO SUAVE PARA DETECTAR BOTELLAS (score, no gate duro) ========== 
def es_botella(imagen_cv2):
    """Devuelve un score 0..1 de probabilidad por forma (sin hard-reject).

    Nota: antes se usaba un return True/False (gate duro). Eso era demasiado sensible
    a iluminación/distancia/ángulo. Ahora combinamos heurísticas con pesos.
    """
    try:
        h, w = imagen_cv2.shape[:2]
        if h < 20 or w < 20:
            return 0.0

        escala = 0.5
        img_proc = cv2.resize(imagen_cv2, (max(1, int(w * escala)), max(1, int(h * escala))))

        gray = cv2.cvtColor(img_proc, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0.0

        contorno = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contorno)
        area_imagen = float(img_proc.shape[0] * img_proc.shape[1])
        if area_imagen <= 0:
            return 0.0

        x, y, w_rect, h_rect = cv2.boundingRect(contorno)
        if w_rect <= 0 or h_rect <= 0:
            return 0.0

        porcentaje_area = area / area_imagen
        aspecto = h_rect / w_rect if w_rect > 0 else 0

        # 1) Área (ideal aprox 8%..40%)
        s_area = 1.0
        if porcentaje_area < 0.08:
            s_area = np.clip(porcentaje_area / 0.08, 0, 1)
        elif porcentaje_area > 0.40:
            s_area = np.clip((0.70 - porcentaje_area) / 0.30, 0, 1)

        # 2) Aspecto (botellas tienden a ser más altas que anchas)
        # score triangular entre 1.0..2.5..5.0 (máximo cerca de 3)
        if aspecto <= 1.0:
            s_aspecto = 0.0
        else:
            s_aspecto = np.clip((aspecto - 1.0) / (2.5 - 1.0), 0, 1)
            # caer si se va demasiado (manos cercanas o fondo)
            if aspecto > 5.0:
                s_aspecto *= 0.2

        # 3) Circularidad (una mano/persona puede ser más “redonda” por proximidad)
        perimetro = cv2.arcLength(contorno, True)
        if perimetro <= 0:
            s_circ = 0.0
        else:
            circularidad = 4 * np.pi * area / (perimetro * perimetro)
            # circularidad alta (>=0.85) penaliza
            s_circ = 1.0 - np.clip((circularidad - 0.6) / 0.25, 0, 1)

        # 4) Contornos internos: manos suelen generar más “detalles”
        _, contours_inner, _ = cv2.findContours(edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        internos_grandes = 0
        if contours_inner:
            internos_grandes = sum(1 for c in contours_inner if cv2.contourArea(c) > 150)
        # penaliza si hay muchos internos
        s_internos = 1.0 - np.clip((internos_grandes - 1) / 4.0, 0, 1)

        # 5) Cuello: ancho superior no debería crecer demasiado vs ancho medio
        puntos_superiores = [p[0][0] for p in contorno if p[0][1] < y + h_rect * 0.25]
        s_cuello = 0.5
        if len(puntos_superiores) > 10:
            ancho_superior = float(max(puntos_superiores) - min(puntos_superiores))
            ancho_medio = float(w_rect) * 0.7
            # si ancho superior es significativamente mayor, penaliza
            ratio = ancho_superior / (ancho_medio + 1e-6)
            s_cuello = np.clip(1.0 - (ratio - 1.0) / 0.8, 0, 1)

        # Combinar (pesos suman ~1)
        score = (
            0.30 * s_area +
            0.30 * s_aspecto +
            0.15 * s_circ +
            0.15 * s_internos +
            0.10 * s_cuello
        )

        # penalización si área es demasiado pequeña
        if area < 250:
            score *= 0.5

        return float(np.clip(score, 0.0, 1.0))
    except Exception:
        return 0.0

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
                        r = requests.post('http://127.0.0.1:5000/reciclar', json=datos, timeout=2)
                        if r.status_code == 200:
                            data = r.json()
                            print(f"✅ +{data.get('puntos_ganados', 0)} pts")
                    except:
                        pass
            time.sleep(0.1)
    except Exception as e:
        print(f"⚠️ Arduino no disponible: {e}")

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
        
        print(f"🔍 Intentando login: {email}")
        
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
            print(f"❌ Usuario no encontrado: {email}")
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        contrasena_hash = hash_contrasena(contrasena)
        print(f"🔍 Hash ingresado: {contrasena_hash}")
        print(f"🔍 Hash en BD:     {usuario[3]}")
        
        if usuario[3] != contrasena_hash:
            print(f"❌ Contraseña incorrecta para: {email}")
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        
        print(f"✅ Login exitoso: {email}")
        
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
        print(f"❌ Error en login: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/registro', methods=['POST'])
def api_registro():
    try:
        datos = request.get_json()
        nombre = datos.get('nombre')
        email = datos.get('email')
        contrasena = datos.get('contrasena')
        
        print(f"📝 Registrando: {nombre}, {email}")
        
        if not nombre or not email or not contrasena:
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        
        if len(contrasena) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        contrasena_hash = hash_contrasena(contrasena)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, contrasena, rol, puntos_totales)
            VALUES (%s, %s, %s, 'usuario', 0) RETURNING id
        """, (nombre, email, contrasena_hash))
        
        usuario_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        print(f"✅ Usuario registrado: ID {usuario_id}")
        
        return jsonify({'status': 'ok', 'mensaje': 'Usuario registrado', 'id': usuario_id}), 201
        
    except Exception as e:
        print(f"❌ ERROR EN REGISTRO: {e}")
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
    return render_template('index.html')  

@app.route('/dashboard')
@login_requerido
def dashboard():
    return render_template('dashboard_usuario.html')

@app.route('/admin')
@admin_requerido
def admin_panel():
    return render_template('dashboard_admin.html')

# ========== ENDPOINTS ==========
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
    
@app.route('/actualizar_puntaje', methods=['POST'])
@admin_requerido
def actualizar_puntaje():
    try:
        datos = request.get_json()
        material = datos.get('material')
        puntos = datos.get('puntos')
        
        if not material or not puntos:
            return jsonify({'error': 'Faltan datos'}), 400
        
        if puntos < 1 or puntos > 100:
            return jsonify({'error': 'Los puntos deben estar entre 1 y 100'}), 400
        
        # Mapeo de nombres
        mapeo = {
            'plastico': 'plastico',
            'vidrio': 'vidrio',
            'lata': 'lata'
        }
        
        nombre_bd = mapeo.get(material)
        if not nombre_bd:
            return jsonify({'error': 'Material no válido'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tipos_residuo 
            SET puntos_base = %s 
            WHERE nombre = %s
        """, (puntos, nombre_bd))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'mensaje': f'Puntaje de {material} actualizado a {puntos} puntos'
        }), 200
        
    except Exception as e:
        print(f"❌ Error actualizando puntaje: {e}")
        return jsonify({'error': str(e)}), 500

# ========== ENDPOINT CLASIFICAR WEBCAM CON FILTRO MEJORADO ==========
@app.route('/clasificar_webcam', methods=['POST'])
def clasificar_webcam():
    """Clasifica una imagen usando EfficientNetB0 con filtro de forma mejorado"""
    try:
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
        
        # ========== FILTRO DE FORMA MEJORADO ==========
        # Score de forma (suave, no gate duro)
        score_forma = es_botella(img_cv2)
        if modelo_efficientnet is None:
            return jsonify({'error': 'Modelo no cargado'}), 500

        clase, confianza, _ = clasificar_botella(img_cv2)
        if clase is None:
            return jsonify({
                'status': 'error',
                'error': 'no_bottle',
                'mensaje': 'No se detectó ninguna botella'
            }), 200

        # Combinar evidencia de forma + IA
        # confianza viene en % (0..100)
        final_score = 0.7 * (confianza / 100.0) + 0.3 * float(score_forma)
        # Umbral (ajustable)
        if final_score < 0.55:
            return jsonify({
                'status': 'error',
                'error': 'no_bottle',
                'mensaje': 'No se detectó una botella con suficiente evidencia'
            }), 200

        if confianza < 50:
            return jsonify({
                'status': 'error',
                'error': 'baja_confianza',
                'mensaje': f'⚠️ Confianza baja: {confianza:.1f}%',
                'confianza': round(confianza, 2)
            }), 200
        
        if modelo_efficientnet is None:
            return jsonify({'error': 'Modelo no cargado'}), 500
        
        clase, confianza, _ = clasificar_botella(img_cv2)
        
        if clase is None:
            return jsonify({
                'status': 'error',
                'error': 'no_bottle',
                'mensaje': 'No se detectó ninguna botella'
            }), 200
        
        if confianza < 50:
            return jsonify({
                'status': 'error',
                'error': 'baja_confianza',
                'mensaje': f'⚠️ Confianza baja: {confianza:.1f}%',
                'confianza': round(confianza, 2)
            }), 200
        
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
        
        return jsonify({
            'status': 'ok',
            'tipo': clase,
            'tipo_es': tipo_es,
            'tipo_nombre': MAPEO_DISPLAY.get(clase, tipo_es.upper()),
            'confianza': round(confianza, 2),
            'puntos': puntos,
            'puntos_totales': nuevos_puntos,
            'modelo': 'EfficientNetB0'
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