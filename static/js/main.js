$(document).ready(function () {
    const video = document.getElementById("camera-stream");
    const canvas = document.getElementById("camera-canvas");
    const capturedCanvas = document.getElementById("captured-image");
    const loader = $(".loader");
    let isCameraActive = false;
    let lastImagePath = null;

    async function getCameras() {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === "videoinput");
        return videoDevices;
    }

    // Inicia la cámara con un dispositivo específico
    async function startCamera(deviceId) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { deviceId: { exact: deviceId } }
            });
            video.srcObject = stream;
            currentStream = stream;
            isCameraActive = true;
        } catch (err) {
            console.error("Error al acceder a la cámara:", err);
            alert("Verifica los permisos de la cámara en el navegador.");
        }
    }

    // Cambia entre la cámara delantera y trasera
    $("#btn-toggle-camera").click(async function () {
        if (!isCameraActive) {
            alert("Primero activa la cámara.");
            return;
        }

        // Detener la cámara actual si está activa
        if (currentStream) {
            const tracks = currentStream.getTracks();
            tracks.forEach(track => track.stop());
        }

        // Obtener las cámaras disponibles
        const cameras = await getCameras();
        const currentIndex = cameras.findIndex(camera => camera.deviceId === currentDeviceId);
        const nextCamera = cameras[(currentIndex + 1) % cameras.length]; // Cambia entre cámaras

        // Iniciar la nueva cámara
        currentDeviceId = nextCamera.deviceId;
        startCamera(currentDeviceId);
    });

    // Inicia la cámara al principio (por defecto cámara delantera)
    async function initializeCamera() {
        const cameras = await getCameras();
        if (cameras.length > 0) {
            currentDeviceId = cameras[0].deviceId;
            startCamera(currentDeviceId);
        } else {
            alert("No se encontraron cámaras.");
        }
    }

    initializeCamera(); // Inicia la cámara al cargar la página

    // Carga los feedbacks del usuario
    function loadFeedbacks() {
        $.ajax({
            type: "GET",
            url: "/my_feedbacks",
            success: function (response) {
                const feedbackList = response.feedbacks
                    .map(
                        (feedback) => `
                        <div style="margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;">
                            <p><b>ID:</b> ${feedback.opi_id}</p>
                            <p><b>Descripción:</b> ${feedback.opi_descripcion}</p>
                            <p><b>Me gusta:</b> ${feedback.opi_like ? "Sí" : "No"}</p>
                            <img src="${feedback.opi_imagen_ruta}" alt="Imagen asociada" style="max-width: 100%;">
                        </div>
                    `
                    )
                    .join("");
                $("#feedback-list").html(feedbackList);
            },
            error: function () {
                alert("Error al cargar los feedbacks.");
            },
        });
    }

    // Envía feedback a la base de datos
    function sendFeedback(descriptionSelector, likeSelector, sectionSelector) {
        const feedbackData = {
            description: $(descriptionSelector).val(),
            like: $(likeSelector).is(":checked") ? 1 : 0,
            image_path: lastImagePath,
        };
        if (!feedbackData.description.trim()) {
            alert("La descripción no puede estar vacía.");
            return;
        }
        $.ajax({
            type: "POST",
            url: "/save_feedback",
            contentType: "application/json",
            data: JSON.stringify(feedbackData),
            success: function () {
                alert("Feedback guardado correctamente.");
                $(sectionSelector).hide();
                $(descriptionSelector).val("");
                $(likeSelector).prop("checked", false);
                startCamera();
            },
            error: function () {
                alert("Error al guardar el feedback.");
                startCamera();
            },
        });
    }

    // Captura la imagen desde la cámara
    $("#btn-capture").click(function () {
        if (!isCameraActive) {
            alert("Primero activa la cámara.");
            return;
        }
        const context = capturedCanvas.getContext("2d");
        capturedCanvas.width = video.videoWidth;
        capturedCanvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, capturedCanvas.width, capturedCanvas.height);
        const imageData = capturedCanvas.toDataURL("image/png");
        loader.show();
        $.ajax({
            type: "POST",
            url: "/predict_feedback",
            contentType: "application/json",
            data: JSON.stringify({ image_data: imageData }),
            success: function (response) {
                loader.hide();
                $("#result-camera").html(
                    "<b>Predicción:</b> " +
                    response.predicted_class +
                    "<br><b>Confianza:</b> " +
                    response.confidence_percentage +
                    "%"
                );
                lastImagePath = response.image_path;

                // Mostrar sección para feedback de la predicción
                $("#feedback-section-camera").show();
            },
            error: function () {
                loader.hide();
                alert("Error durante la predicción.");
            },
        });
    });

    // Envía feedback de predicción
    $("#btn-feedback").click(function () {
        sendFeedback("#feedback-description", "#feedback-like", "#feedback-section-camera");
    });

    // Subida de imagen
    $("#imageUpload").change(function () {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                $("#uploaded-image").attr("src", e.target.result).show();
                $("#feedback-section-upload").hide();
            };
            reader.readAsDataURL(file);
        }
    });

    // Predicción de imagen cargada
    $("#btn-predict-upload").click(function () {
        const file = $("#imageUpload")[0].files[0];
        if (!file) {
            alert("Selecciona una imagen para subir.");
            return;
        }
        const formData = new FormData();
        formData.append("file", file);
        loader.show();
        $.ajax({
            type: "POST",
            url: "/predict_feedback",
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                loader.hide();
                $("#result-upload").html(
                    "<b>Predicción:</b> " +
                    response.predicted_class +
                    "<br><b>Confianza:</b> " +
                    response.confidence_percentage +
                    "%"
                );
                $("#uploaded-image").attr("src", response.image_path).show();
                lastImagePath = response.image_path;

                // Mostrar sección de feedback de imagen cargada
                $("#feedback-section-upload").show();
            },
            error: function () {
                loader.hide();
                alert("Error durante la predicción.");
            },
        });
    });

    // Envía feedback de imagen cargada
    $("#btn-feedback-upload").click(function () {
        sendFeedback("#feedback-description-upload", "#feedback-like-upload", "#feedback-section-upload");
    });

    // Elimina feedback por ID
    $("#btn-delete-feedback").click(function () {
        const feedbackId = $("#delete-feedback-id").val();
        if (!feedbackId) {
            alert("Por favor, ingresa un ID de feedback.");
            return;
        }
        $.ajax({
            type: "DELETE",
            url: `/delete_feedback/${feedbackId}`,
            success: function (response) {
                alert(response.message);
                loadFeedbacks();
            },
            error: function () {
                alert("Error al eliminar el feedback.");
            },
        });
    });

    // Modifica feedback por ID
    $("#btn-edit-feedback").click(function () {
        const feedbackId = $("#edit-feedback-id").val();
        const description = $("#edit-feedback-description").val();
        const like = $("#edit-feedback-like").val();

        if (!feedbackId || !description || (like !== "0" && like !== "1")) {
            alert("Por favor, completa todos los campos correctamente.");
            return;
        }
        $.ajax({
            type: "PUT",
            url: `/edit_feedback/${feedbackId}`,
            contentType: "application/json",
            data: JSON.stringify({ description, like }),
            success: function (response) {
                alert(response.message);
                loadFeedbacks();
            },
            error: function () {
                alert("Error al modificar el feedback.");
            },
        });
    });

    // Navegación entre secciones
    $(".nav-toggle").click(function (e) {
        e.preventDefault();
        const target = $(this).attr("href");
        $(".content-section").hide();
        $(target).show();
    });

    // Inicializar
    startCamera();
    loadFeedbacks();
});
