// MODULO DE VENTAS

var carrito = [];

document.addEventListener('DOMContentLoaded', function () {

    var modalCrear = document.getElementById('modalCrearVenta');
    if (!modalCrear) return;

    modalCrear.addEventListener('shown.bs.modal', function () {
        var input = document.getElementById('inputClienteCrear');
        if (input) {
            input.oninput = function () {
                validarCliente(this, document.getElementById('feedbackCliente'), document.getElementById('contadorCliente'));
            };
        }
    });

    modalCrear.addEventListener('hidden.bs.modal', function () {
        carrito = [];
        renderCarrito();
        var input = document.getElementById('inputClienteCrear');
        if (input) input.value = '';
        var fc = document.getElementById('feedbackCliente');
        if (fc) fc.textContent = '';
        var cc = document.getElementById('contadorCliente');
        if (cc) cc.textContent = '0/30 caracteres';
        var se = document.getElementById('selectEstado');
        if (se) se.value = '';
        var fe = document.getElementById('feedbackEstado');
        if (fe) fe.textContent = '';
        var bus = document.getElementById('busquedaProductos');
        if (bus) {
            bus.value = '';
            document.querySelectorAll('.producto-card').forEach(function (c) { c.style.display = 'block'; });
        }
    });

    var busqueda = document.getElementById('busquedaProductos');
    if (busqueda) {
        busqueda.addEventListener('input', function () {
            var term = this.value.toLowerCase();
            document.querySelectorAll('.producto-card').forEach(function (card) {
                card.style.display = card.getAttribute('data-nombre').includes(term) ? 'block' : 'none';
            });
        });
    }

    document.querySelectorAll('.input-cliente-editar').forEach(function (input) {
        var feedback = input.parentElement.querySelector('.feedback-editar');
        var contador = input.parentElement.querySelector('.contador-editar');
        input.oninput = function () { validarCliente(this, feedback, contador); };
    });

    var formCrear = document.getElementById('formCrearVenta');
    if (formCrear) {
        formCrear.removeAttribute('onsubmit');
        formCrear.addEventListener('submit', function (e) {
            if (!validarFormVenta()) { e.preventDefault(); }
        });
    }

    document.querySelectorAll('[id^="formEditarVenta"]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            var cliente   = form.querySelector('input[name="cliente"]');
            var estado    = form.querySelector('select[name="estado"]');
            var feedbackC = form.querySelector('.feedback-editar');
            var feedbackE = form.querySelector('.feedback-estado-editar');
            var valido    = true;
            if (feedbackC) feedbackC.textContent = '';
            if (feedbackE) feedbackE.textContent = '';
            if (!cliente.value.trim()) {
                if (feedbackC) feedbackC.textContent = 'El nombre del cliente es obligatorio';
                valido = false;
            } else if (cliente.value.trim().length < 3) {
                if (feedbackC) feedbackC.textContent = 'El nombre debe tener al menos 3 caracteres';
                valido = false;
            }
            if (!estado.value) {
                if (feedbackE) feedbackE.textContent = 'Debes seleccionar un estado';
                valido = false;
            }
            if (!valido) e.preventDefault();
        });
    });
});


function validarCliente(input, feedbackEl, contadorEl) {
    if (/[0-9]/.test(input.value)) {
        input.value = input.value.replace(/[0-9]/g, '');
        if (feedbackEl) feedbackEl.textContent = 'No se permiten números';
    } else if (/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/.test(input.value)) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
        if (feedbackEl) feedbackEl.textContent = 'No se permiten caracteres especiales';
    } else {
        if (feedbackEl) feedbackEl.textContent = '';
    }
    if (input.value.length > 30) input.value = input.value.substring(0, 30);
    if (contadorEl) contadorEl.textContent = input.value.length + '/30 caracteres';
}


function agregarProducto(id, nombre, precio, stock) {
    id = String(id);
    var stockNum = parseInt(stock) || 999;
    for (var i = 0; i < carrito.length; i++) {
        if (carrito[i].id === id) {
            var alerta = document.getElementById('alertaProductoDuplicado');
            if (alerta) { alerta.classList.remove('d-none'); setTimeout(function () { alerta.classList.add('d-none'); }, 2500); }
            return;
        }
    }
    var precioNum = parseFloat(String(precio).replace(',', '.')) || 0;
    carrito.push({ id: id, nombre: nombre, precio: precioNum, cantidad: 1, stock: stockNum });
    var alerta = document.getElementById('alertaCarritoVacio');
    if (alerta) alerta.classList.add('d-none');
    renderCarrito();
}


