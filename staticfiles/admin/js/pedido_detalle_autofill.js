(function($) {
    'use strict';
    
    console.log('🔔 Cargando script de autocompletado...');
    
    // Función para obtener la URL base
    function getBaseUrl() {
        return window.location.origin;
    }
    
    // Datos en caché para productos y lotes
    var productoCache = {};
    var loteCache = {};
    
    // Función para obtener datos del producto
    function obtenerDatosProducto(productoId, callback) {
        if (!productoId) {
            callback(null);
            return;
        }
        
        if (productoCache[productoId]) {
            callback(productoCache[productoId]);
            return;
        }
        
        var url = getBaseUrl() + '/pedidos/admin/api/producto/' + productoId + '/';
        console.log('🔔 Solicitando datos del producto:', url);
        
        $.ajax({
            url: url,
            type: 'GET',
            success: function(data) {
                console.log('✅ Datos del producto recibidos:', data);
                productoCache[productoId] = data;
                callback(data);
            },
            error: function(xhr, status, error) {
                console.error('❌ Error obteniendo datos del producto:', error);
                callback(null);
            }
        });
    }
    
    // Función para obtener datos del lote
    function obtenerDatosLote(loteId, callback) {
        if (!loteId) {
            callback(null);
            return;
        }
        
        if (loteCache[loteId]) {
            callback(loteCache[loteId]);
            return;
        }
        
        var url = getBaseUrl() + '/pedidos/admin/api/lote/' + loteId + '/';
        console.log('🔔 Solicitando datos del lote:', url);
        
        $.ajax({
            url: url,
            type: 'GET',
            success: function(data) {
                console.log('✅ Datos del lote recibidos:', data);
                loteCache[loteId] = data;
                callback(data);
            },
            error: function(xhr, status, error) {
                console.error('❌ Error obteniendo datos del lote:', error);
                callback(null);
            }
        });
    }
    
    // Función para actualizar campos de visualización
    function actualizarCampoReadonly($row, selector, valor) {
        var $campo = $row.find(selector);
        if ($campo.length) {
            $campo.text(valor || '-');
        }
    }
    
    // Función principal para actualizar todos los campos
    function actualizarCamposDetalle($row) {
        var productoId = $row.find('select[id$="-producto"]').val();
        var loteId = $row.find('select[id$="-lote"]').val();
        var cantidad = parseInt($row.find('input[id$="-cantidad"]').val()) || 0;
        
        console.log('🔔 Actualizando campos - Producto:', productoId, 'Lote:', loteId, 'Cantidad:', cantidad);
        
        // Actualizar campos del producto
        if (productoId) {
            obtenerDatosProducto(productoId, function(productoData) {
                if (productoData) {
                    // Actualizar campos de visualización
                    actualizarCampoReadonly($row, '.field-nombre_producto_auto .readonly', productoData.nombre);
                    actualizarCampoReadonly($row, '.field-precio1_auto .readonly', '$' + (parseFloat(productoData.precio1) || 0).toFixed(2));
                    actualizarCampoReadonly($row, '.field-registro_sanitario_auto .readonly', productoData.registro_sanitario);
                    actualizarCampoReadonly($row, '.field-ubicacion_auto .readonly', productoData.ubicacion);
                    
                    // Actualizar campos ocultos (para guardar)
                    $row.find('input[id$="-nombre_producto"]').val(productoData.nombre || '');
                    $row.find('input[id$="-precio1"]').val(parseFloat(productoData.precio1) || 0);
                    $row.find('input[id$="-registro_sanitario"]').val(productoData.registro_sanitario || '');
                    $row.find('input[id$="-ubicacion"]').val(productoData.ubicacion || '');
                    
                    // Calcular y actualizar subtotal
                    var precio = parseFloat(productoData.precio1) || 0;
                    var subtotal = precio * cantidad;
                    actualizarCampoReadonly($row, '.field-subtotal_auto .readonly', '$' + subtotal.toFixed(2));
                } else {
                    limpiarCamposProducto($row);
                }
            });
        } else {
            limpiarCamposProducto($row);
        }
        
        // Actualizar campos del lote
        if (loteId) {
            obtenerDatosLote(loteId, function(loteData) {
                if (loteData) {
                    // Actualizar campos de visualización del lote
                    actualizarCampoReadonly($row, '.field-fecha_elaboracion_auto .readonly', loteData.fecha_elaboracion);
                    actualizarCampoReadonly($row, '.field-vigencia_lote_auto .readonly', loteData.vigencia_lote);
                    actualizarCampoReadonly($row, '.field-stock_disponible .readonly', loteData.cantidad + ' unidades');
                    
                    // Actualizar campos ocultos
                    if (loteData.fecha_elaboracion) {
                        $row.find('input[id$="-fecha_elaboracion"]').val(loteData.fecha_elaboracion);
                    }
                    if (loteData.vigencia_lote) {
                        $row.find('input[id$="-vigencia_lote"]').val(loteData.vigencia_lote);
                    }
                } else {
                    limpiarCamposLote($row);
                }
            });
        } else {
            limpiarCamposLote($row);
        }
    }
    
    // Función para limpiar campos del producto
    function limpiarCamposProducto($row) {
        actualizarCampoReadonly($row, '.field-nombre_producto_auto .readonly', '-');
        actualizarCampoReadonly($row, '.field-precio1_auto .readonly', '$0.00');
        actualizarCampoReadonly($row, '.field-registro_sanitario_auto .readonly', '-');
        actualizarCampoReadonly($row, '.field-ubicacion_auto .readonly', '-');
        actualizarCampoReadonly($row, '.field-subtotal_auto .readonly', '$0.00');
        
        $row.find('input[id$="-nombre_producto"]').val('');
        $row.find('input[id$="-precio1"]').val('0');
        $row.find('input[id$="-registro_sanitario"]').val('');
        $row.find('input[id$="-ubicacion"]').val('');
    }
    
    // Función para limpiar campos del lote
    function limpiarCamposLote($row) {
        actualizarCampoReadonly($row, '.field-fecha_elaboracion_auto .readonly', '-');
        actualizarCampoReadonly($row, '.field-vigencia_lote_auto .readonly', '-');
        actualizarCampoReadonly($row, '.field-stock_disponible .readonly', '0 unidades');
        
        $row.find('input[id$="-fecha_elaboracion"]').val('');
        $row.find('input[id$="-vigencia_lote"]').val('');
    }
    
    // Inicializar cuando el documento está listo
    $(document).ready(function() {
        console.log('🔔 Inicializando autocompletado...');
        
        // Actualizar campos cuando cambia producto, lote o cantidad
        $(document).on('change', 'select[id$="-producto"], select[id$="-lote"]', function() {
            var $row = $(this).closest('.dynamic-pedidodetalle');
            console.log('🔔 Cambio detectado en:', this.id);
            actualizarCamposDetalle($row);
        });
        
        $(document).on('input', 'input[id$="-cantidad"]', function() {
            var $row = $(this).closest('.dynamic-pedidodetalle');
            setTimeout(function() {
                actualizarCamposDetalle($row);
            }, 300);
        });
        
        // Actualizar todas las filas existentes al cargar
        setTimeout(function() {
            $('.dynamic-pedidodetalle').each(function() {
                actualizarCamposDetalle($(this));
            });
        }, 1000);
    });
    
    // También actualizar cuando se añaden nuevas filas
    django.jQuery(document).on('formset:added', function(event, $row, formsetName) {
        if (formsetName.indexOf('pedidodetalle') !== -1) {
            console.log('🔔 Nueva fila añadida');
            setTimeout(function() {
                actualizarCamposDetalle($row);
            }, 500);
            
            // Configurar eventos para la nueva fila
            $row.find('select[id$="-producto"], select[id$="-lote"]').on('change', function() {
                actualizarCamposDetalle($row);
            });
            
            $row.find('input[id$="-cantidad"]').on('input', function() {
                setTimeout(function() {
                    actualizarCamposDetalle($row);
                }, 300);
            });
        }
    });
    
})(django.jQuery);