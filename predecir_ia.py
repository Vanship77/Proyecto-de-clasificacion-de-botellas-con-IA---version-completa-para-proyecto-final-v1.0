# predecir_ia.py - Con EfficientNetB0
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import random

# Cargar modelo EfficientNetB0
modelo = tf.keras.models.load_model('modelos_guardados/clasificador_efficientnet.h5')
CLASSES = ['glass (vidrio)', 'metal (lata)', 'plastic (plastico)']

print("=" * 60)
print("🔍 CLASIFICADOR DE BOTELLAS - EfficientNetB0")
print("=" * 60)

# Seleccionar una imagen aleatoria
clase_real = random.choice(['glass', 'metal', 'plastic'])
carpeta = f'datasets/botellas/{clase_real}'
imagenes = os.listdir(carpeta)
img_path = os.path.join(carpeta, random.choice(imagenes))

print(f"\n📷 Imagen: {os.path.basename(img_path)}")
print(f"🎯 Clase real: {clase_real}")
print("-" * 40)

# Preprocesar
img = image.load_img(img_path, target_size=(224, 224))
img_array = image.img_to_array(img)
img_array = np.expand_dims(img_array, axis=0) / 255.0

# Predecir
prediccion = modelo.predict(img_array, verbose=0)

print("\n📊 Probabilidades:")
for i, clase in enumerate(CLASSES):
    print(f"   {clase}: {prediccion[0][i]:.2%}")

clase_predicha = CLASSES[np.argmax(prediccion[0])]
confianza = max(prediccion[0])
clase_real_nombre = CLASSES[['glass', 'metal', 'plastic'].index(clase_real)]

print("-" * 40)
print(f"\n✅ Predicción: {clase_predicha}")
print(f"📊 Confianza: {confianza:.2%}")
print("=" * 60)