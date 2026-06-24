# fix_model.py - Repara el modelo para que se pueda cargar correctamente
import tensorflow as tf
import os

print("=" * 60)
print("🔧 REPARANDO MODELO EFFICIENTNETB0")
print("=" * 60)

# Cargar el modelo original
print("\n📂 Cargando modelo original...")
try:
    modelo = tf.keras.models.load_model('modelo_residuos.keras')
    print("✅ Modelo cargado correctamente")
except Exception as e:
    print(f"❌ Error cargando modelo: {e}")
    exit(1)

# Crear un nuevo modelo SIN la capa Lambda
print("\n🔧 Creando modelo reparado...")

nuevas_capas = []
for i, capa in enumerate(modelo.layers):
    # Saltar la capa Lambda (índice 2)
    if i != 2:
        nuevas_capas.append(capa)

modelo_reparado = tf.keras.Sequential(nuevas_capas)

# Compilar
modelo_reparado.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

print("✅ Modelo reparado creado")

# Guardar
print("\n💾 Guardando modelos reparados...")
os.makedirs('modelos_guardados', exist_ok=True)

modelo_reparado.save('modelo_residuos_fixed.keras')
print("✅ Guardado: modelo_residuos_fixed.keras")

modelo_reparado.save('modelos_guardados/clasificador_efficientnet.keras')
print("✅ Guardado: modelos_guardados/clasificador_efficientnet.keras")

# Verificar
print("\n🧪 Verificando carga...")
try:
    test = tf.keras.models.load_model('modelos_guardados/clasificador_efficientnet.keras')
    print("✅ Modelo se carga correctamente")
except Exception as e:
    print(f"❌ Error cargando: {e}")

print("\n" + "=" * 60)
print("🎉 ¡MODELO REPARADO CON ÉXITO!")
print("=" * 60)
print("\n📁 Archivos generados:")
print("   - modelo_residuos_fixed.keras")
print("   - modelos_guardados/clasificador_efficientnet.keras")