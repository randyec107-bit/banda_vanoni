// Función para copiar al portapapeles
function copyToClipboard(text) {
    // Crear un elemento temporal de texto
    var tempInput = document.createElement("input");
    tempInput.value = text;
    document.body.appendChild(tempInput);
    
    // Seleccionar y copiar el texto
    tempInput.select();
    tempInput.setSelectionRange(0, 99999); // Para dispositivos móviles
    
    try {
        var successful = document.execCommand("copy");
        if (successful) {
            // Mostrar notificación temporal
            showNotification('✅ Número de guía copiado: ' + text);
        } else {
            showNotification('❌ Error al copiar');
        }
    } catch (err) {
        console.error('Error al copiar: ', err);
        showNotification('❌ Error al copiar');
    }
    
    // Limpiar
    document.body.removeChild(tempInput);
}

// Función para mostrar notificación
function showNotification(message) {
    // Crear elemento de notificación
    var notification = document.createElement("div");
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4CAF50;
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 10000;
        font-weight: bold;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        animation: fadeInOut 3s ease-in-out;
    `;
    notification.textContent = message;
    
    // Agregar al documento
    document.body.appendChild(notification);
    
    // Remover después de 3 segundos
    setTimeout(function() {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Agregar estilos CSS para la animación
var style = document.createElement('style');
style.textContent = `
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateY(-20px); }
        10% { opacity: 1; transform: translateY(0); }
        90% { opacity: 1; transform: translateY(0); }
        100% { opacity: 0; transform: translateY(-20px); }
    }
`;
document.head.appendChild(style);

console.log('✅ Script de copy automático cargado');