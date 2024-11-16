$(document).ready(function () {
    const video = document.getElementById('camera-stream');
    const canvas = document.getElementById('camera-canvas');
    const capturedCanvas = document.getElementById('captured-image');
    const loader = $('.loader');
    let isFrontCamera = true;

    // Alternar entre secciones
    $('a.nav-link').click(function (e) {
        e.preventDefault();
        const target = $(this).attr('href');
        $('.content-section').hide();
        $(target).show();
    });

    // Función para iniciar la cámara
    async function startCamera() {
        try {
            const constraints = {
                video: {
                    facingMode: isFrontCamera ? 'user' : 'environment'
                }
            };
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = stream;
            video.style.transform = isFrontCamera ? 'scaleX(-1)' : 'scaleX(1)';
        } catch (err) {
            console.error("Error al acceder a la cámara:", err);
            alert("No se pudo acceder a la cámara. Verifica los permisos.");
        }
    }

    // Cambiar entre cámara frontal y trasera
    $('#btn-toggle-camera').click(function () {
        isFrontCamera = !isFrontCamera;
        startCamera();
    });

    // Capturar imagen y predecir
    $('#btn-capture').click(function () {
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        if (isFrontCamera) {
            // Si está en modo espejo, invertir horizontalmente
            context.translate(canvas.width, 0);
            context.scale(-1, 1);
        }

        // Dibujar la imagen en el canvas
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        if (isFrontCamera) {
            // Restaurar la transformación después de dibujar
            context.setTransform(1, 0, 0, 1, 0, 0);
        }

        const imageData = canvas.toDataURL('image/jpeg');
        loader.show();

        $.ajax({
            type: 'POST',
            url: '/camera_predict',
            data: JSON.stringify({ image: imageData, mirror_mode: isFrontCamera }),
            contentType: 'application/json',
            success: function (data) {
                loader.hide();
                const ctxCaptured = capturedCanvas.getContext('2d');
                capturedCanvas.width = canvas.width;
                capturedCanvas.height = canvas.height;

                // Dibujar la imagen capturada en el canvas del lado derecho
                ctxCaptured.drawImage(canvas, 0, 0, canvas.width, canvas.height);

                // Dibujar el contorno del objeto detectado
                if (data.contour) {
                    ctxCaptured.beginPath();
                    ctxCaptured.moveTo(data.contour[0][0], data.contour[0][1]);
                    data.contour.forEach(point => ctxCaptured.lineTo(point[0], point[1]));
                    ctxCaptured.closePath();
                    ctxCaptured.strokeStyle = 'green';
                    ctxCaptured.lineWidth = 3;
                    ctxCaptured.stroke();
                }

                $('#result-camera').html(
                    `<b>Predicción:</b> ${data.predicted_class}<br><b>Confianza:</b> ${data.confidence_percentage}%`
                );
            },
            error: function (error) {
                loader.hide();
                console.error("Error:", error);
            }
        });
    });

    // Mostrar vista previa de la imagen subida
    $('#imageUpload').change(function () {
        const reader = new FileReader();
        reader.onload = function (e) {
            $('#uploaded-image').attr('src', e.target.result).show();
            $('#result-upload').html('');
        };
        reader.readAsDataURL(this.files[0]);
    });

    // Predicción desde una imagen subida
    $('#btn-predict-upload').click(function () {
        const form_data = new FormData($('#upload-file')[0]);
        loader.show();

        $.ajax({
            type: 'POST',
            url: '/predict',
            data: form_data,
            contentType: false,
            processData: false,
            success: function (data) {
                loader.hide();
                $('#result-upload').html(
                    `<b>Predicción:</b> ${data.predicted_class}<br><b>Confianza:</b> ${data.confidence_percentage}%`
                );
            },
            error: function (error) {
                loader.hide();
                console.error("Error:", error);
            }
        });
    });

    startCamera();
});
