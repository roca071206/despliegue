function confirmarEliminar(nombre, formulario) {
    Swal.fire({
        title: 'Eliminar "' + nombre + '"?',
        text: 'Esta accion no se puede deshacer.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Si, eliminar',
        cancelButtonText: 'Cancelar'
    }).then(function (result) {
        if (result.isConfirmed) {
            formulario.submit();
        }
    });
}