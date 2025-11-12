(function($) {
    'use strict';
    
    console.log('🔔 Inicializando sistema de posición para pedidos...');
    
    // Guardar la posición del scroll antes de enviar el formulario
    function guardarPosicionScroll() {
        try {
            var scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
            localStorage.setItem('pedido_scroll_position', scrollPosition.toString());
            console.log('💾 Posición guardada:', scrollPosition);
        } catch (e) {
            console.warn('⚠️ No se pudo guardar la posición:', e);
        }
    }
    
    // Restaurar la posición del scroll después de cargar la página
    function restaurarPosicionScroll() {
        try {
            var posicionGuardada = localStorage.getItem('pedido_scroll_position');
            if (posicionGuardada) {
                var posicion = parseInt(posicionGuardada);
                console.log('📖 Restaurando posición:', posicion);
                
                // Usar timeout para asegurar que el DOM esté completamente cargado
                setTimeout(function() {
                    if (posicion > 0) {
                        window.scrollTo(0, posicion);
                    }
                    // Limpiar después de restaurar
                    localStorage.removeItem('pedido_scroll_position');
                }, 300);
            }
        } catch (e) {
            console.warn('⚠️ No se pudo restaurar la posición:', e);
        }
    }
    
    // Función para detectar si estamos en una página de edición de pedido
    function esPaginaDePedido() {
        return window.location.pathname.includes('/pedidos/pedido/') && 
               (window.location.pathname.includes('/change/') || window.location.pathname.includes('/add/'));
    }
    
    // Inicializar cuando el documento está listo
    $(document).ready(function() {
        // Solo ejecutar en páginas de pedidos
        if (!esPaginaDePedido()) {
            return;
        }
        
        console.log('📄 Página de pedido cargada, restaurando posición...');
        
        // Restaurar posición después de un breve delay
        setTimeout(restaurarPosicionScroll, 500);
        
        // Guardar posición antes de enviar cualquier formulario
        $('form').on('submit', function() {
            console.log('🔄 Formulario enviándose, guardando posición...');
            guardarPosicionScroll();
        });
        
        // Guardar posición cuando se hace clic en botones de guardar
        $('input[type="submit"]').on('click', function() {
            console.log('🖱️ Botón de guardar clickeado:', this.name);
            guardarPosicionScroll();
        });
        
        // Guardar posición cuando se añaden/eliminan filas en los inlines
        django.jQuery(document).on('formset:added formset:removed', function() {
            console.log('📋 Formset cambiado, guardando posición...');
            setTimeout(guardarPosicionScroll, 100);
        });
        
        // Guardar posición cuando se cambia entre pestañas (si las hay)
        $(document).on('click', '.form-row a, .inline-group h2', function() {
            setTimeout(guardarPosicionScroll, 50);
        });
        
        // Guardar posición periódicamente durante la edición (cada 3 segundos)
        setInterval(function() {
            if (document.activeElement && 
                (document.activeElement.tagName === 'INPUT' || 
                 document.activeElement.tagName === 'SELECT' ||
                 document.activeElement.tagName === 'TEXTAREA')) {
                guardarPosicionScroll();
            }
        }, 3000);
    });
    
    // También guardar cuando el usuario está a punto de salir de la página
    window.addEventListener('beforeunload', function() {
        if (esPaginaDePedido()) {
            guardarPosicionScroll();
        }
    });
    
    // Manejar navegación con el botón atrás/adelante
    window.addEventListener('pageshow', function(event) {
        if (event.persisted && esPaginaDePedido()) {
            setTimeout(restaurarPosicionScroll, 200);
        }
    });
    
})(django.jQuery);