setTimeout(function () {
    var alertas = document.querySelectorAll('.alert');
    alertas.forEach(function (alerta) {
        var bsAlert = bootstrap.Alert.getOrCreateInstance(alerta);
        bsAlert.close();
    });
}, 3000);