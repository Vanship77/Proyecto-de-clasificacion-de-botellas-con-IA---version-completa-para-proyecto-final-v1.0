# entrenar_modelo.py - Entrenamiento con EfficientNetB0 (CON LAMBDA - CORREGIDO)
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
import json

# ========== CONFIGURACIÓN ==========
DATASET_DIR = "datasets/trashnet"
TAMANO_IMAGEN = (224, 224)
TAMANO_LOTE = 32
EPOCHS = 25
CLASES = ['glass', 'metal', 'plastic']

print("=" * 60)
print("🚀 ENTRENAMIENTO CON EFFICIENTNETB0 (CON LAMBDA)")
print("=" * 60)
print(f"📂 Dataset: {DATASET_DIR}")
print(f"📋 Clases: {CLASES}")
print("=" * 60)

# ========== 1. VERIFICAR DATASET ==========
print("\n📊 Verificando dataset...")

conteo = {}
for clase in CLASES:
    ruta = os.path.join(DATASET_DIR, clase)
    if os.path.exists(ruta):
        conteo[clase] = len([f for f in os.listdir(ruta) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        print(f"   ✅ {clase}: {conteo[clase]} imágenes")
    else:
        print(f"   ❌ {clase}: carpeta no encontrada")
        conteo[clase] = 0

total_imagenes = sum(conteo.values())
if total_imagenes == 0:
    print("\n❌ No se encontraron imágenes. Verifica la ruta.")
    exit(1)

# ========== 2. CARGAR DATOS ==========
print("\n📂 Cargando datos...")

# Pesos para clases desbalanceadas
total = sum(conteo.values())
peso_clases = {}
for i, clase in enumerate(CLASES):
    if conteo[clase] > 0:
        peso_clases[i] = total / (len(CLASES) * conteo[clase])
print(f"⚖️ Pesos: {peso_clases}")

datos_entrenamiento = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.30,
    subset="training",
    seed=123,
    image_size=TAMANO_IMAGEN,
    batch_size=TAMANO_LOTE,
    class_names=CLASES
)

datos_temporales = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.30,
    subset="validation",
    seed=123,
    image_size=TAMANO_IMAGEN,
    batch_size=TAMANO_LOTE,
    class_names=CLASES
)

# Dividir validación (15%) y prueba (15%)
lotes_validacion = tf.data.experimental.cardinality(datos_temporales)
datos_prueba = datos_temporales.take(lotes_validacion // 2)
datos_validacion = datos_temporales.skip(lotes_validacion // 2)

autotune = tf.data.AUTOTUNE
datos_entrenamiento = datos_entrenamiento.cache().prefetch(autotune)
datos_validacion = datos_validacion.cache().prefetch(autotune)
datos_prueba = datos_prueba.cache().prefetch(autotune)

# ========== 3. CREAR MODELO ==========
print("\n🏗️ Creando modelo EfficientNetB0...")

modelo_base = EfficientNetB0(
    weights='imagenet',
    include_top=False,
    input_shape=(224, 224, 3)
)
modelo_base.trainable = False

# Aumento de datos
aumento_datos = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.15),
    tf.keras.layers.RandomZoom(0.15),
    tf.keras.layers.RandomTranslation(0.1, 0.1),
    tf.keras.layers.RandomContrast(0.2),
    tf.keras.layers.RandomBrightness(0.2, value_range=(0, 255)),
])

# Modelo CON Lambda
modelo = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(224, 224, 3)),
    aumento_datos,
    tf.keras.layers.Lambda(preprocess_input),  # ÍNDICE 1
    modelo_base,                               # ÍNDICE 2 (EfficientNetB0)
    tf.keras.layers.GlobalAveragePooling2D(),  # ÍNDICE 3
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dropout(0.4),
    tf.keras.layers.Dense(len(CLASES), activation='softmax')
])

# ========== 4. ENTRENAR ==========
print("\n📚 FASE 1: Entrenando...")

modelo.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

callbacks = [
    EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1)
]

historial = modelo.fit(
    datos_entrenamiento,
    validation_data=datos_validacion,
    epochs=EPOCHS,
    class_weight=peso_clases,
    callbacks=callbacks
)

# ========== 5. AJUSTE FINO ==========
print("\n🔧 FASE 2: Ajuste fino...")

