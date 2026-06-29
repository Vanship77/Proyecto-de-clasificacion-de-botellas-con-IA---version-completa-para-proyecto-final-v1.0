# predecir_ia.py - Predictor con EfficientNetB0
import os
import sys
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input

# ========== CONFIGURACIÓN ==========
CLASES = ['glass', 'metal', 'plastic']
MAPEO_DISPLAY = {'glass': 'VIDRIO', 'metal': 'LATA', 'plastic': 'PLÁSTICO'}

def cargar_modelo():
    """Carga el modelo EfficientNet entrenado"""
    rutas = [
        'modelo_residuos.keras',
        'modelos_guardados/clasificador_efficientnet.keras'
    ]
    
    for ruta in rutas:
        if os.path.exists(ruta):
            try:
                modelo = tf.keras.models.load_model(ruta)
                print(f"✅ Modelo cargado desde: {ruta}")
                return modelo
            except Exception as e:
                print(f"⚠️ Error cargando {ruta}: {e}")
    
    print("❌ No se encontró ningún modelo entrenado.")
    print("   Ejecuta: python entrenar_modelo.py")
    return None

def predecir_imagen(ruta_imagen, modelo, umbral=0.75):
    if not os.path.exists(ruta_imagen):
        return {'error': f'Archivo no encontrado: {ruta_imagen}'}
    
    img = image.load_img(ruta_imagen, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = img_array.astype(np.float32)
    img_array = preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)
    
    prediccion = modelo.predict(img_array, verbose=0)
    indice = np.argmax(prediccion[0])
    confianza = float(prediccion[0][indice])
    clase = CLASES[indice]
    
    if confianza < umbral:
        return {
            'clase': 'desconocido',
            'clase_display': 'DESCONOCIDO',
            'confianza': confianza * 100,
            'probabilidades': {
                c: float(prediccion[0][i]) * 100 
                for i, c in enumerate(CLASES)
            }
        }
    
    return {
        'clase': clase,
        'clase_display': MAPEO_DISPLAY.get(clase, clase.upper()),
        'confianza': confianza * 100,
        'probabilidades': {
            c: float(prediccion[0][i]) * 100 
            for i, c in enumerate(CLASES)
        }
    }

def main():
    print("=" * 60)
    print("🔍 CLASIFICADOR DE BOTELLAS - EfficientNetB0")
    print("=" * 60)
    
    modelo = cargar_modelo()
    if modelo is None:
        return
    
    if len(sys.argv) < 2:
        print("\n📖 Uso:")
        print("   python predecir_ia.py [ruta_imagen]")
        print("   python predecir_ia.py [ruta_carpeta]")
        print("\n💡 Ejemplos:")
        print("   python predecir_ia.py botella.jpg")
        print("   python predecir_ia.py datasets/trashnet/glass/")
        return
    
    ruta = sys.argv[1]
    
    if not os.path.exists(ruta):
        print(f"❌ Ruta no encontrada: {ruta}")
        return
    
    if os.path.isdir(ruta):
        print(f"\n📁 Procesando carpeta: {ruta}")
        print("-" * 40)
        
        for archivo in os.listdir(ruta):
            if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                ruta_img = os.path.join(ruta, archivo)
                resultado = predecir_imagen(ruta_img, modelo)
                
                if 'error' in resultado:
                    print(f"{archivo}: ❌ ERROR")
                else:
                    print(f"{archivo}: {resultado['clase_display']} ({resultado['confianza']:.2f}%)")
    else:
        print(f"\n📷 Imagen: {os.path.basename(ruta)}")
        print("-" * 40)
        
        resultado = predecir_imagen(ruta, modelo)
        
        if 'error' in resultado:
            print(f"❌ Error: {resultado['error']}")
            return
        
        print(f"✅ Clase: {resultado['clase_display']}")
        print(f"📊 Confianza: {resultado['confianza']:.2f}%")
        print("\n📊 Probabilidades:")
        for clase, prob in resultado['probabilidades'].items():
            barra = '█' * int(prob // 5)
            print(f"   {clase}: {barra} {prob:.2f}%")

if __name__ == "__main__":
    main()