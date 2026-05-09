# src/bd/conexion.py - Conexión a PostgreSQL
import psycopg2
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.conn = None
    
    def conectar(self):
        """Establece conexión con PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("✅ Conectado a PostgreSQL")
            return True
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def crear_tablas(self):
        """Crea las tablas necesarias si no existen"""
        cursor = self.conn.cursor()
        
        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                puntos_totales INTEGER DEFAULT 0,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de tipos de residuo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_residuo (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(30) UNIQUE NOT NULL,
                puntos_base INTEGER NOT NULL
            )
        """)
        
        # Insertar tipos de residuo si no existen
        cursor.execute("""
            INSERT INTO tipos_residuo (nombre, puntos_base) 
            VALUES ('plastico', 10), ('vidrio', 15), ('lata', 10)
            ON CONFLICT (nombre) DO NOTHING
        """)
        
        # Tabla de registros de reciclaje
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros_reciclaje (
                id SERIAL PRIMARY KEY,
                id_usuario INTEGER REFERENCES usuarios(id),
                id_tipo_residuo INTEGER REFERENCES tipos_residuo(id),
                puntos_ganados INTEGER NOT NULL,
                confianza_ia DECIMAL(5,2),
                fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        print("✅ Tablas creadas correctamente")
    
    def registrar_reciclaje(self, usuario_id, tipo_residuo, confianza_ia):
        """Registra un reciclaje y suma puntos al usuario"""
        cursor = self.conn.cursor()
        
        # Obtener puntos del tipo de residuo
        cursor.execute("SELECT puntos_base FROM tipos_residuo WHERE nombre = %s", (tipo_residuo,))
        puntos = cursor.fetchone()[0]
        
        # Insertar registro
        cursor.execute("""
            INSERT INTO registros_reciclaje (id_usuario, id_tipo_residuo, puntos_ganados, confianza_ia)
            VALUES (%s, (SELECT id FROM tipos_residuo WHERE nombre = %s), %s, %s)
        """, (usuario_id, tipo_residuo, puntos, confianza_ia))
        
        # Actualizar puntos del usuario
        cursor.execute("""
            UPDATE usuarios SET puntos_totales = puntos_totales + %s
            WHERE id = %s
        """, (puntos, usuario_id))
        
        self.conn.commit()
        return puntos
    
    def cerrar(self):
        if self.conn:
            self.conn.close()
            print("🔌 Conexión cerrada")