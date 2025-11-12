(function($) {
    'use strict';
    
    console.log('🔔 Cargando filtro de lotes por producto...');
    
    // Función para actualizar los lotes basados en el producto seleccionado
    function actualizarLotes($row) {
        var productoId = $row.find('select[id$="-producto"]').val();
        var $loteSelect = $row.find('select[id$="-lote"]');
        
        console.log('🔔 Actualizando lotes para producto:', productoId);
        
        if (productoId) {
            // Limpiar el select de lotes
            $loteSelect.empty();
            $loteSelect.append('<option value="">---------</option>');
            
            // Obtener los lotes del producto seleccionado via AJAX
            $.ajax({
                url: '/admin/api/lotes_por_producto/' + productoId + '/',
                type: 'GET',
                success: function(data) {
                    console.log('✅ Lotes recibidos:', data);
                    
                    // Agregar los lotes al select
                    $.each(data.lotes, function(index, lote) {
                        var optionText = lote.lote;
                        if (lote.vigencia_lote) {
                            optionText += ' (Vence: ' + lote.vigencia_lote + ')';
                        }
                        optionText += ' - Stock: ' + lote.cantidad;
                        
                        $loteSelect.append(
                            $('<option></option>').val(lote.id).text(optionText)
                        );
                    });
                    
                    // Disparar evento change para actualizar campos automáticos
                    $loteSelect.trigger('change');
                },
                error: function(xhr, status, error) {
                    console.error('❌ Error obteniendo lotes:', error);
                }
            });
        } else {
            // Si no hay producto seleccionado, limpiar lotes
            $loteSelect.empty();
            $loteSelect.append('<option value="">---------</option>');
            $loteSelect.trigger('change');
        }
    }
    
    // Inicializar cuando el documento está listo
    $(document).ready(function() {
        console.log('🔔 Inicializando filtro de lotes...');
        
        // Actualizar lotes cuando cambia el producto
        $(document).on('change', 'select[id$="-producto"]', function() {
            var $row = $(this).closest('.dynamic-pedidodetalle');
            console.log('🔔 Producto cambiado:', this.value);
            actualizarLotes($row);
        });
        
        // Actualizar todas las filas existentes al cargar
        setTimeout(function() {
            $('.dynamic-pedidodetalle').each(function() {
                var $row = $(this);
                var productoId = $row.find('select[id$="-producto"]').val();
                if (productoId) {
                    actualizarLotes($row);
                }
            });
        }, 1000);
    });
    
    // También actualizar cuando se añaden nuevas filas
    django.jQuery(document).on('formset:added', function(event, $row, formsetName) {
        if (formsetName.indexOf('pedidodetalle') !== -1) {
            console.log('🔔 Nueva fila añadida, configurando filtro de lotes...');
            
            // Configurar evento para la nueva fila
            $row.find('select[id$="-producto"]').on('change', function() {
                actualizarLotes($row);
            });
        }
    });
    
})(django.jQuery);