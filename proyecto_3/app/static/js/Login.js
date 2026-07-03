/**
 * ═══════════════════════════════════════════════════════════════════════
 * MÓDULO DE LOGIN - JavaScript
 * Funcionalidad para mostrar/ocultar contraseña y validación en tiempo real
 * ═══════════════════════════════════════════════════════════════════════
 */

document.addEventListener('DOMContentLoaded', function() {

    // ── Toggle contraseña ───────────────────────────────────────────────
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput  = document.getElementById('passwordInput');
    const eyeIcon        = document.getElementById('eyeIcon');

    if (togglePassword && passwordInput && eyeIcon) {
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            eyeIcon.classList.toggle('fa-eye', type === 'password');
            eyeIcon.classList.toggle('fa-eye-slash', type === 'text');
        });
    }

    // ── Usuario: solo letras, números y guión bajo ──────────────────────
    const inputUsername = document.querySelector('input[name="username"]');
    if (inputUsername) {
        inputUsername.addEventListener('keypress', function(e) {
            if (e.key.length > 1) return; // permitir Backspace, flechas, etc.
            if (!/^[a-zA-Z0-9_]$/.test(e.key)) e.preventDefault();
        });
        inputUsername.addEventListener('paste', function(e) {
            const texto = (e.clipboardData || window.clipboardData).getData('text');
            if (!/^[a-zA-Z0-9_]+$/.test(texto)) e.preventDefault();
        });
    }

});