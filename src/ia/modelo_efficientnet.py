# src/ia/modelo_efficientnet.py
# Clasificador de botellas con EfficientNetB0
# VERSIÓN CON DESCONGELAMIENTO PARCIAL Y TOTAL

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Parámetros
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 30
NUM_CLASSES = 3

# Nombres de las clases
CLASS_NAMES = ['glass', 'metal', 'plastic']

# Mapeo a español
MAPEO_ES = {
    'glass': 'VIDRIO 🍾',
    'metal': 'LATA 🥫',
    'plastic': 'PLÁSTICO 🥤'
}

PUNTOS_POR_TIPO = {
    'glass': 15,
    'metal': 10,
    'plastic': 10
}

# Ruta del dataset
DATA_DIR = 'datasets/botellas'

# Ruta donde guardar el modelo
MODELO_DIR = 'modelos_guardados'
MODELO_PATH = os.path.join(MODELO_DIR, 'clasificador_efficientnet.h5')

# ============================================================
# VERIFICAR DATASET
# ============================================================

def verificar_dataset(data_dir):
    """Verifica que el dataset exista y tenga imágenes"""
    if not os.path.exists(data_dir):
        print(f"❌ No se encuentra: {data_dir}")
        return False
    
    for clase in CLASS_NAMES:
        clase_path = os.path.join(data_dir, clase)
        if not os.path.exists(clase_path):
            print(f"❌ No existe: {clase_path}")
            return False
        
        imagenes = os.listdir(clase_path)
        print(f"📂 {clase}: {len(imagenes)} imágenes")
        if len(imagenes) == 0:
            print(f"   ⚠️ La carpeta {clase} está vacía")
            return False
    
    print("✅ Dataset verificado correctamente")
    return True

# ============================================================
# CARGAR DATOS CON DATA AUGMENTATION
# ============================================================

def cargar_datos(data_dir, img_size, batch_size):
    """Carga las imágenes con Data Augmentation"""
    
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=0.2
    )
    
    val_datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=0.2
    )
    
    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',
        subset='training',
        classes=CLASS_NAMES,
        shuffle=True
    )
    
    val_generator = val_datagen.flow_from_directory(
        data_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation',
        classes=CLASS_NAMES,
        shuffle=False
    )
    
    print(f"\n📊 Clases encontradas: {train_generator.class_indices}")
    print(f"📊 Imágenes de entrenamiento: {train_generator.samples}")
    print(f"📊 Imágenes de validación: {val_generator.samples}")
    
    return train_generator, val_generator

# ============================================================
# CREAR MODELO CON EFFICIENTNETB0 (OPCIÓN 1: DESC CONGELAR PARCIAL)
# ============================================================

def crear_modelo_efficientnet_opcion1(num_classes, img_size):
    """
    OPCIÓN 1: Descongelar SOLO las capas superiores (top layers)
    - Congela las primeras 100 capas
    - Entrena las capas restantes (las más cercanas a la salida)
    - Ideal para datasets pequeños (500-1000 imágenes)
    - Tasa de aprendizaje: 0.0001
    """
    
    print("\n🔧 OPCIÓN 1: Descongelamiento parcial (capas superiores)")
    print("-" * 50)
    
    base_model = EfficientNetB0(
        input_shape=(img_size[0], img_size[1], 3),
        include_top=False,
        weights='imagenet'
    )
    
    # ========== CONGELAR PRIMERAS 100 CAPAS ==========
    # Las primeras capas aprenden características básicas (bordes, colores)
    # Las últimas capas aprenden características específicas (formas de botellas)
    for i, layer in enumerate(base_model.layers):
        if i < 100:  # Congelar primeras 100 capas
            layer.trainable = False
        else:
            layer.trainable = True
    
    capas_entrenables = sum(1 for l in base_model.layers if l.trainable)
    print(f"✅ Capas totales: {len(base_model.layers)}")
    print(f"   Capas congeladas: {len(base_model.layers) - capas_entrenables}")
    print(f"   Capas entrenables: {capas_entrenables}")
    
    # ========== AGREGAR CAPAS PERSONALIZADAS ==========
    model = keras.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.3),  # Más dropout para evitar sobreajuste
        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model

