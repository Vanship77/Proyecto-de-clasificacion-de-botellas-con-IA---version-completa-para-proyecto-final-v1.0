# src/ia/modelo.py
# Clasificador de botellas: Plástico, Vidrio, Lata

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import matplotlib.pyplot as plt
import os
import numpy as np

# ============================================
# CONFIGURACIÓN
# ============================================

# Parámetros
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 30
NUM_CLASSES = 3  # plastico, vidrio, lata

# Nombres de las clases (deben coincidir con las carpetas)
CLASS_NAMES = ['glass', 'metal', 'plastic']

# Ruta donde están las imágenes
DATA_DIR = 'datasets/botellas'

# ============================================
# CARGAR LOS DATOS
# ============================================

def cargar_datos(data_dir, img_size, batch_size):
    """
    Carga las imágenes desde carpetas organizadas por clase
    """
    
    # Data augmentation para entrenamiento
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        validation_split=0.2  # 20% para validación
    )
    
    # Solo reescalado para validación
    val_datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=0.2
    )
    
    # Cargar datos de entrenamiento
    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',
        subset='training',
        classes=CLASS_NAMES
    )
    
    # Cargar datos de validación
    val_generator = val_datagen.flow_from_directory(
        data_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation',
        classes=CLASS_NAMES
    )
    
    print(f"\n📊 Clases encontradas: {train_generator.class_indices}")
    print(f"📊 Imágenes de entrenamiento: {train_generator.samples}")
    print(f"📊 Imágenes de validación: {val_generator.samples}")
    
    return train_generator, val_generator

# ============================================
# CREAR EL MODELO
# ============================================

def crear_modelo(num_classes, img_size):
    """
    Crea un modelo usando MobileNetV2 pre-entrenado (transfer learning)
    """
    
    # Cargar MobileNetV2 sin la capa superior
    base_model = MobileNetV2(
        input_shape=(img_size[0], img_size[1], 3),
        include_top=False,
        weights='imagenet'
    )
    
    # Congelar las capas del modelo base
    base_model.trainable = False
    
    # Construir el modelo completo
    model = keras.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.2),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model

# ============================================
# ENTRENAR EL MODELO
# ============================================

def entrenar_modelo(model, train_gen, val_gen, epochs):
    """
    Entrena el modelo y guarda el historial
    """
    
    # Compilar el modelo
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Callbacks para mejorar el entrenamiento
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            verbose=1
        )
    ]
    
    print("\n🚀 Comenzando entrenamiento...")
    print("=" * 50)
    
    # Entrenar
    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1
    )
    
    return history

# ============================================
# EVALUAR Y GUARDAR
# ============================================

def evaluar_modelo(model, val_gen):
    """
    Evalúa el modelo en el conjunto de validación
    """
    print("\n📊 Evaluando modelo...")
    loss, accuracy = model.evaluate(val_gen)
    print(f"✅ Precisión en validación: {accuracy:.4f} ({accuracy*100:.2f}%)")
    return accuracy

def guardar_modelo(model, ruta='modelos_guardados/clasificador_botellas.h5'):
    """
    Guarda el modelo entrenado
    """
    os.makedirs('modelos_guardados', exist_ok=True)
    model.save(ruta)
    print(f"✅ Modelo guardado en: {ruta}")

def graficar_resultados(history):
    """
    Grafica la precisión y pérdida durante el entrenamiento
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Precisión
    ax1.plot(history.history['accuracy'], label='Entrenamiento')
    ax1.plot(history.history['val_accuracy'], label='Validación')
    ax1.set_title('Precisión del modelo')
    ax1.set_xlabel('Épocas')
    ax1.set_ylabel('Precisión')
    ax1.legend()
    ax1.grid(True)
    
    # Pérdida
    ax2.plot(history.history['loss'], label='Entrenamiento')
    ax2.plot(history.history['val_loss'], label='Validación')
    ax2.set_title('Pérdida del modelo')
    ax2.set_xlabel('Épocas')
    ax2.set_ylabel('Pérdida')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('modelos_guardados/grafico_entrenamiento.png')
    plt.show()
    print("✅ Gráfico guardado en: modelos_guardados/grafico_entrenamiento.png")

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def main():
    print("=" * 60)
    print("♻️  CLASIFICADOR DE BOTELLAS - PLÁSTICO, VIDRIO, LATA")
    print("=" * 60)
    
    # Verificar que existe la carpeta de datos
    if not os.path.exists(DATA_DIR):
        print(f"\n❌ ERROR: No se encuentra la carpeta: {DATA_DIR}")
        print("\n📌 Por favor:")
        print("   1. Asegúrate de tener las imágenes en datasets/botellas/")
        print("   2. Ejecuta los comandos para copiar el dataset")
        print("\n   Estructura esperada:")
        print(f"   {DATA_DIR}/")
        print("       glass/")
        print("           imagen1.jpg")
        print("       metal/")
        print("           imagen1.jpg")
        print("       plastic/")
        print("           imagen1.jpg")
        return
    
    # 1. Cargar datos
    print("\n📂 Cargando dataset...")
    train_gen, val_gen = cargar_datos(DATA_DIR, IMG_SIZE, BATCH_SIZE)
    
    # 2. Crear modelo
    print("\n🧠 Creando modelo con transfer learning (MobileNetV2)...")
    model = crear_modelo(NUM_CLASSES, IMG_SIZE)
    model.summary()
    
    # 3. Entrenar
    history = entrenar_modelo(model, train_gen, val_gen, EPOCHS)
    
    # 4. Evaluar
    accuracy = evaluar_modelo(model, val_gen)
    
    # 5. Guardar modelo
    guardar_modelo(model)
    
    # 6. Graficar resultados
    graficar_resultados(history)
    
    print("\n" + "=" * 60)
    print("🎉 ¡ENTRENAMIENTO COMPLETADO CON ÉXITO!")
    print("=" * 60)
    print(f"\n📊 Resumen final:")
    print(f"   - Precisión del modelo: {accuracy:.2%}")
    print(f"   - Modelo guardado en: modelos_guardados/clasificador_botellas.h5")
    print(f"   - Gráfico guardado en: modelos_guardados/grafico_entrenamiento.png")

if __name__ == "__main__":
    main()
    