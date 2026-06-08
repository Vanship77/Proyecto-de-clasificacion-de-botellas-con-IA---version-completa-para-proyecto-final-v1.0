# api.py - Servidor API con YOLO + MobileNet
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
import cv2  # OpenCV para procesar imágenes
from ultralytics import YOLO  # YOLO para detectar botellas

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

# ========== CARGAR MODELO YOLO (detector de objetos) ==========
print("🔄 Cargando modelo YOLO...")
try:
    modelo_yolo = YOLO('yolov8n.pt')  # Modelo nano (rápido y liviano)
    print("✅ Modelo YOLO cargado correctamente")
except Exception as e:
    print(f"⚠️ No se pudo cargar YOLO: {e}")
    modelo_yolo = None

# ========== CARGAR MODELO MOBILENET (clasificador de materiales) ==========
try:
    modelo_mobilenet = tf.keras.models.load_model('modelos_guardados/clasificador_botellas.h5')
    print("✅ Modelo MobileNet cargado correctamente")
except Exception as e:
    print(f"⚠️ No se pudo cargar el modelo: {e}")
    modelo_mobilenet = None

CLASSES = ['glass', 'metal', 'plastic']

MAPEO = {
    'glass': 'vidrio',
    'metal': 'lata',
    'plastic': 'plastico'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ========== FUNCIÓN PARA DETECTAR Y RECORTAR BOTELLA CON YOLO ==========
def detectar_y_recortar_botella(imagen_cv2):
    """
    Detecta si hay una botella en la imagen usando YOLO.
    Si encuentra una, devuelve el recorte de la botella.
    Si no, devuelve None.
    """
    if modelo_yolo is None:
        return None  # Si YOLO no está disponible, no filtramos
    
    # Redimensionar para YOLO (optimizar rendimiento)
    h, w = imagen_cv2.shape[:2]
    if w > 640:
        escala = 640 / w
        nuevo_w = 640
        nuevo_h = int(h * escala)
        imagen_cv2 = cv2.resize(imagen_cv2, (nuevo_w, nuevo_h))
    
    # Ejecutar YOLO
    resultados = modelo_yolo(imagen_cv2, verbose=False)
    
    # Buscar la mejor botella (clase 39 = 'bottle' en COCO)
    mejor_botella = None
    mejor_confianza = 0
    
    for caja in resultados[0].boxes:
        clase = int(caja.cls[0])
        confianza = float(caja.conf[0])
        
        if clase == 39 and confianza > 0.5:  # 39 = bottle, confianza > 50%
            if confianza > mejor_confianza:
                mejor_confianza = confianza
                x1, y1, x2, y2 = map(int, caja.xyxy[0])
                # Asegurar que las coordenadas estén dentro de la imagen
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(imagen_cv2.shape[1], x2), min(imagen_cv2.shape[0], y2)
                mejor_botella = imagen_cv2[y1:y2, x1:x2]
    
    if mejor_botella is not None:
        print(f"🎯 Botella detectada con confianza: {mejor_confianza:.2f}")
        return mejor_botella
    else:
        print("❌ No se detectó ninguna botella en la imagen")
        return None

def preprocesar_para_mobilenet(imagen_cv2):
    """Convierte una imagen de OpenCV al formato que espera MobileNet"""
    # Convertir de BGR (OpenCV) a RGB
    img_rgb = cv2.cvtColor(imagen_cv2, cv2.COLOR_BGR2RGB)
    # Redimensionar a 224x224 (tamaño que espera MobileNet)
    img_resized = cv2.resize(img_rgb, (224, 224))
    # Normalizar y expandir dimensiones
    img_array = np.array(img_resized) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

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

# ========== ENDPOINT MEJORADO CON YOLO + MOBILENET ==========
@app.route('/clasificar_webcam', methods=['POST'])
def clasificar_webcam():
    """Clasifica una imagen usando YOLO (detección) + MobileNet (clasificación)"""
    try:
        if 'imagen' not in request.files:
            return jsonify({'error': 'No se recibió ninguna imagen'}), 400
        
        usuario_id = request.form.get('usuario_id')
        if not usuario_id:
            return jsonify({'error': 'ID de usuario requerido'}), 400
        
        # Leer la imagen
        archivo = request.files['imagen']
        imagen_bytes = archivo.read()
        
        # Convertir a formato OpenCV (para YOLO)
        nparr = np.frombuffer(imagen_bytes, np.uint8)
        img_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_cv2 is None:
            return jsonify({'error': 'No se pudo procesar la imagen'}), 400
        
        # ========== PASO 1: DETECTAR BOTELLA CON YOLO ==========
        recorte_botella = detectar_y_recortar_botella(img_cv2)
        
        if recorte_botella is None:
            # No se detectó ninguna botella
            return jsonify({
                'status': 'error',
                'error': 'no_bottle',
                'mensaje': '📷 No se detectó ninguna botella. Acerca la botella a la cámara, sin otros objetos.'
            }), 200  # 200 para que el frontend lo maneje como error amigable
        
        # Verificar que el recorte tenga un tamaño mínimo
        h, w = recorte_botella.shape[:2]
        if h < 30 or w < 30:
            return jsonify({
                'status': 'error',
                'error': 'bottle_too_small',
                'mensaje': '🔍 La botella se ve muy pequeña. Acércate más.'
            }), 200
        
        # ========== PASO 2: CLASIFICAR MATERIAL CON MOBILENET ==========
        if modelo_mobilenet is None:
            return jsonify({'error': 'Modelo no cargado'}), 500
        
        img_para_mobilenet = preprocesar_para_mobilenet(recorte_botella)
        prediccion = modelo_mobilenet.predict(img_para_mobilenet, verbose=0)
        clase_idx = np.argmax(prediccion[0])
        confianza = float(prediccion[0][clase_idx]) * 100
        clase = CLASSES[clase_idx]
        
        # ========== PASO 3: REGISTRAR EN BASE DE DATOS ==========
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
        
        print(f"✅ Clasificado: {tipo_es} con {confianza:.1f}% confianza")
        
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
        print(f"❌ Error en clasificar_webcam: {e}")
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
    print("🌐 SERVIDOR API CON YOLO + MOBILENET")
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
    print("   POST /clasificar_webcam - Clasificar con YOLO + MobileNet")
    print("\n🔌 Configuración del sensor infrarrojo:")
    print(f"   Puerto Arduino: {PUERTO_ARDUINO}")
    print(f"   Usuario por defecto: {USUARIO_POR_DEFECTO}")
    print(f"   Tipo por defecto: {TIPO_POR_DEFECTO} ({MAPEO.get(TIPO_POR_DEFECTO, TIPO_POR_DEFECTO)})")
    print("\n🚀 Servidor en http://127.0.0.1:5000")
    print("🌍 Interfaz web en http://127.0.0.1:5000")
    print("=" * 50)
    
    try:
        hilo_arduino = threading.Thread(target=leer_arduino, daemon=True)
        hilo_arduino.start()
    except Exception as e:
        print(f"⚠️ No se pudo iniciar hilo de Arduino: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)