// Utilidades Globales para Torneo de Pádel

// Función para mostrar alertas flash personalizadas
function mostrarAlerta(mensaje, tipo = 'info') {
    const alertasContainer = document.getElementById('flash-messages');
    if (!alertasContainer) {
        console.warn('No se encontró el contenedor de alertas');
        return;
    }

    const iconos = {
        success: 'check-circle-fill',
        danger: 'exclamation-triangle-fill',
        warning: 'exclamation-triangle-fill',
        info: 'info-circle-fill'
    };

    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show fade-in`;
    alerta.setAttribute('role', 'alert');
    alerta.innerHTML = `
        <i class="bi bi-${iconos[tipo]} me-2"></i>
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    alertasContainer.appendChild(alerta);

    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        alerta.classList.remove('show');
        setTimeout(() => alerta.remove(), 300);
    }, 5000);
}

// Validación de teléfono (formato flexible)
function validarTelefono(telefono) {
    // Permite formatos: 1234567890, 123-456-7890, (123) 456-7890, +54 11 1234-5678
    const patron = /^[\d\s\-\(\)\+]+$/;
    return patron.test(telefono) && telefono.replace(/\D/g, '').length >= 10;
}

// Formatear teléfono
function formatearTelefono(telefono) {
    const numeros = telefono.replace(/\D/g, '');
    if (numeros.length === 10) {
        return `(${numeros.substring(0, 3)}) ${numeros.substring(3, 6)}-${numeros.substring(6)}`;
    }
    return telefono;
}

// Validación de formularios antes de submit
function validarFormularioAgregarPareja(form) {
    const nombre = form.querySelector('[name="nombre"]').value.trim();
    const telefono = form.querySelector('[name="telefono"]').value.trim();
    const categoria = form.querySelector('[name="categoria"]').value;
    const franjas = form.querySelectorAll('[name="franjas[]"]:checked');

    if (!nombre) {
        mostrarAlerta('Por favor ingrese el nombre de la pareja', 'warning');
        return false;
    }

    if (!telefono) {
        mostrarAlerta('Por favor ingrese el teléfono', 'warning');
        return false;
    }

    if (!validarTelefono(telefono)) {
        mostrarAlerta('El teléfono debe tener al menos 10 dígitos', 'warning');
        return false;
    }

    if (!categoria) {
        mostrarAlerta('Por favor seleccione una categoría', 'warning');
        return false;
    }

    if (franjas.length === 0) {
        mostrarAlerta('Por favor seleccione al menos un horario', 'warning');
        return false;
    }

    return true;
}

// Confirmación antes de eliminar
function confirmarEliminacion(mensaje = '¿Está seguro de eliminar este elemento?') {
    return confirm(mensaje);
}

// Contador de parejas seleccionadas
function actualizarContadorFranjas() {
    const checkboxes = document.querySelectorAll('[name="franjas[]"]');
    const contador = document.getElementById('contador-franjas');
    
    if (contador) {
        const seleccionadas = Array.from(checkboxes).filter(cb => cb.checked).length;
        contador.textContent = `${seleccionadas} franja${seleccionadas !== 1 ? 's' : ''} seleccionada${seleccionadas !== 1 ? 's' : ''}`;
    }
}

// Inicializar tooltips de Bootstrap
function inicializarTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Copiar texto al portapapeles
function copiarAlPortapapeles(texto) {
    navigator.clipboard.writeText(texto).then(() => {
        mostrarAlerta('Copiado al portapapeles', 'success');
    }).catch(err => {
        mostrarAlerta('Error al copiar: ' + err, 'danger');
    });
}

// Exportar tabla a CSV
function exportarTablaCSV(tablaId, nombreArchivo = 'datos.csv') {
    const tabla = document.getElementById(tablaId);
    if (!tabla) return;

    let csv = [];
    const filas = tabla.querySelectorAll('tr');

    filas.forEach(fila => {
        const cols = fila.querySelectorAll('td, th');
        const row = [];
        cols.forEach(col => row.push(col.textContent));
        csv.push(row.join(','));
    });

    const csvString = csv.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nombreArchivo;
    a.click();
    window.URL.revokeObjectURL(url);

    mostrarAlerta('Archivo CSV descargado', 'success');
}

