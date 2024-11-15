from flask import Flask, jsonify, request, render_template
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import cv2
import io

# Clases del modelo
classes = ['cardboard', 'glass', 'metal', 'organic', 'paper', 'plastic', 'trash']

# Inicialización de la app
app = Flask(__name__)

# Ruta del modelo
MODEL_PATH = "modelos/Densenet121.h5"

# Cargar el modelo
model = load_model(MODEL_PATH)

# Configuración de la cámara
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Ancho
cap.set(4, 480)  # Alto

def model_predict(image, model):
    image_res = image.resize((224, 224), Image.BILINEAR)
    image_dim = np.array(image_res)
    image_dim = np.expand_dims(image_dim, axis=0)
    preds = model.predict(image_dim)
    predicted_class = classes[np.argmax(preds)]
    confidence_percentage = str(round(preds[0, np.argmax(preds)] * 100, 2))
    return predicted_class, confidence_percentage

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def upload():
    if request.method == 'POST':
        try:
            f = request.files['file']
            image = Image.open(io.BytesIO(f.read()))
            predicted_class, confidence_percentage = model_predict(image, model)
            result = {
                "predicted_class": predicted_class,
                "confidence_percentage": confidence_percentage
            }
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": f"Error en la predicción: {e}"}), 500

@app.route('/camera_predict', methods=['GET'])
def camera_predict():
    try:
        ret, frame = cap.read()
        if not ret:
            return jsonify({"error": "No se pudo acceder a la cámara."}), 500

        # Procesar frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        predicted_class, confidence_percentage = model_predict(image, model)

        result = {
            "predicted_class": predicted_class,
            "confidence_percentage": confidence_percentage
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Error en la predicción de la cámara: {e}"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
