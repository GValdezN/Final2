import pymysql
from werkzeug.security import generate_password_hash

# Configuración de la base de datos
DB_HOST = '18.221.93.23'
DB_USER = 'gabo'
DB_PASSWORD = '1234'
DB_NAME = 'hola'

# Conectar a la base de datos
connection = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

try:
    with connection.cursor() as cursor:
        # Seleccionar todos los usuarios con contraseñas sin cifrar
        cursor.execute("SELECT usu_id, usu_pass FROM usuario")
        usuarios = cursor.fetchall()

        for usuario in usuarios:
            usu_id = usuario[0]
            usu_pass = usuario[1]

            # Cifrar la contraseña
            hashed_password = generate_password_hash(usu_pass)

            # Actualizar la contraseña cifrada en la base de datos
            cursor.execute(
                "UPDATE usuario SET usu_pass = %s WHERE usu_id = %s",
                (hashed_password, usu_id)
            )

        # Confirmar los cambios
        connection.commit()

        print("Contraseñas cifradas correctamente.")
finally:
    connection.close()