// Imprimir sección específica
function imprimirSeccion(seccionId) {
    const seccion = document.getElementById(seccionId);
    if (!seccion) return;

    const ventanaImpresion = window.open('', '', 'height=600,width=800');
    ventanaImpresion.document.write('<html><head><title>Imprimir</title>');
    ventanaImpresion.document.write('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">');
    ventanaImpresion.document.write('<link rel="stylesheet" href="/static/css/style.css">');
    ventanaImpresion.document.write('</head><body>');
    ventanaImpresion.document.write(seccion.innerHTML);
    ventanaImpresion.document.write('</body></html>');
    ventanaImpresion.document.close();
    ventanaImpresion.print();
}

// Animación de carga para botones
function toggleBotonCargando(boton, cargando = true) {
    if (cargando) {
        boton.disabled = true;
        boton.dataset.originalText = boton.innerHTML;
        boton.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            Cargando...
        `;
    } else {
        boton.disabled = false;
        boton.innerHTML = boton.dataset.originalText || boton.innerHTML;
    }
}

// Scroll suave a elemento
function scrollSuaveA(elementoId) {
    const elemento = document.getElementById(elementoId);
    if (elemento) {
        elemento.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Filtrar tabla en tiempo real
function filtrarTabla(inputId, tablaId) {
    const input = document.getElementById(inputId);
    const tabla = document.getElementById(tablaId);
    
    if (!input || !tabla) return;

    input.addEventListener('keyup', function() {
        const filtro = this.value.toLowerCase();
        const filas = tabla.getElementsByTagName('tr');

        for (let i = 1; i < filas.length; i++) { // Empezar desde 1 para saltar header
            const celdas = filas[i].getElementsByTagName('td');
            let encontrado = false;

            for (let j = 0; j < celdas.length; j++) {
                if (celdas[j].textContent.toLowerCase().indexOf(filtro) > -1) {
                    encontrado = true;
                    break;
                }
            }

            filas[i].style.display = encontrado ? '' : 'none';
        }
    });
}

// Guardar datos en localStorage
function guardarEnLocalStorage(clave, datos) {
    try {
        localStorage.setItem(clave, JSON.stringify(datos));
        return true;
    } catch (e) {
        console.error('Error al guardar en localStorage:', e);
        return false;
    }
}

// Cargar datos desde localStorage
function cargarDeLocalStorage(clave) {
    try {
        const datos = localStorage.getItem(clave);
        return datos ? JSON.parse(datos) : null;
    } catch (e) {
        console.error('Error al cargar de localStorage:', e);
        return null;
    }
}

// Inicializar eventos cuando carga el DOM
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips
    inicializarTooltips();

    // Auto-cerrar alertas después de 5 segundos
    const alertas = document.querySelectorAll('.alert:not(.alert-permanent)');
    alertas.forEach(alerta => {
        setTimeout(() => {
            alerta.classList.remove('show');
            setTimeout(() => alerta.remove(), 300);
        }, 5000);
    });

    // Agregar animación fade-in a cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });

    // Contador de franjas si existe
    const checkboxesFranjas = document.querySelectorAll('[name="franjas[]"]');
    if (checkboxesFranjas.length > 0) {
        checkboxesFranjas.forEach(cb => {
            cb.addEventListener('change', actualizarContadorFranjas);
        });
    }
});

// Exportar funciones globalmente
window.torneoUtils = {
    mostrarAlerta,
    validarTelefono,
    formatearTelefono,
    validarFormularioAgregarPareja,
    confirmarEliminacion,
    actualizarContadorFranjas,
    copiarAlPortapapeles,
    exportarTablaCSV,
    imprimirSeccion,
    toggleBotonCargando,
    scrollSuaveA,
    filtrarTabla,
    guardarEnLocalStorage,
    cargarDeLocalStorage
};