# ============================================================
# CREAR MODELO CON EFFICIENTNETB0 (OPCIÓN 2: DESC CONGELAR TODO)
# ============================================================

def crear_modelo_efficientnet_opcion2(num_classes, img_size):
    """
    OPCIÓN 2: Descongelar TODO el modelo
    - Todas las capas son entrenables
    - Necesita MÁS datos (>1000 imágenes por clase)
    - Tasa de aprendizaje: 0.00001 (muy baja)
    - Puede causar sobreajuste si hay pocos datos
    """
    
    print("\n🔧 OPCIÓN 2: Descongelamiento total (todas las capas)")
    print("⚠️  Necesita >1000 imágenes por clase para funcionar bien")
    print("-" * 50)
    
    base_model = EfficientNetB0(
        input_shape=(img_size[0], img_size[1], 3),
        include_top=False,
        weights='imagenet'
    )
    
    # ========== DESC CONGELAR TODAS LAS CAPAS ==========
    base_model.trainable = True
    
    print(f"✅ Capas totales: {len(base_model.layers)}")
    print(f"   Capas entrenables: {len(base_model.layers)} (TODAS)")
    
    # ========== AGREGAR CAPAS PERSONALIZADAS ==========
    model = keras.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.5),  # Más dropout
        layers.Dense(256, activation='relu'),  # Más neuronas
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model

# ============================================================
# COMPILAR MODELO
# ============================================================

def compilar_modelo_opcion1(model):
    """Compila para OPCIÓN 1 (descongelado parcial)"""
    
    optimizer = keras.optimizers.Adam(
        learning_rate=0.0001,  # Tasa baja para fine-tuning
        beta_1=0.9,
        beta_2=0.999
    )
    
    model.compile(
        optimizer=optimizer,
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("✅ Modelo compilado (Opcion 1 - lr=0.0001)")
    return model

def compilar_modelo_opcion2(model):
    """Compila para OPCIÓN 2 (descongelado total)"""
    
    optimizer = keras.optimizers.Adam(
        learning_rate=0.00001,  # Tasa MUY baja para no destruir el pre-entrenamiento
        beta_1=0.9,
        beta_2=0.999
    )
    
    model.compile(
        optimizer=optimizer,
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("✅ Modelo compilado (Opcion 2 - lr=0.00001)")
    return model

# ============================================================
# ENTRENAR MODELO
# ============================================================

def entrenar_modelo(model, train_gen, val_gen, epochs, opcion):
    """Entrena el modelo con callbacks"""
    
    os.makedirs(MODELO_DIR, exist_ok=True)
    
    # Callbacks
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=10 if opcion == 2 else 7,  # Más paciencia para opción 2
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5 if opcion == 2 else 4,
            min_lr=1e-8,
            verbose=1
        ),
        ModelCheckpoint(
            MODELO_PATH,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
    ]
    
    print(f"\n🚀 Comenzando entrenamiento (Opción {opcion})...")
    print("=" * 60)
    print(f"📊 Épocas: {epochs}")
    print(f"📦 Batch size: {BATCH_SIZE}")
    print(f"📂 Imágenes de entrenamiento: {train_gen.samples}")
    print(f"📂 Imágenes de validación: {val_gen.samples}")
    print("=" * 60)
    
    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1
    )
    
    print("\n✅ Entrenamiento completado!")
    print(f"📊 Mejor precisión de validación: {max(history.history['val_accuracy']):.4f}")
    
    return history

# ============================================================
# EVALUAR MODELO
# ============================================================

def evaluar_modelo(model, val_gen):
    """Evalúa el modelo y genera métricas"""
    
    print("\n📊 EVALUANDO EL MODELO")
    print("=" * 50)
    
    loss, accuracy = model.evaluate(val_gen, verbose=1)
    print(f"✅ Precisión en validación: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"📉 Pérdida en validación: {loss:.4f}")
    
    val_gen.reset()
    predicciones = model.predict(val_gen, verbose=1)
    clases_predichas = np.argmax(predicciones, axis=1)
    clases_reales = val_gen.classes
    
    nombres_clases = list(val_gen.class_indices.keys())
    
    cm = confusion_matrix(clases_reales, clases_predichas)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=nombres_clases,
                yticklabels=nombres_clases)
    plt.title('Matriz de Confusión - EfficientNetB0')
    plt.ylabel('Clase Real')
    plt.xlabel('Clase Predicha')
    plt.savefig(os.path.join(MODELO_DIR, 'matriz_confusion_efficientnet.png'))
    plt.show()
    
    print("\n📊 REPORTE DE CLASIFICACIÓN")
    print("-" * 30)
    print(classification_report(clases_reales, clases_predichas, target_names=nombres_clases))
    
    return accuracy, loss

