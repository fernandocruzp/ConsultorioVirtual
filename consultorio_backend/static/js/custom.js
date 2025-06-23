// Funciones personalizadas para Pineda IntegralMedic

document.addEventListener('DOMContentLoaded', function() {
    // Aplicar clases de Bootstrap a los campos de formulario
    const formControls = document.querySelectorAll('input, textarea, select');
    formControls.forEach(function(element) {
        if (!element.classList.contains('form-control') && 
            !element.classList.contains('form-check-input') &&
            element.type !== 'hidden' &&
            element.type !== 'submit' &&
            element.type !== 'button') {
            element.classList.add('form-control');
        }
        
        // Si hay errores, marcar el campo como inválido
        if (element.nextElementSibling && element.nextElementSibling.classList.contains('invalid-feedback')) {
            element.classList.add('is-invalid');
        }
    });
    
    // Inicializar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers de Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Función para calcular IMC en el formulario de consulta
    const pesoInput = document.querySelector('#id_peso');
    const alturaInput = document.querySelector('#id_altura');
    
    if (pesoInput && alturaInput) {
        const calcularIMC = function() {
            const peso = parseFloat(pesoInput.value);
            const altura = parseFloat(alturaInput.value);
            
            if (!isNaN(peso) && !isNaN(altura) && altura > 0) {
                const imc = peso / Math.pow(altura/100, 2);
                
                // Mostrar el IMC calculado
                let imcInfo = document.getElementById('imc-info');
                if (!imcInfo) {
                    imcInfo = document.createElement('div');
                    imcInfo.id = 'imc-info';
                    imcInfo.className = 'alert alert-info mt-3';
                    alturaInput.parentNode.parentNode.parentNode.after(imcInfo);
                }
                
                let imcClass = 'alert-info';
                let imcText = '';
                
                if (imc < 18.5) {
                    imcClass = 'alert-warning';
                    imcText = 'Bajo peso';
                } else if (imc < 25) {
                    imcClass = 'alert-success';
                    imcText = 'Normal';
                } else if (imc < 30) {
                    imcClass = 'alert-warning';
                    imcText = 'Sobrepeso';
                } else {
                    imcClass = 'alert-danger';
                    imcText = 'Obesidad';
                }
                
                imcInfo.className = `alert ${imcClass} mt-3`;
                imcInfo.innerHTML = `<strong>IMC calculado:</strong> ${imc.toFixed(2)} - <span>${imcText}</span>`;
            }
        };
        
        pesoInput.addEventListener('input', calcularIMC);
        alturaInput.addEventListener('input', calcularIMC);
        
        // Calcular IMC inicial si ya hay valores
        if (pesoInput.value && alturaInput.value) {
            calcularIMC();
        }
    }
    
    // Mejorar el campo de fecha y hora
    const fechaHoraInput = document.querySelector('#id_fecha_hora');
    if (fechaHoraInput && fechaHoraInput.type !== 'datetime-local') {
        fechaHoraInput.type = 'datetime-local';
    }
    
    // Confirmar acciones peligrosas
    const confirmarAcciones = document.querySelectorAll('.confirmar-accion');
    confirmarAcciones.forEach(function(elemento) {
        elemento.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro de realizar esta acción?')) {
                e.preventDefault();
            }
        });
    });
});