function sumar(id) {
    for (var i = 0; i < carrito.length; i++) {
        if (carrito[i].id === id) {
            if (carrito[i].cantidad < carrito[i].stock) { carrito[i].cantidad++; renderCarrito(); }
            return;
        }
    }
}

function restar(id) {
    for (var i = 0; i < carrito.length; i++) {
        if (carrito[i].id === id) {
            if (carrito[i].cantidad > 1) { carrito[i].cantidad--; renderCarrito(); }
            else { eliminarProducto(id); }
            return;
        }
    }
}

function eliminarProducto(id) {
    carrito = carrito.filter(function (i) { return i.id !== id; });
    renderCarrito();
}


function renderCarrito() {
    var tbody         = document.getElementById('filasCarrito');
    var tabla         = document.getElementById('tablaCarrito');
    var msgVacio      = document.getElementById('msgCarritoVacio');
    var tituloCarrito = document.getElementById('tituloCarrito');
    var totalEl       = document.getElementById('totalCarrito');
    var camposOcultos = document.getElementById('camposOcultosProductos');
    if (!tbody) return;

    camposOcultos.innerHTML = '';

    if (carrito.length === 0) {
        msgVacio.classList.remove('d-none');
        tabla.classList.add('d-none');
        if (tituloCarrito) tituloCarrito.classList.add('d-none');
        totalEl.textContent = '$0';
        return;
    }

    msgVacio.classList.add('d-none');
    tabla.classList.remove('d-none');
    if (tituloCarrito) tituloCarrito.classList.remove('d-none');

    var total = 0;
    tbody.innerHTML = '';

    for (var k = 0; k < carrito.length; k++) {
        var item     = carrito[k];
        var subtotal = item.precio * item.cantidad;
        total += subtotal;

        var tr = document.createElement('tr');
        tr.innerHTML =
            '<td><span class="fw-bold">' + item.nombre + '</span><br>' +
            '<small class="text-muted">$' + item.precio.toLocaleString('es-CO') + ' c/u</small></td>' +
            '<td><div class="d-flex align-items-center gap-1">' +
            '<button type="button" class="btn btn-outline-secondary btn-sm px-2" onclick="restar(\'' + item.id + '\')">-</button>' +
            '<span class="fw-bold px-2">' + item.cantidad + '</span>' +
            '<button type="button" class="btn btn-outline-secondary btn-sm px-2" onclick="sumar(\'' + item.id + '\')">+</button>' +
            '</div></td>' +
            '<td class="text-end fw-bold">$' + subtotal.toLocaleString('es-CO') + '</td>' +
            '<td class="text-end"><button type="button" class="btn btn-sm btn-outline-danger" ' +
            'onclick="eliminarProducto(\'' + item.id + '\')"><i class="fa-solid fa-trash"></i></button></td>';
        tbody.appendChild(tr);

        var names = ['producto_id[]', 'producto_nombre[]', 'producto_precio[]', 'producto_cantidad[]'];
        var vals  = [item.id, item.nombre, item.precio, item.cantidad];
        for (var j = 0; j < 4; j++) {
            var inp = document.createElement('input');
            inp.type  = 'hidden';
            inp.name  = names[j];
            inp.value = vals[j];
            camposOcultos.appendChild(inp);
        }
    }

    totalEl.textContent = '$' + total.toLocaleString('es-CO');
}


function validarFormVenta() {
    var valido = true;

    if (carrito.length === 0) {
        var alerta   = document.getElementById('alertaCarritoVacio');
        var msgVacio = document.getElementById('msgCarritoVacio');
        alerta.classList.remove('d-none');
        msgVacio.classList.add('d-none');
        alerta.scrollIntoView({ behavior: 'smooth', block: 'center' });
        valido = false;
    }

    var clienteInput = document.getElementById('inputClienteCrear');
    var feedbackC    = document.getElementById('feedbackCliente');
    var cliente      = clienteInput ? clienteInput.value.trim() : '';
    if (!cliente) {
        if (feedbackC) feedbackC.textContent = 'El nombre del cliente es obligatorio';
        valido = false;
    } else if (cliente.length < 3) {
        if (feedbackC) feedbackC.textContent = 'El nombre debe tener al menos 3 caracteres';
        valido = false;
    } else {
        if (feedbackC) feedbackC.textContent = '';
    }

    var estadoSelect = document.getElementById('selectEstado');
    var feedbackE    = document.getElementById('feedbackEstado');
    var estado       = estadoSelect ? estadoSelect.value : '';
    if (!estado) {
        if (feedbackE) feedbackE.textContent = 'Debes seleccionar un estado';
        valido = false;
    } else {
        if (feedbackE) feedbackE.textContent = '';
    }

    return valido;
}