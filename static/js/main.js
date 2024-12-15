$(document).ready(function(){
    const video=document.getElementById("camera-stream")
    const canvas=document.getElementById("camera-canvas")
    const capturedCanvas=document.getElementById("captured-image")
    const loader=$(".loader")
    let isCameraActive=false
    let lastImagePath=null
    async function startCamera(){
        try{
            const stream=await navigator.mediaDevices.getUserMedia({video:true})
            video.srcObject=stream
            isCameraActive=true
        }catch(err){
            console.error("Error al acceder a la cámara:",err)
            alert("Verifica los permisos de la cámara en el navegador.")
        }
    }
    function sendFeedback(descriptionSelector,likeSelector,sectionSelector){
        const feedbackData={
            description:$(descriptionSelector).val(),
            like:$(likeSelector).is(":checked")?1:0,
            image_path:lastImagePath
        }
        if(!feedbackData.description.trim()){
            alert("La descripción no puede estar vacía.")
            return
        }
        $.ajax({
            type:"POST",
            url:"/save_feedback",
            contentType:"application/json",
            data:JSON.stringify(feedbackData),
            success:function(){
                alert("Feedback guardado correctamente.")
                $(sectionSelector).hide()
                $(descriptionSelector).val("")
                $(likeSelector).prop("checked",false)
                startCamera()
            },
            error:function(){
                alert("Error al guardar el feedback.")
                startCamera()
            }
        })
    }
    $(".nav-toggle").click(function(e){
        e.preventDefault()
        const target=$(this).attr("href")
        $(".content-section").hide()
        $(target).show()
    })
    $("#btn-toggle-camera").click(function(){
        if(!isCameraActive){
            startCamera()
        }
    })
    $("#btn-capture").click(function(){
        if(!isCameraActive){
            alert("Primero activa la cámara.")
            return
        }
        const context=capturedCanvas.getContext("2d")
        capturedCanvas.width=video.videoWidth
        capturedCanvas.height=video.videoHeight
        context.drawImage(video,0,0,capturedCanvas.width,capturedCanvas.height)
        const imageData=capturedCanvas.toDataURL("image/png")
        loader.show()
        $.ajax({
            type:"POST",
            url:"/predict_feedback",
            contentType:"application/json",
            data:JSON.stringify({image_data:imageData}),
            success:function(response){
                loader.hide()
                $("#result-camera").html("<b>Predicción:</b> "+response.predicted_class+"<br><b>Confianza:</b> "+response.confidence_percentage+"%")
                lastImagePath=response.image_path
                $("#feedback-section").show()
            },
            error:function(){
                loader.hide()
                alert("Error durante la predicción.")
            }
        })
    })
    $("#btn-feedback").click(function(){
        sendFeedback("#feedback-description","#feedback-like","#feedback-section")
    })
    $("#imageUpload").change(function(){
        const file=this.files[0]
        if(file){
            const reader=new FileReader()
            reader.onload=function(e){
                $("#uploaded-image").attr("src",e.target.result).show()
                $("#feedback-section-upload").hide()
            }
            reader.readAsDataURL(file)
        }
    })
    $("#btn-predict-upload").click(function(){
        const file=$("#imageUpload")[0].files[0]
        if(!file){
            alert("Selecciona una imagen para subir.")
            return
        }
        const formData=new FormData()
        formData.append("file",file)
        loader.show()
        $.ajax({
            type:"POST",
            url:"/predict_feedback",
            data:formData,
            processData:false,
            contentType:false,
            success:function(response){
                loader.hide()
                $("#result-upload").html("<b>Predicción:</b> "+response.predicted_class+"<br><b>Confianza:</b> "+response.confidence_percentage+"%")
                $("#uploaded-image").attr("src",response.image_path).show()
                lastImagePath=response.image_path
                $("#feedback-section-upload").show()
            },
            error:function(){
                loader.hide()
                alert("Error durante la predicción.")
            }
        })
    })
    $("#btn-feedback-upload").click(function(){
        sendFeedback("#feedback-description-upload","#feedback-like-upload","#feedback-section-upload")
    })
    startCamera()
})
