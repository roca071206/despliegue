var marcasExistentes = [];

document.addEventListener('DOMContentLoaded', function () {
    // Recolectar marcas existentes del listado
    document.querySelectorAll('.list-group-item .fw-semibold').forEach(function (el) {
        marcasExistentes.push(el.textContent.trim().toLowerCase());
    });

    var form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function (e) {
            var input = form.querySelector('input[name="nombreMarca"]');
            var valor = input.value.trim();

            if (valor.length < 2) {
                e.preventDefault();
                mostrarErrorMarca('⚠ El nombre debe tener al menos 2 letras.');
                input.focus();
                return;
            }
            if (marcasExistentes.includes(valor.toLowerCase())) {
                e.preventDefault();
                mostrarErrorMarca('⚠ Ya existe una marca con ese nombre.');
                input.focus();
            }
        });
    }
});

function bloquearNombreMarca(input) {
    var limpio = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚüÜñÑ ]/g, '');
    limpio = limpio.replace(/ {2,}/g, ' ');
    if (input.value !== limpio) {
        input.value = limpio;
        mostrarErrorMarca('⚠ Solo se permiten letras, sin números ni caracteres especiales.');
    }
}

function mostrarErrorMarca(msg) {
    var el = document.getElementById('marca_error');
    if (el) {
        el.textContent = msg;
        el.style.display = 'block';
        clearTimeout(el._timer);
        el._timer = setTimeout(function () { el.style.display = 'none'; }, 3000);
    }
}

function confirmarEliminar(nombre, form) {
    Swal.fire({
        title: '¿Eliminar marca?',
        html: 'Estás a punto de eliminar <strong>"' + nombre + '"</strong>.<br>Esta acción no se puede deshacer.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then(function (result) {
        if (result.isConfirmed) { form.submit(); }
    });
}