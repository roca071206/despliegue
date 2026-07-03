/* animaciones.js - Sistema global de animaciones ligero usando IntersectionObserver */

document.addEventListener("DOMContentLoaded", () => {
    // Configuración para animaciones simples (fade-up, fade-in, slide-left)
    const observerOptions = {
        threshold: 0.1, // Se activa cuando el 10% del elemento es visible
        rootMargin: "0px 0px -30px 0px" // Margen inferior para que anime un poco antes de entrar completamente
    };

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-active');
                obs.unobserve(entry.target); // Animar solo una vez
            }
        });
    }, observerOptions);

    // Seleccionar elementos individuales y observarlos
    const individualElements = document.querySelectorAll('.animate-fade-up, .animate-fade-in, .animate-slide-left');
    individualElements.forEach(el => observer.observe(el));

    // Configuración para animaciones en cascada (stagger) para listas, tablas y grids
    const staggerObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Seleccionar todos los hijos con la clase animate-item
                const items = entry.target.querySelectorAll('.animate-item');
                
                // Aplicar delay en cascada a cada elemento
                items.forEach((item, index) => {
                    item.style.transitionDelay = `${index * 0.05}s`; // 50ms entre cada item
                    // Forzar reflow para asegurar que el delay se aplique antes de la clase activa
                    void item.offsetWidth;
                });

                // Activar el contenedor padre para iniciar la animación de los hijos
                entry.target.classList.add('animate-active');
                obs.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observar contenedores stagger
    const staggerContainers = document.querySelectorAll('.animate-stagger');
    staggerContainers.forEach(container => staggerObserver.observe(container));
});
