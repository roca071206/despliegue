/**
 * escaner.js — Escáner de código de barras
 * - Cámara en vivo: requiere 5 lecturas consistentes antes de aceptar el código
 * - Imagen subida: procesa directamente la foto con QuaggaJS
 */

document.addEventListener('DOMContentLoaded', function () {
(function () {
    'use strict';

    var camaraActiva   = false;
    var ultimoCodigo   = '';
    var productoActual = null;
    var lecturas       = {};
    var LECTURAS_REQUERIDAS = 5;

    function el(id) { return document.getElementById(id); }

    var btnActivar      = el('btn-activar-camara');
    var btnDetener      = el('btn-detener-camara');
    var btnBuscarManual = el('btn-buscar-manual-codigo');
    var btnLimpiar      = el('btn-limpiar-scanner');
    var inputDisplay    = el('scanner-codigo-display');
    var scannerArea     = el('scanner-area');
    var instruccion     = el('scanner-instruccion');
    var resultado       = el('scanner-resultado');
    var inputImagen     = el('scanner-input-imagen');
    var btnSubirImagen  = el('btn-subir-imagen');
    var previewImagen   = el('scanner-preview-imagen');

    var modalStock          = bootstrap.Modal.getOrCreateInstance(el('modalActualizarStock'));
    var stockNombre         = el('stock-modal-nombre');
    var stockActual         = el('stock-modal-actual');
    var stockCantidad       = el('stock-modal-cantidad');
    var stockError          = el('stock-modal-error');
    var btnGuardarStock     = el('btn-guardar-stock');
    var btnCancelarStock    = el('btn-cancelar-stock');
    var btnCerrarStockModal = el('btn-cerrar-stock-modal');

    function getCsrf() {
        var c = document.cookie.split('; ').find(function(r){ return r.startsWith('csrftoken='); });
        return c ? c.split('=')[1] : '';
    }

    // ── CAMARA EN VIVO ────────────────────────────────────────────
    btnActivar.addEventListener('click', iniciarQuagga);
    btnDetener.addEventListener('click', detenerQuagga);
    btnLimpiar.addEventListener('click', resetScanner);
    btnBuscarManual.addEventListener('click', function () {
        if (ultimoCodigo) buscarCodigo(ultimoCodigo);
    });

    function iniciarQuagga() {
        if (typeof Quagga === 'undefined') {
            mostrarResultado('error', '<i class="fa-solid fa-triangle-exclamation me-1"></i> La librería del escáner no cargó. Recarga la página.');
            return;
        }
        lecturas = {};
        scannerArea.style.display = 'block';
        btnActivar.style.display  = 'none';
        btnDetener.style.display  = 'inline-block';
        setInstruccion('warning', '<i class="fa-solid fa-spinner fa-spin fa-lg"></i><span>Iniciando cámara...</span>');

        Quagga.init({
            inputStream: {
                name: 'Live',
                type: 'LiveStream',
                target: document.getElementById('interactive'),
                constraints: {
                    width:      { ideal: 1280 },
                    height:     { ideal: 720 },
                    facingMode: 'environment',
                },
            },
            locator:      { patchSize: 'large', halfSample: false },
            numOfWorkers: navigator.hardwareConcurrency || 4,
            frequency:    15,
            decoder: {
                readers:  ['ean_reader', 'ean_8_reader', 'code_128_reader', 'upc_reader', 'upc_e_reader'],
                multiple: false,
            },
            locate: true,
        }, function (err) {
            if (err) {
                detenerQuagga();
                var msg = String(err.message || err);
                if (msg.toLowerCase().includes('permission')) {
                    mostrarResultado('error', '<i class="fa-solid fa-ban me-1"></i> Permiso de cámara denegado. Habilítalo en tu navegador.');
                } else {
                    mostrarResultado('error', '<i class="fa-solid fa-triangle-exclamation me-1"></i> No se pudo acceder a la cámara: ' + msg);
                }
                return;
            }
            Quagga.start();
            camaraActiva = true;
            setInstruccion('success', '<i class="fa-solid fa-circle-check fa-lg"></i><span>Cámara activa. Apunta al código de barras y mantén el producto quieto.</span>');
        });

        Quagga.onDetected(function (data) {
            var codigo = data.codeResult.code;
            if (!codigo || !/^\d{7,14}$/.test(codigo)) return;

            lecturas[codigo] = (lecturas[codigo] || 0) + 1;
            var progreso = lecturas[codigo];

            if (progreso < LECTURAS_REQUERIDAS) {
                setInstruccion('warning',
                    '<i class="fa-solid fa-spinner fa-spin fa-lg"></i>' +
                    '<span>Confirmando código <strong>' + codigo + '</strong>... (' + progreso + '/' + LECTURAS_REQUERIDAS + ')</span>'
                );
                return;
            }

            if (codigo === ultimoCodigo) return;
            ultimoCodigo = codigo;
            inputDisplay.value = codigo;
            inputDisplay.classList.add('border-success');
            btnBuscarManual.style.display = 'inline-block';
            detenerQuagga();
            buscarCodigo(codigo);
        });
    }

    function detenerQuagga() {
        if (typeof Quagga !== 'undefined') { try { Quagga.stop(); } catch(e) {} }
        lecturas     = {};
        camaraActiva = false;
        scannerArea.style.display = 'none';
        btnActivar.style.display  = 'inline-block';
        btnDetener.style.display  = 'none';
        setInstruccion('info', '<i class="fa-solid fa-circle-info fa-lg"></i><span>Haz clic en <strong>Activar cámara</strong> y apunta al código de barras del producto.</span>');
    }

    // ── ESCANEAR DESDE IMAGEN ─────────────────────────────────────
    btnSubirImagen.addEventListener('click', function () {
        inputImagen.value = '';
        inputImagen.click();
    });

    inputImagen.addEventListener('change', function () {
        var file = this.files[0];
        if (!file || !file.type.startsWith('image/')) return;

        var url = URL.createObjectURL(file);
        previewImagen.src           = url;
        previewImagen.style.display = 'block';
        mostrarResultado('loading', '<i class="fa-solid fa-spinner fa-spin me-1"></i> Procesando imagen...');
        setInstruccion('warning', '<i class="fa-solid fa-spinner fa-spin fa-lg"></i><span>Analizando imagen...</span>');

        setTimeout(function () { escanearDesdeImagen(url, file); }, 300);
    });

    function escanearDesdeImagen(objectUrl, file) {
        if (typeof Quagga === 'undefined') {
            mostrarResultado('error', '<i class="fa-solid fa-triangle-exclamation me-1"></i> Librería no disponible.');
            return;
        }
        Quagga.decodeSingle({
            decoder:  { readers: ['ean_reader', 'ean_8_reader', 'code_128_reader', 'upc_reader', 'upc_e_reader'], multiple: false },
            locator:  { patchSize: 'large', halfSample: false },
            locate:   true,
            src:      objectUrl,
        }, function (result) {
            URL.revokeObjectURL(objectUrl);
            if (result && result.codeResult && /^\d{7,14}$/.test(result.codeResult.code)) {
                confirmarCodigoImagen(result.codeResult.code, file);
            } else {
                reintentarEscaneoImagen(file);
            }
        });
    }

    function reintentarEscaneoImagen(file) {
        var url2 = URL.createObjectURL(file);
        Quagga.decodeSingle({
            decoder:  { readers: ['ean_reader', 'ean_8_reader', 'code_128_reader', 'upc_reader', 'upc_e_reader'] },
            locator:  { patchSize: 'medium', halfSample: true },
            locate:   true,
            src:      url2,
        }, function (result) {
            URL.revokeObjectURL(url2);
            if (result && result.codeResult && /^\d{7,14}$/.test(result.codeResult.code)) {
                confirmarCodigoImagen(result.codeResult.code, file);
            } else {
                setInstruccion('info', '<i class="fa-solid fa-circle-info fa-lg"></i><span>No se detectó código. Intenta con mejor iluminación.</span>');
                mostrarResultado('error',
                    '<i class="fa-solid fa-triangle-exclamation me-1"></i> No se pudo leer el código de barras.<br>' +
                    '<small class="text-muted">Consejos: buena luz, código horizontal, imagen nítida.</small><br><br>' +
                    '<button class="btn btn-outline-secondary btn-sm" id="btn-reintentar-imagen">' +
                    '  <i class="fa-solid fa-rotate me-1"></i> Subir otra imagen' +
                    '</button>'
                );
                document.getElementById('btn-reintentar-imagen').addEventListener('click', function() {
                    inputImagen.value = ''; inputImagen.click();
                });
            }
        });
    }

    function confirmarCodigoImagen(codigo, file) {
        ultimoCodigo = codigo;
        inputDisplay.value = codigo;
        inputDisplay.classList.add('border-success');
        btnBuscarManual.style.display = 'inline-block';
        setInstruccion('success', '<i class="fa-solid fa-circle-check fa-lg"></i><span>Código detectado: <strong>' + codigo + '</strong></span>');
        buscarCodigo(codigo);
    }

    // ── LOGICA COMPARTIDA ─────────────────────────────────────────
    function resetScanner() {
        detenerQuagga();
        ultimoCodigo = ''; productoActual = null; lecturas = {};
        inputDisplay.value = '';
        inputDisplay.classList.remove('border-success');
        btnBuscarManual.style.display = 'none';
        resultado.style.display       = 'none';
        resultado.innerHTML           = '';
        previewImagen.style.display   = 'none';
        previewImagen.src             = '';
        inputImagen.value             = '';
    }

    function buscarCodigo(codigo) {
        mostrarResultado('loading', '<i class="fa-solid fa-spinner fa-spin me-1"></i> Buscando: <strong>' + codigo + '</strong>');
        fetch('/productos/buscar-codigo/?codigo=' + encodeURIComponent(codigo), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status === 'encontrado') {
                productoActual = data;
                mostrarResultado('encontrado',
                    '<div class="d-flex align-items-center gap-2 mb-2">' +
                    '  <i class="fa-solid fa-circle-check text-success fa-lg"></i>' +
                    '  <strong class="text-success">Producto encontrado en el sistema</strong>' +
                    '</div>' +
                    '<table class="table table-sm table-bordered mb-3">' +
                    '  <tr><th>Nombre</th><td>' + data.nombre + '</td></tr>' +
                    '  <tr><th>Marca</th><td>' + data.marca + '</td></tr>' +
                    '  <tr><th>Stock actual</th><td><strong>' + data.stock_actual + '</strong> unidades</td></tr>' +
                    '  <tr><th>Precio</th><td>$' + data.precio + '</td></tr>' +
                    '</table>' +
                    '<button class="btn btn-primary w-100" id="btn-abrir-actualizar-stock">' +
                    '  <i class="fa-solid fa-plus me-1"></i> Actualizar stock' +
                    '</button>'
                );
                el('btn-abrir-actualizar-stock').addEventListener('click', abrirModalStock);
            } else if (data.status === 'nuevo') {
                var nom  = data.nombre_sugerido || '';
                var info = nom
                    ? '<p class="mb-1">Encontrado en base pública: <strong>' + nom + '</strong></p>'
                    : '<p class="text-muted small mb-1">Sin información pública para este código.</p>';
                mostrarResultado('nuevo',
                    '<div class="d-flex align-items-center gap-2 mb-2">' +
                    '  <i class="fa-solid fa-circle-exclamation text-warning fa-lg"></i>' +
                    '  <strong class="text-warning">Producto no registrado</strong>' +
                    '</div>' + info +
                    '<p class="text-muted small mb-3">Código: <code>' + codigo + '</code></p>' +
                    '<button class="btn btn-success w-100" id="btn-ir-crear-producto">' +
                    '  <i class="fa-solid fa-plus me-1"></i> Crear producto nuevo' +
                    '</button>'
                );
                el('btn-ir-crear-producto').addEventListener('click', function () { irATabManual(nom, codigo); });
            } else {
                mostrarResultado('error', '<i class="fa-solid fa-triangle-exclamation me-1"></i> ' + (data.mensaje || 'Error.'));
            }
        })
        .catch(function() {
            mostrarResultado('error', '<i class="fa-solid fa-wifi me-1"></i> Error de conexión.');
        });
    }

    function irATabManual(nombre, codigoBarras) {
        bootstrap.Tab.getOrCreateInstance(el('tab-manual-btn')).show();
        if (nombre) { var inp = el('add_nombre'); if (inp) { inp.value = nombre; inp.focus(); } }
        var inpCod = el('add_codigo_barras');
        if (inpCod && codigoBarras) { inpCod.value = codigoBarras; }
    }

    function abrirModalStock() {
        if (!productoActual) return;
        stockNombre.textContent  = productoActual.nombre;
        stockActual.textContent  = productoActual.stock_actual;
        stockCantidad.value      = '';
        stockError.style.display = 'none';
        modalStock.show();
    }
    function cerrarModalStock() {
        modalStock.hide();
        // Limpiar backdrop residual por si queda huerfano (modal static)
        document.querySelectorAll(".modal-backdrop").forEach(function(b) { b.remove(); });
        document.body.classList.remove("modal-open");
        document.body.style.removeProperty("overflow");
        document.body.style.removeProperty("padding-right");
    }
    btnCancelarStock.addEventListener('click', cerrarModalStock);
    btnCerrarStockModal.addEventListener('click', cerrarModalStock);

    btnGuardarStock.addEventListener('click', function () {
        var cantidad = parseInt(stockCantidad.value, 10);
        if (!cantidad || cantidad < 1) {
            stockError.textContent = '⚠ Ingresa una cantidad válida (mínimo 1).';
            stockError.style.display = 'block'; return;
        }
        stockError.style.display  = 'none';
        btnGuardarStock.disabled  = true;
        btnGuardarStock.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Guardando...';

        fetch('/productos/actualizar-stock-escaner/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf(), 'X-Requested-With': 'XMLHttpRequest' },
            body: JSON.stringify({ id: productoActual.id, cantidad: cantidad }),
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            btnGuardarStock.disabled  = false;
            btnGuardarStock.innerHTML = '<i class="fa-solid fa-floppy-disk me-1"></i> Guardar';
            if (data.status === 'ok') {
                cerrarModalStock();
                productoActual.stock_actual = data.stock_nuevo;
                mostrarResultado('exito',
                    '<div class="d-flex align-items-center gap-2 mb-2">' +
                    '  <i class="fa-solid fa-circle-check text-success fa-lg"></i>' +
                    '  <strong class="text-success">Stock actualizado correctamente</strong>' +
                    '</div>' +
                    '<p class="mb-1"><strong>' + data.nombre + '</strong></p>' +
                    '<p class="text-muted mb-3">Nuevo stock: <strong class="text-dark">' + data.stock_nuevo + '</strong> unidades</p>' +
                    '<button class="btn btn-outline-success btn-sm" id="btn-escanear-otro">' +
                    '  <i class="fa-solid fa-barcode me-1"></i> Escanear otro' +
                    '</button>'
                );
                el('btn-escanear-otro').addEventListener('click', resetScanner);
                setTimeout(function() { window.location.reload(); }, 2500);
            } else {
                stockError.textContent   = '⚠ ' + (data.mensaje || 'Error al actualizar.');
                stockError.style.display = 'block';
            }
        })
        .catch(function() {
            btnGuardarStock.disabled  = false;
            btnGuardarStock.innerHTML = '<i class="fa-solid fa-floppy-disk me-1"></i> Guardar';
            stockError.textContent   = '⚠ Error de conexión.';
            stockError.style.display = 'block';
        });
    });

    function mostrarResultado(tipo, html) {
        resultado.style.display = 'block';
        var clases = { loading: 'alert alert-secondary', encontrado: 'alert alert-success', nuevo: 'alert alert-warning', error: 'alert alert-danger', exito: 'alert alert-success' };
        resultado.className = clases[tipo] || 'alert alert-secondary';
        resultado.innerHTML = html;
    }
    function setInstruccion(tipo, html) {
        var clases = { info: 'alert alert-info d-flex align-items-center gap-2 mb-3', warning: 'alert alert-warning d-flex align-items-center gap-2 mb-3', success: 'alert alert-success d-flex align-items-center gap-2 mb-3' };
        instruccion.className = clases[tipo] || clases.info;
        instruccion.innerHTML = html;
    }
//hola
    var modalAgregar = document.getElementById('modalAgregar');
    if (modalAgregar) {
        modalAgregar.addEventListener('hidden.bs.modal', resetScanner);
        el('tab-manual-btn').addEventListener('shown.bs.tab', function () { if (camaraActiva) detenerQuagga(); });
    }

})();
}); // DOMContentLoaded