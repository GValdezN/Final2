from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import base64
import io
import cv2
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

# Inicialización de Flask
app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Configuración de la base de datos
DB_HOST = '18.221.93.23'  # IP de la base de datos
DB_USER = 'gabo'          # Usuario de la base de datos
DB_PASSWORD = '1234'      # Contraseña de la base de datos
DB_NAME = 'hola'          # Nombre de la base de datos

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

def preprocess_image(image):
    """Preprocesar la imagen para detección."""
    np_image = np.array(image)
    gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 1)
    edges = cv2.Canny(blurred, 49, 37)
    dilated = cv2.dilate(edges, np.ones((5, 5)), iterations=1)
    return np_image, dilated

def detect_object(image, processed_image):
    """Detectar el objeto y devolver el contorno."""
    contours, _ = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        if area > 4000:  # Umbral mínimo de área
            return largest_contour
    return None

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
        return redirect(url_for('login'))  # Redirige al login si no está autenticado
    return render_template('index.html', user_name=session['user_name'])  # Carga index.html si está autenticado

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
                    return redirect(url_for('home'))  # Redirige a index.html después de iniciar sesión
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
    return redirect(url_for('login'))  # Redirige al login después de cerrar sesión

@app.route('/camera_predict', methods=['POST'])
def camera_predict():
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 401

    try:
        data = request.get_json()
        image_data = data['image']
        mirror_mode = data['mirror_mode']
        image = Image.open(io.BytesIO(base64.b64decode(image_data.split(',')[1])))

        original_image, processed_image = preprocess_image(image)
        contour = detect_object(original_image, processed_image)

        if contour is not None:
            mask = np.zeros_like(original_image[:, :, 0])
            cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
            cropped_image = cv2.bitwise_and(original_image, original_image, mask=mask)

            cropped_pil = Image.fromarray(cropped_image)
            if mirror_mode:
                cropped_pil = cropped_pil.transpose(Image.FLIP_LEFT_RIGHT)

            predicted_class, confidence = model_predict(cropped_pil, model)

            contour_points = contour.reshape(-1, 2).tolist()
            return jsonify({
                "predicted_class": predicted_class,
                "confidence_percentage": confidence,
                "contour": contour_points
            })
        else:
            return jsonify({"error": "No se detectó ningún objeto."}), 400
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@app.route('/predict', methods=['POST'])
def upload_predict():
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 401

    try:
        file = request.files['file']
        image = Image.open(io.BytesIO(file.read()))
        predicted_class, confidence = model_predict(image, model)
        return jsonify({"predicted_class": predicted_class, "confidence_percentage": confidence})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
