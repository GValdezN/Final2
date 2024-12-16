from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import base64
import io
import os
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Inicialización de Flask
app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Configuración de la base de datos
DB_HOST = '18.221.93.23'
DB_USER = 'gabo'
DB_PASSWORD = '1234'
DB_NAME = 'hola'

# Configuración de rutas para guardar imágenes
UPLOAD_FOLDER = 'static/captured_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ruta del modelo
MODEL_PATH = "modelos/Densenet121.h5"
model = load_model(MODEL_PATH)

# Clases del modelo
classes = ['cardboard', 'glass', 'metal', 'organic', 'paper', 'plastic', 'trash']

def conectar_db():
    """Conecta a la base de datos."""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def model_predict(image, model):
    """Realiza la predicción usando el modelo cargado."""
    image_resized = image.resize((224, 224), Image.BILINEAR)
    image_array = np.array(image_resized)
    image_array = np.expand_dims(image_array, axis=0)
    preds = model.predict(image_array)
    predicted_class = classes[np.argmax(preds)]
    confidence = str(round(preds[0, np.argmax(preds)] * 100, 2))
    return predicted_class, confidence

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user_name=session['user_name'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usu_nombre = request.form['usu_nombre']
        usu_correo = request.form['usu_correo']
        usu_pass = request.form['usu_pass']
        hashed_password = generate_password_hash(usu_pass)

        try:
            connection = conectar_db()
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO usuario (usu_nombre, usu_correo, usu_pass, usu_tipo_id) VALUES (%s, %s, %s, %s)",
                    (usu_nombre, usu_correo, hashed_password, 1)
                )
                connection.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Error al registrar: {str(e)}", 500
        finally:
            connection.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usu_correo = request.form['usu_correo']
        usu_pass = request.form['usu_pass']

        try:
            connection = conectar_db()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM usuario WHERE usu_correo = %s", (usu_correo,))
                user = cursor.fetchone()

                if user and check_password_hash(user['usu_pass'], usu_pass):
                    session['user_id'] = user['usu_id']
                    session['user_name'] = user['usu_nombre']
                    return redirect(url_for('home'))
                else:
                    return "Usuario o contraseña incorrectos", 401
        except Exception as e:
            return f"Error al iniciar sesión: {str(e)}", 500
        finally:
            connection.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/predict_feedback', methods=['POST'])
def predict_feedback():
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 401

    try:
        file = request.files.get('file')
        image_data = request.json.get('image_data') if not file else None

        if file:
            image = Image.open(file)
        elif image_data:
            image = Image.open(io.BytesIO(base64.b64decode(image_data.split(',')[1])))
        else:
            return jsonify({"error": "No se recibió una imagen válida"}), 400

        if image.mode != 'RGB':
            image = image.convert('RGB')

        predicted_class, confidence = model_predict(image, model)

        filename = secure_filename(f"{session['user_id']}_{np.random.randint(1000)}.png")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image.save(filepath)

        return jsonify({
            "predicted_class": predicted_class,
            "confidence_percentage": confidence,
            "image_path": filepath
        })
    except Exception as e:
        return jsonify({"error": f"Error durante la predicción: {str(e)}"}), 500

@app.route('/save_feedback', methods=['POST'])
def save_feedback():
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 401

    try:
        data = request.get_json()
        description = data.get('description', '')
        like = data.get('like', False)
        image_path = data.get('image_path')

        if not description.strip():
            return jsonify({"error": "La descripción no puede estar vacía"}), 400

        connection = conectar_db()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO opinion (opi_descripcion, opi_like, opi_usu_id, opi_imagen_ruta) VALUES (%s, %s, %s, %s)",
                (description, like, session['user_id'], image_path)
            )
            connection.commit()

        return jsonify({"message": "Feedback guardado exitosamente"})
    except Exception as e:
        return jsonify({"error": f"Error al guardar el feedback: {str(e)}"}), 500
    finally:
        connection.close()

@app.route('/my_feedbacks', methods=['GET'])
def my_feedbacks():
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 401

    try:
        connection = conectar_db()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT opi_id, opi_descripcion, opi_like, opi_imagen_ruta FROM opinion WHERE opi_usu_id = %s",
                (session['user_id'],)
            )
            feedbacks = cursor.fetchall()
        return jsonify({"feedbacks": feedbacks})
    except Exception as e:
        return jsonify({"error": f"Error al cargar los feedbacks: {str(e)}"}), 500
    finally:
        connection.close()

@app.route('/delete_feedback/<int:feedback_id>', methods=['DELETE'])
def delete_feedback(feedback_id):
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 401

    try:
        connection = conectar_db()
        with connection.cursor() as cursor:
            # Obtén la ruta de la imagen antes de eliminar el registro
            cursor.execute(
                "SELECT opi_imagen_ruta FROM opinion WHERE opi_id = %s AND opi_usu_id = %s",
                (feedback_id, session['user_id'])
            )
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": "Feedback no encontrado o no autorizado"}), 404

            image_path = result['opi_imagen_ruta']

            # Elimina el registro en la base de datos
            cursor.execute(
                "DELETE FROM opinion WHERE opi_id = %s AND opi_usu_id = %s",
                (feedback_id, session['user_id'])
            )
            connection.commit()

        # Elimina el archivo del sistema de archivos
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        return jsonify({"message": "Feedback eliminado correctamente"})
    except Exception as e:
        return jsonify({"error": f"Error al eliminar el feedback: {str(e)}"}), 500
    finally:
        connection.close()

@app.route('/edit_feedback/<int:feedback_id>', methods=['PUT'])
def edit_feedback(feedback_id):
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 401

    try:
        data = request.get_json()
        description = data.get('description')
        like = data.get('like')

        connection = conectar_db()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE opinion SET opi_descripcion = %s, opi_like = %s WHERE opi_id = %s AND opi_usu_id = %s",
                (description, like, feedback_id, session['user_id'])
            )
            connection.commit()
        return jsonify({"message": "Feedback modificado correctamente"})
    except Exception as e:
        return jsonify({"error": f"Error al modificar el feedback: {str(e)}"}), 500
    finally:
        connection.close()
        
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