# La capa 2 es EfficientNetB0 (después de Lambda en índice 1)
efficientnet_layer = modelo.layers[2]
efficientnet_layer.trainable = True

# Mantener BatchNormalization congeladas
for capa in efficientnet_layer.layers:
    if isinstance(capa, tf.keras.layers.BatchNormalization):
        capa.trainable = False

print("✅ EfficientNetB0 descongelado")

modelo.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

historial_ajuste = modelo.fit(
    datos_entrenamiento,
    validation_data=datos_validacion,
    epochs=10,
    class_weight=peso_clases,
    callbacks=callbacks
)

# ========== 6. EVALUAR ==========
print("\n📊 Evaluando modelo...")
perdida, exactitud = modelo.evaluate(datos_prueba, verbose=0)
print(f"✅ Precisión en prueba: {exactitud*100:.2f}%")

# ========== 7. GUARDAR (SIN LA LAMBDA) ==========
print("\n💾 Guardando modelo...")

# Crear un nuevo modelo SIN la Lambda (índice 1)
nuevas_capas = []
for i, capa in enumerate(modelo.layers):
    if i != 1:  # Saltar la capa Lambda
        nuevas_capas.append(capa)

modelo_guardar = tf.keras.Sequential(nuevas_capas)

# Compilar
modelo_guardar.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

os.makedirs("modelos_guardados", exist_ok=True)

# Guardar el modelo SIN Lambda
modelo_guardar.save("modelo_residuos.keras")
modelo_guardar.save("modelos_guardados/clasificador_efficientnet.keras")
print("✅ Modelo guardado en:")
print("   - modelo_residuos.keras")
print("   - modelos_guardados/clasificador_efficientnet.keras")

# Guardar configuración
config = {
    'clases': CLASES,
    'tamano_imagen': TAMANO_IMAGEN,
    'exactitud': float(exactitud),
    'perdida': float(perdida),
    'conteo_imagenes': conteo
}
with open('modelos_guardados/config_efficientnet.json', 'w') as f:
    json.dump(config, f, indent=2)

# ========== 8. GRÁFICAS ==========
print("\n📈 Generando gráficas...")

hist = {}
for key in historial.history.keys():
    hist[key] = historial.history[key] + historial_ajuste.history[key]

plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(hist['accuracy'], label='Entrenamiento', marker='o')
plt.plot(hist['val_accuracy'], label='Validación', marker='o')
plt.title('Precisión por época')
plt.xlabel('Época')
plt.ylabel('Precisión')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.plot(hist['loss'], label='Entrenamiento', marker='o')
plt.plot(hist['val_loss'], label='Validación', marker='o')
plt.title('Pérdida por época')
plt.xlabel('Época')
plt.ylabel('Pérdida')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('modelos_guardados/grafico_entrenamiento_efficientnet.png', dpi=150, bbox_inches='tight')
plt.show()

# ========== 9. MATRIZ DE CONFUSIÓN ==========
print("\n🔄 Generando matriz de confusión...")

etiquetas_reales = []
etiquetas_predichas = []

for imagenes, etiquetas in datos_prueba:
    preds = modelo.predict(imagenes, verbose=0)
    etiquetas_reales.extend(etiquetas.numpy())
    etiquetas_predichas.extend(np.argmax(preds, axis=1))

print("\n📋 Reporte de clasificación:")
print(classification_report(etiquetas_reales, etiquetas_predichas, target_names=CLASES, zero_division=0))

matriz = confusion_matrix(etiquetas_reales, etiquetas_predichas)

plt.figure(figsize=(8, 6))
sns.heatmap(matriz, annot=True, fmt='d', cmap='Blues',
            xticklabels=CLASES, yticklabels=CLASES)
plt.title('Matriz de Confusión - EfficientNetB0')
plt.xlabel('Predicción')
plt.ylabel('Clase Real')
plt.tight_layout()
plt.savefig('modelos_guardados/matriz_confusion_efficientnet.png', dpi=150, bbox_inches='tight')
plt.show()

print("\n" + "=" * 60)
print("✅ ENTRENAMIENTO COMPLETADO")
print("=" * 60)
print(f"📊 Precisión: {exactitud*100:.2f}%")
print(f"💾 Modelo: modelo_residuos.keras")
print(f"📈 Gráficas: modelos_guardados/")
print("=" * 60)