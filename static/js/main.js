$(document).ready(function () {
    const video = document.getElementById('camera-stream');
    const canvas = document.getElementById('camera-canvas');
    const loader = $('.loader');

    // Alternar entre secciones
    $('a.nav-link').click(function (e) {
        e.preventDefault();
        const target = $(this).attr('href');
        $('.content-section').hide(); // Ocultar todas las secciones
        $(target).show(); // Mostrar la sección seleccionada
    });

    // Iniciar cámara al cargar
    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
        } catch (err) {
            console.error("Error al acceder a la cámara:", err);
            alert("No se pudo acceder a la cámara. Verifica los permisos.");
        }
    }

    // Predicción desde la cámara
    $('#btn-capture').click(function () {
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const imageData = canvas.toDataURL('image/jpeg');
        loader.show();

        $.ajax({
            type: 'POST',
            url: '/camera_predict',
            data: JSON.stringify({ image: imageData }),
            contentType: 'application/json',
            success: function (data) {
                loader.hide();
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
            $('#result-upload').html(''); // Limpiar resultados previos
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

    startCamera(); // Iniciar cámara al cargar
});
