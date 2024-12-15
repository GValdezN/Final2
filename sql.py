from flask import Flask, jsonify
import pymysql

app = Flask(__name__)

# Configuración de la base de datos
DB_HOST = '18.221.93.23'   # IP pública de la base de datos
DB_USER = 'gabo'           # Usuario de la base de datos
DB_PASSWORD = '1234'       # Contraseña del usuario
DB_NAME = 'hola'           # Nombre de la base de datos

# Prueba de conexión a la base de datos
def conectar_db():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except Exception as e:
        print("Error al conectar a la base de datos:", e)
        return None

@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    connection = conectar_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM usuarios;")
                usuarios = cursor.fetchall()
                return jsonify(usuarios)
        finally:
            connection.close()
    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

