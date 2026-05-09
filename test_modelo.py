# test_modelo.py
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os

# Cargar el modelo
modelo = tf.keras.models.load_model('modelos_guardados/clasificador_botellas.h5')
CLASSES = ['glass', 'metal', 'plastic']

# Buscar una imagen de prueba en la carpeta datasets/botellas
test_dir = 'datasets/botellas'
for clase in CLASSES:
    clase_path = os.path.join(test_dir, clase)
    imagenes = os.listdir(clase_path)
    if imagenes:
        img_path = os.path.join(clase_path, imagenes[0])
        print(f"\n📷 Probando con imagen: {img_path}")
        
        # Cargar y preprocesar
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0
        
        # Predecir
        prediccion = modelo.predict(img_array, verbose=0)
        clase_idx = np.argmax(prediccion[0])
        confianza = prediccion[0][clase_idx]
        
        print(f"✅ Predicción: {CLASSES[clase_idx]}")
        print(f"📊 Confianza: {confianza:.2%}")
        print(f"🎯 Esperado: {clase}")
        print(f"{'✓ CORRECTO' if CLASSES[clase_idx] == clase else '✗ INCORRECTO'}")
        break