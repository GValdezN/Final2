from flask import Flask, jsonify, request, render_template
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import base64
import io

# Clases del modelo
classes = ['cardboard', 'glass', 'metal', 'organic', 'paper', 'plastic', 'trash']

# Inicialización de la app
app = Flask(__name__)

# Ruta del modelo
MODEL_PATH = "modelos/Densenet121.h5"

# Cargar el modelo
model = load_model(MODEL_PATH)

def model_predict(image, model):
    """Realiza la predicción usando el modelo cargado."""
    image_res = image.resize((224, 224), Image.BILINEAR)
    image_dim = np.array(image_res)
    image_dim = np.expand_dims(image_dim, axis=0)
    preds = model.predict(image_dim)
    predicted_class = classes[np.argmax(preds)]
    confidence_percentage = str(round(preds[0, np.argmax(preds)] * 100, 2))
    return predicted_class, confidence_percentage

@app.route('/')
def home():
    """Renderiza el archivo index.html."""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def upload_predict():
    """Predicción al subir una imagen."""
    if request.method == 'POST':
        try:
            f = request.files['file']  # Recibir archivo
            image = Image.open(io.BytesIO(f.read()))  # Convertir a imagen
            predicted_class, confidence_percentage = model_predict(image, model)

            result = {
                "predicted_class": predicted_class,
                "confidence_percentage": confidence_percentage
            }
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": f"Error en la predicción: {e}"}), 500

@app.route('/camera_predict', methods=['GET', 'POST'])
def camera_predict():
    """Predicción desde la cámara."""
    if request.method == 'POST':
        try:
            # Decodificar imagen enviada en POST
            data = request.get_json()
            image_data = data['image']
            image = Image.open(io.BytesIO(base64.b64decode(image_data.split(',')[1])))

            predicted_class, confidence_percentage = model_predict(image, model)

            result = {
                "predicted_class": predicted_class,
                "confidence_percentage": confidence_percentage
            }
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": f"Error en la predicción de la cámara: {e}"}), 500
    elif request.method == 'GET':
        # Respuesta simple para pruebas con GET
        return jsonify({"message": "Endpoint activo. Usa POST para predicciones."}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
