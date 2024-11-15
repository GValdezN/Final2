$(document).ready(function () {
    // Inicialización
    $('.image-section').hide();
    $('.loader').hide();
    $('#result-upload').hide();
    $('#result-camera').hide();

    // Cambiar entre secciones de la barra de navegación
    $('a.nav-link').click(function (e) {
        e.preventDefault();
        const target = $(this).attr('href');

        // Ocultar ambas secciones
        $('#upload-section').hide();
        $('#camera-section').hide();

        // Mostrar la sección seleccionada
        $(target).show();
    });

    // Opción 1: Subir Imagen
    function readURL(input) {
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            reader.onload = function (e) {
                $('#imagePreview').css('background-image', 'url(' + e.target.result + ')');
                $('#imagePreview').hide();
                $('#imagePreview').fadeIn(650);
            };
            reader.readAsDataURL(input.files[0]);
        }
    }

    $("#imageUpload").change(function () {
        $('.image-section').show();
        $('#btn-predict').show();
        $('#result-upload').text('');
        $('#result-upload').hide();
        readURL(this);
    });

    // Predicción al subir imagen
    $('#btn-predict').click(function () {
        var form_data = new FormData($('#upload-file')[0]);

        // Mostrar animación de carga
        $(this).hide();
        $('.loader').show();

        // Llamada al endpoint de predicción
        $.ajax({
            type: 'POST',
            url: '/predict',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            async: true,
            success: function (data) {
                // Mostrar resultados
                $('.loader').hide();
                $('#result-upload').fadeIn(1000);
                let predictedClass = data.predicted_class;
                let confidencePercentage = data.confidence_percentage;
                $('#result-upload').html(
                    '<b>Predicción:</b> ' +
                    predictedClass +
                    '<br><b>Confianza:</b> ' +
                    confidencePercentage +
                    '%'
                );
            },
        });
    });

    // Opción 2: Cámara en Tiempo Real
    function updateCameraResult(predictedClass, confidencePercentage) {
        $('#result-camera').html(
            '<b>Predicción:</b> ' +
            predictedClass +
            '<br><b>Confianza:</b> ' +
            confidencePercentage +
            '%'
        );
        $('#result-camera').fadeIn(1000);
    }

    // Stream de cámara (si deseas actualizaciones dinámicas desde backend)
    setInterval(function () {
        $.ajax({
            type: 'GET',
            url: '/camera_predict',
            success: function (data) {
                let predictedClass = data.predicted_class;
                let confidencePercentage = data.confidence_percentage;
                updateCameraResult(predictedClass, confidencePercentage);
            },
        });
    }, 3000); // Actualizar cada 3 segundos
});
