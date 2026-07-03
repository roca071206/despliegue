var tiposExistentes = [];

document.addEventListener('DOMContentLoaded', function () {
    // Recolectar tipos existentes del listado
    document.querySelectorAll('.list-group-item span').forEach(function (el) {
        tiposExistentes.push(el.textContent.trim().toLowerCase());
    });

    var form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function (e) {
            var input = form.querySelector('input[name="nombre_tipo"]');
            var valor = input.value.trim();

            if (valor.length < 2) {
                e.preventDefault();
                mostrarErrorTipo('⚠ El nombre debe tener al menos 2 letras.');
                input.focus();
                return;
            }
            if (tiposExistentes.includes(valor.toLowerCase())) {
                e.preventDefault();
                mostrarErrorTipo('⚠ Ya existe un tipo con ese nombre.');
                input.focus();
            }
        });
    }
});

function bloquearNombreTipo(input) {
    var antes = input.value;
    var limpio = antes.replace(/[^a-zA-ZáéíóúÁÉÍÓÚüÜñÑ ]/g, '');
    limpio = limpio.replace(/ {2,}/g, ' ');
    if (antes !== limpio) {
        input.value = limpio;
        mostrarErrorTipo('⚠ Solo se permiten letras y espacios.');
    }
}

function mostrarErrorTipo(msg) {
    var el = document.getElementById('tipo_error');
    if (el) {
        el.textContent = msg;
        el.style.display = 'block';
        clearTimeout(el._timer);
        el._timer = setTimeout(function () { el.style.display = 'none'; }, 3000);
    }
}

//por ahora no se valida el precio del tipo, pero se podría agregar una función similar a validarPrecio() de productos.js si se decide hacerlo en el futuro.