# ============================================================
# GRAFICAR RESULTADOS
# ============================================================

def graficar_resultados(history):
    """Grafica la evolución del entrenamiento"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1.plot(history.history['accuracy'], label='Entrenamiento', linewidth=2)
    ax1.plot(history.history['val_accuracy'], label='Validación', linewidth=2)
    ax1.set_title('Precisión del Modelo - EfficientNetB0', fontsize=14)
    ax1.set_xlabel('Épocas', fontsize=12)
    ax1.set_ylabel('Precisión', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(history.history['loss'], label='Entrenamiento', linewidth=2)
    ax2.plot(history.history['val_loss'], label='Validación', linewidth=2)
    ax2.set_title('Pérdida del Modelo - EfficientNetB0', fontsize=14)
    ax2.set_xlabel('Épocas', fontsize=12)
    ax2.set_ylabel('Pérdida', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(MODELO_DIR, 'historial_efficientnet.png'))
    plt.show()
    
    print(f"✅ Gráficos guardados en: {MODELO_DIR}")

# ============================================================
# GUARDAR MODELO
# ============================================================

def guardar_modelo(model):
    """Guarda el modelo entrenado"""
    os.makedirs(MODELO_DIR, exist_ok=True)
    model.save(MODELO_PATH)
    print(f"✅ Modelo guardado en: {MODELO_PATH}")

# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    print("=" * 60)
    print("♻️  CLASIFICADOR DE BOTELLAS CON EFFICIENTNETB0")
    print("=" * 60)
    
    # ========== SELECCIONAR OPCIÓN ==========
    print("\n📌 ¿Qué opción quieres probar?")
    print("   [1] Opción 1: Descongelar capas superiores (recomendado para pocos datos)")
    print("   [2] Opción 2: Descongelar todo (necesita >1000 imágenes por clase)")
    
    # Cambia esta variable para probar cada opción
    OPCION = 1  # Cambiar a 2 para probar la opción 2
    
    print(f"\n🔧 Usando Opción {OPCION}")
    print("=" * 60)
    
    # 1. Verificar dataset
    print("\n📂 Verificando dataset...")
    if not verificar_dataset(DATA_DIR):
        print("\n❌ Error: Revisa la ruta del dataset")
        return
    
    # 2. Cargar datos
    print("\n📂 Cargando dataset...")
    train_gen, val_gen = cargar_datos(DATA_DIR, IMG_SIZE, BATCH_SIZE)
    
    # 3. Crear modelo según opción
    print("\n🧠 Creando modelo con EfficientNetB0...")
    if OPCION == 1:
        model = crear_modelo_efficientnet_opcion1(NUM_CLASSES, IMG_SIZE)
        model = compilar_modelo_opcion1(model)
    else:
        model = crear_modelo_efficientnet_opcion2(NUM_CLASSES, IMG_SIZE)
        model = compilar_modelo_opcion2(model)
    
    model.summary()
    
    # 4. Entrenar
    history = entrenar_modelo(model, train_gen, val_gen, EPOCHS, OPCION)
    
    # 5. Evaluar
    accuracy, loss = evaluar_modelo(model, val_gen)
    
    # 6. Graficar
    graficar_resultados(history)
    
    # 7. Guardar
    guardar_modelo(model)
    
    print("\n" + "=" * 60)
    print("🎉 ¡ENTRENAMIENTO CON EFFICIENTNETB0 COMPLETADO!")
    print("=" * 60)
    print(f"\n📊 Resumen final:")
    print(f"   - Modelo: EfficientNetB0 (Opción {OPCION})")
    print(f"   - Precisión en validación: {accuracy:.2%}")
    print(f"   - Modelo guardado en: {MODELO_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()