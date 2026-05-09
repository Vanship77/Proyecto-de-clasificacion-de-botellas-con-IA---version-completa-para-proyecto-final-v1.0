# main.py - Punto de entrada del proyecto
from src.bd.conexion import Database

def main():
    print("=" * 50)
    print("♻️  SISTEMA DE RECICLAJE CON IA")
    print("=" * 50)
    
    # Probar conexión a PostgreSQL
    print("\n📡 Probando conexión a PostgreSQL...")
    db = Database()
    if db.conectar():
        db.crear_tablas()
        print("\n🎉 ¡Todo listo para empezar!")
        print("\n📌 Próximos pasos:")
        print("   1. Entrenar la IA con el dataset de botellas")
        print("   2. Crear la API para conectar con Arduino")
        print("   3. Integrar la clasificación con la BD")
        db.cerrar()
    else:
        print("\n⚠️ No se pudo conectar a PostgreSQL")
        print("   Asegúrate de tener PostgreSQL instalado y ejecutándose")

if __name__ == "__main__":
    main()