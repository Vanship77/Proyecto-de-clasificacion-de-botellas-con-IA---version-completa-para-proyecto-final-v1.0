# src/ia/modelo_efficientnet.py
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input
import numpy as np
import os
import cv2

CLASS_NAMES = ['glass', 'metal', 'plastic']
MAPEO_ES = {'glass': 'vidrio', 'metal': 'lata', 'plastic': 'plastico'}
MAPEO_DISPLAY = {'glass': 'VIDRIO', 'metal': 'LATA', 'plastic': 'PLÁSTICO'}

class ClasificadorEfficientNet:
    def __init__(self, modelo_path=None):
        self.modelo = None
        self.class_names = CLASS_NAMES
        self.tamano = (224, 224)
        self.modelo_path = modelo_path or 'modelo_residuos.keras'
        self.cargar_modelo()
    
    def cargar_modelo(self):
        if os.path.exists(self.modelo_path):
            try:
                self.modelo = tf.keras.models.load_model(self.modelo_path)
                print(f"✅ Modelo cargado desde: {self.modelo_path}")
                return True
            except Exception as e:
                print(f"⚠️ Error: {e}")
        
        alt_path = 'modelos_guardados/clasificador_efficientnet.keras'
        if os.path.exists(alt_path):
            try:
                self.modelo = tf.keras.models.load_model(alt_path)
                self.modelo_path = alt_path
                print(f"✅ Modelo cargado desde: {alt_path}")
                return True
            except Exception as e:
                print(f"⚠️ Error: {e}")
        
        print("❌ No se encontró modelo. Ejecuta: python entrenar_modelo.py")
        return False
    
    def preprocesar_cv2(self, img_cv2):
        """Normaliza usando preprocess_input de EfficientNetB0"""
        img_rgb = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, self.tamano)
        img_array = np.array(img_resized, dtype=np.float32)
        img_array = preprocess_input(img_array)
        return np.expand_dims(img_array, axis=0)
    
    def preprocesar_archivo(self, ruta_imagen):
        img = image.load_img(ruta_imagen, target_size=self.tamano)
        img_array = image.img_to_array(img)
        img_array = img_array.astype(np.float32)
        img_array = preprocess_input(img_array)
        return np.expand_dims(img_array, axis=0)
    
    def predecir(self, img_cv2, umbral=0.75):
        if self.modelo is None:
            raise ValueError("Modelo no cargado")
        
        img_procesada = self.preprocesar_cv2(img_cv2)
        prediccion = self.modelo.predict(img_procesada, verbose=0)
        indice = np.argmax(prediccion[0])
        confianza = float(prediccion[0][indice])
        clase = self.class_names[indice]
        
        if confianza < umbral:
            return {
                'clase': 'desconocido',
                'clase_es': 'desconocido',
                'clase_display': 'DESCONOCIDO',
                'confianza': confianza * 100,
                'probabilidades': {
                    c: float(prediccion[0][i]) * 100 
                    for i, c in enumerate(self.class_names)
                }
            }
        
        return {
            'clase': clase,
            'clase_es': MAPEO_ES.get(clase, clase),
            'clase_display': MAPEO_DISPLAY.get(clase, clase.upper()),
            'confianza': confianza * 100,
            'probabilidades': {
                c: float(prediccion[0][i]) * 100 
                for i, c in enumerate(self.class_names)
            }
        }
    
    def predecir_archivo(self, ruta_imagen, umbral=0.75):
        if self.modelo is None:
            raise ValueError("Modelo no cargado")
        if not os.path.exists(ruta_imagen):
            return {'error': f'Archivo no encontrado: {ruta_imagen}'}
        
        img_procesada = self.preprocesar_archivo(ruta_imagen)
        prediccion = self.modelo.predict(img_procesada, verbose=0)
        indice = np.argmax(prediccion[0])
        confianza = float(prediccion[0][indice])
        clase = self.class_names[indice]
        
        if confianza < umbral:
            return {
                'clase': 'desconocido',
                'clase_es': 'desconocido',
                'clase_display': 'DESCONOCIDO',
                'confianza': confianza * 100,
                'probabilidades': {
                    c: float(prediccion[0][i]) * 100 
                    for i, c in enumerate(self.class_names)
                }
            }
        
        return {
            'clase': clase,
            'clase_es': MAPEO_ES.get(clase, clase),
            'clase_display': MAPEO_DISPLAY.get(clase, clase.upper()),
            'confianza': confianza * 100,
            'probabilidades': {
                c: float(prediccion[0][i]) * 100 
                for i, c in enumerate(self.class_names)
            }
        }

_clasificador_global = None

def get_clasificador():
    global _clasificador_global
    if _clasificador_global is None:
        _clasificador_global = ClasificadorEfficientNet()
    return _clasificador_global