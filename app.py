from flask import Flask, jsonify, request, render_template
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import base64
import io
import cv2

# Clases del modelo
classes = ['cardboard', 'glass', 'metal', 'organic', 'paper', 'plastic', 'trash']

# Inicialización de la app
app = Flask(__name__)

# Ruta del modelo
MODEL_PATH = "modelos/Densenet121.h5"
model = load_model(MODEL_PATH)

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
    return None  # Si no hay objeto detectado

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
    return render_template('index.html')

@app.route('/camera_predict', methods=['POST'])
def camera_predict():
    try:
        data = request.get_json()
        image_data = data['image']
        mirror_mode = data['mirror_mode']  # Recibe si está en modo espejo
        image = Image.open(io.BytesIO(base64.b64decode(image_data.split(',')[1])))
        
        # Preprocesar y detectar el objeto
        original_image, processed_image = preprocess_image(image)
        contour = detect_object(original_image, processed_image)

        if contour is not None:
            mask = np.zeros_like(original_image[:, :, 0])
            cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
            cropped_image = cv2.bitwise_and(original_image, original_image, mask=mask)

            # Convertir el recorte a PIL para predecir
            cropped_pil = Image.fromarray(cropped_image)
            if mirror_mode:
                cropped_pil = cropped_pil.transpose(Image.FLIP_LEFT_RIGHT)

            # Realizar la predicción
            predicted_class, confidence = model_predict(cropped_pil, model)

            # Devolver el contorno
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
    try:
        file = request.files['file']
        image = Image.open(io.BytesIO(file.read()))
        predicted_class, confidence = model_predict(image, model)
        return jsonify({"predicted_class": predicted_class, "confidence_percentage": confidence})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
