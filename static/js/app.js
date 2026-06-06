<<<<<<< HEAD
// static/js/app.js - Basurero Inteligente con YOLO + MobileNet (SIN PARPADEOS)

=======
// static/js/app.js - Versión COMPLETA con DETECCIÓN AUTOMÁTICA y ELIMINAR USUARIOS

const nombresTipos = {
    'plastic': '🥤 PLÁSTICO',
    'glass': '🍾 VIDRIO',
    'metal': '🥫 LATA'
};

// ========== VARIABLES GLOBALES ==========
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
let streamCamara = null;
let detecciones = [];
let autoDetectInterval = null;
let isAutoDetecting = false;
let lastDetectionTime = 0;

<<<<<<< HEAD
const AUTO_DETECT_INTERVAL = 2000;
const DEBOUNCE_TIME = 3000;

// ========== INICIALIZACIÓN ==========
document.addEventListener('DOMContentLoaded', () => {
    // Mostrar placeholder mientras carga
    mostrarPlaceholder();
    
=======
// Configuración de detección automática
const AUTO_DETECT_INTERVAL = 2000;  // 2 segundos entre detecciones
const DEBOUNCE_TIME = 3000;          // 3 segundos sin detectar otra botella

// ========== GUARDAR Y RESTAURAR USUARIO SELECCIONADO ==========
function guardarUsuarioSeleccionado() {
    const usuarioId = document.getElementById('usuario_id').value;
    if (usuarioId) {
        localStorage.setItem('usuarioSeleccionado', usuarioId);
    }
}

function restaurarUsuarioSeleccionado() {
    const usuarioGuardado = localStorage.getItem('usuarioSeleccionado');
    if (usuarioGuardado) {
        document.getElementById('usuario_id').value = usuarioGuardado;
        cargarEstadisticas();
    }
}

// ========== INICIALIZACIÓN ==========
document.addEventListener('DOMContentLoaded', () => {
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
    cargarListaUsuarios();
    cargarRanking();
    cargarEstadisticas();
    cargarStatsHeader();
    
<<<<<<< HEAD
    const btnActivar = document.getElementById('btnActivarCamara');
    const btnDetener = document.getElementById('btnDetenerCamara');
    if (btnActivar) btnActivar.addEventListener('click', activarCamara);
    if (btnDetener) btnDetener.addEventListener('click', detenerCamara);
    
    setInterval(() => {
        cargarRanking();
        cargarStatsHeader();
        cargarListaUsuarios();
    }, 10000);
});

// ========== MOSTRAR PLACEHOLDER MIENTRAS CARGA ==========
function mostrarPlaceholder() {
    const select = document.getElementById('usuario_id');
    if (select && select.innerHTML === '') {
        select.innerHTML = '<option value="">Cargando usuarios...</option>';
    }
}

=======
    // Restaurar usuario seleccionado después de cargar la lista
    setTimeout(() => {
        restaurarUsuarioSeleccionado();
    }, 500);
    
    // Configurar botones de cámara
    const btnActivar = document.getElementById('btnActivarCamara');
    const btnDetener = document.getElementById('btnDetenerCamara');
    
    if (btnActivar) {
        btnActivar.addEventListener('click', activarCamara);
    }
    if (btnDetener) {
        btnDetener.addEventListener('click', detenerCamara);
    }
    
    // Auto-refrescar cada 10 segundos (reducido de 5 a 10)
    setInterval(() => {
        cargarRanking();
        cargarEstadisticas();
        cargarStatsHeader();
        cargarListaUsuarios();
    }, 10000);  // ← Cambiado de 5000 a 10000
});

>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
// ========== MODO OSCURO ==========
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        const icon = themeToggle.querySelector('i');
        if (document.body.classList.contains('light-mode')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    });
}

<<<<<<< HEAD
=======
// ========== NOTIFICACIONES ==========
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
function mostrarNotificacion(mensaje, tipo) {
    const toast = document.createElement('div');
    let icono = tipo === 'success' ? 'fa-check-circle' : tipo === 'warning' ? 'fa-exclamation-triangle' : 'fa-exclamation-circle';
    let color = tipo === 'success' ? '#2ecc71' : tipo === 'warning' ? '#f39c12' : '#e74c3c';
<<<<<<< HEAD
    toast.innerHTML = `<i class="fas ${icono}"></i><span>${mensaje}</span>`;
    toast.style.cssText = `position:fixed; bottom:20px; right:20px; background:${color}; color:white; padding:12px 20px; border-radius:10px; z-index:2000; animation:slideIn 0.3s ease;`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ========== GUARDAR Y RESTAURAR USUARIO ==========
function guardarUsuarioSeleccionado() {
    const usuarioId = document.getElementById('usuario_id').value;
    if (usuarioId && usuarioId !== '') {
        localStorage.setItem('usuarioSeleccionado', usuarioId);
    }
}

function restaurarUsuarioSeleccionado() {
    const usuarioGuardado = localStorage.getItem('usuarioSeleccionado');
    const select = document.getElementById('usuario_id');
    
    if (usuarioGuardado && select) {
        // Buscar si el usuario existe en las opciones actuales
        const opcionExiste = Array.from(select.options).some(opt => opt.value == usuarioGuardado);
        if (opcionExiste) {
            select.value = usuarioGuardado;
            cargarEstadisticas();
            
            // También actualizar el selector de estadísticas
            const selectorEst = document.getElementById('selector_usuario');
            if (selectorEst && Array.from(selectorEst.options).some(opt => opt.value == usuarioGuardado)) {
                selectorEst.value = usuarioGuardado;
            }
        }
    }
}

// ========== USUARIOS ==========
=======
    
    toast.innerHTML = `<i class="fas ${icono}"></i><span>${mensaje}</span>`;
    toast.style.cssText = `
        position: fixed; bottom: 20px; right: 20px; background: ${color}; color: white;
        padding: 12px 20px; border-radius: 10px; display: flex; align-items: center;
        gap: 10px; z-index: 2000; animation: slideIn 0.3s ease; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== CREAR USUARIO ==========
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
async function crearUsuario() {
    const nombre = document.getElementById('nuevo_nombre').value;
    const email = document.getElementById('nuevo_email').value;
    const mensajeDiv = document.getElementById('mensaje_usuario');
<<<<<<< HEAD
    
    if (!nombre || !email) {
        mensajeDiv.innerHTML = '<p style="color:#e74c3c;">❌ Completa todos los campos</p>';
        return;
    }
    
=======

    if (!nombre || !email) {
        mensajeDiv.innerHTML = '<p style="color: #e74c3c;">❌ Completa todos los campos</p>';
        return;
    }

>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
    try {
        const response = await fetch('/crear_usuario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, email })
        });
<<<<<<< HEAD
        const data = await response.json();
        
        if (response.status === 201) {
            mensajeDiv.innerHTML = `<p style="color:#2ecc71;">✅ Usuario creado! ID: ${data.id}</p>`;
            document.getElementById('nuevo_nombre').value = '';
            document.getElementById('nuevo_email').value = '';
            await cargarListaUsuarios();
            cargarRanking();
            cargarStatsHeader();
            document.getElementById('usuario_id').value = data.id;
            guardarUsuarioSeleccionado();
            cargarEstadisticas();
            mostrarNotificacion(`Usuario ${nombre} creado`, 'success');
        } else {
            mensajeDiv.innerHTML = `<p style="color:#e74c3c;">❌ ${data.error}</p>`;
        }
    } catch (error) {
        mensajeDiv.innerHTML = '<p style="color:#e74c3c;">❌ Error al crear usuario</p>';
    }
}

=======

        const data = await response.json();

        if (response.status === 201) {
            mensajeDiv.innerHTML = `<p style="color: #2ecc71;">✅ Usuario creado! ID: ${data.id}</p>`;
            document.getElementById('nuevo_nombre').value = '';
            document.getElementById('nuevo_email').value = '';
            cargarListaUsuarios();
            cargarRanking();
            cargarStatsHeader();
            mostrarNotificacion(`Usuario ${nombre} creado`, 'success');
            
            // Seleccionar el nuevo usuario automáticamente
            document.getElementById('usuario_id').value = data.id;
            guardarUsuarioSeleccionado();
            cargarEstadisticas();
        } else {
            mensajeDiv.innerHTML = `<p style="color: #e74c3c;">❌ Error: ${data.error}</p>`;
        }
    } catch (error) {
        console.error("Error al crear usuario:", error);
        mensajeDiv.innerHTML = '<p style="color: #e74c3c;">❌ Error al crear usuario</p>';
    }
}

// ========== CARGAR LISTA DE USUARIOS (CORREGIDA) ==========
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
async function cargarListaUsuarios() {
    try {
        const response = await fetch('/usuarios');
        const usuarios = await response.json();
        const select = document.getElementById('usuario_id');
        if (!select) return;
        
<<<<<<< HEAD
        // 🔥 GUARDAR EL VALOR ACTUAL ANTES DE MODIFICAR EL SELECT
        const valorActual = select.value;
        
=======
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
        if (usuarios.length === 0) {
            select.innerHTML = '<option value="">No hay usuarios - Crea uno</option>';
            return;
        }
        
<<<<<<< HEAD
        // Recargar las opciones
=======
        // Guardar el valor actual antes de recargar
        const valorActual = select.value;
        
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
        select.innerHTML = '<option value="">-- Selecciona un usuario --</option>';
        usuarios.forEach(usuario => {
            select.innerHTML += `<option value="${usuario.id}">${usuario.nombre} (⭐ ${usuario.puntos} pts)</option>`;
        });
        
<<<<<<< HEAD
        // 🔥 PRIORIDAD: 1º usuario guardado, 2º valor actual, 3º primer usuario
        const usuarioGuardado = localStorage.getItem('usuarioSeleccionado');
        
        if (usuarioGuardado && usuarios.some(u => u.id == usuarioGuardado)) {
            select.value = usuarioGuardado;
        } else if (valorActual && usuarios.some(u => u.id == valorActual)) {
=======
        // Restaurar el valor seleccionado (si existe y sigue siendo válido)
        if (valorActual && usuarios.some(u => u.id == valorActual)) {
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
            select.value = valorActual;
        } else if (usuarios.length > 0 && !select.value) {
            select.value = usuarios[0].id;
        }
        
<<<<<<< HEAD
        // Solo cargar estadísticas si es necesario
        if (select.value && select.value !== '') {
            cargarEstadisticas();
        }
        
        // Cargar el selector de estadísticas también
=======
        cargarEstadisticas();
        guardarUsuarioSeleccionado();
        
        // También cargar el selector de ver estadísticas
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
        const selectorEstadisticas = document.getElementById('selector_usuario');
        if (selectorEstadisticas) {
            const valorActualEst = selectorEstadisticas.value;
            selectorEstadisticas.innerHTML = '<option value="">-- Selecciona un usuario --</option>';
            usuarios.forEach(usuario => {
                selectorEstadisticas.innerHTML += `<option value="${usuario.id}">🆔 ${usuario.id} - ${usuario.nombre} (⭐ ${usuario.puntos} pts)</option>`;
            });
            if (valorActualEst && usuarios.some(u => u.id == valorActualEst)) {
                selectorEstadisticas.value = valorActualEst;
<<<<<<< HEAD
            } else if (select.value && usuarios.some(u => u.id == select.value)) {
                selectorEstadisticas.value = select.value;
=======
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
            }
        }
    } catch (error) {
        console.error('Error cargando usuarios:', error);
    }
}

<<<<<<< HEAD
async function cargarEstadisticas() {
    const usuario_id = document.getElementById('usuario_id').value;
    if (!usuario_id) return;
    
    guardarUsuarioSeleccionado();
    
    try {
        const response = await fetch(`/estadisticas/${usuario_id}`);
        const data = await response.json();
        
        if (response.ok && !data.error) {
            document.getElementById('estadisticas').innerHTML = `
                <div class="stat-detail-card">
                    <div class="stat-label"><span style="font-size: 1.8rem; display: inline-block; width: 45px; text-align: center;">👤</span> USUARIO</div>
                    <div class="stat-number" style="color: #00d4ff; font-size: 1.3rem; font-weight: 600; letter-spacing: 0.5px;">${data.nombre}</div>
                </div>
                <div class="stat-detail-card">
                    <div class="stat-label"><span style="font-size: 1.8rem; display: inline-block; width: 45px; text-align: center;">⭐</span> PUNTOS TOTALES</div>
                    <div class="stat-number" style="color: #f1c40f; font-size: 2rem; font-weight: 800; text-shadow: 0 2px 5px rgba(241,196,15,0.3);">${data.puntos_totales}</div>
                </div>
                <div class="stat-detail-card">
                    <div class="stat-label"><span style="font-size: 1.8rem; display: inline-block; width: 45px; text-align: center;">♻️</span> TOTAL RECICLAJES</div>
                    <div class="stat-number" style="color: #2ecc71; font-size: 1.6rem; font-weight: 700;">${data.total_reciclajes}</div>
                </div>
                <div class="stat-detail-card">
                    <div class="stat-label"><span style="font-size: 1.8rem; display: inline-block; width: 45px; text-align: center;">🥤</span> PLÁSTICO</div>
                    <div class="stat-number" style="color: #3498db; font-size: 1.5rem; font-weight: 700;">${data.plasticos || 0}</div>
                </div>
                <div class="stat-detail-card">
                    <div class="stat-label"><span style="font-size: 1.8rem; display: inline-block; width: 45px; text-align: center;">🍾</span> VIDRIO</div>
                    <div class="stat-number" style="color: #2ecc71; font-size: 1.5rem; font-weight: 700;">${data.vidrios || 0}</div>
                </div>
                <div class="stat-detail-card">
                    <div class="stat-label"><span style="font-size: 1.8rem; display: inline-block; width: 45px; text-align: center;">🥫</span> LATAS</div>
                    <div class="stat-number" style="color: #e74c3c; font-size: 1.5rem; font-weight: 700;">${data.latas || 0}</div>
                </div>
                <div class="stat-detail-card">
                    <div class="stat-label"><span style="font-size: 1.8rem; display: inline-block; width: 45px; text-align: center;">🏆</span> META (400 PTS)</div>
                    <div class="stat-number" style="font-size: 1.2rem; font-weight: 600;">${data.puntos_totales >= 400 ? '<span style="color: #2ecc71;">✅ LOGRADA</span>' : '<span style="color: #f39c12;">🎯 EN PROGRESO</span>'}</div>
=======
// ========== CARGAR ESTADÍSTICAS (CORREGIDA) ==========
async function cargarEstadisticas() {
    const usuario_id = document.getElementById('usuario_id').value;
    if (!usuario_id) return;

    // Guardar el usuario seleccionado en localStorage
    localStorage.setItem('usuarioSeleccionado', usuario_id);

    try {
        const response = await fetch(`/estadisticas/${usuario_id}`);
        const data = await response.json();

        if (response.ok && !data.error) {
            document.getElementById('estadisticas').innerHTML = `
                <div class="stat-detail-card"><i class="fas fa-user-circle"></i><div class="stat-label">USUARIO</div><div class="stat-number">${data.nombre}</div></div>
                <div class="stat-detail-card"><i class="fas fa-star"></i><div class="stat-label">PUNTOS TOTALES</div><div class="stat-number">${data.puntos_totales}</div></div>
                <div class="stat-detail-card"><i class="fas fa-recycle"></i><div class="stat-label">TOTAL RECICLAJES</div><div class="stat-number">${data.total_reciclajes}</div></div>
                <div class="stat-detail-card"><i class="fas fa-chart-simple"></i><div class="stat-label">PROMEDIO</div><div class="stat-number">${data.total_reciclajes > 0 ? Math.round(data.puntos_totales / data.total_reciclajes) : 0} pts</div></div>
                <div class="stat-detail-card"><div style="font-size:35px;">🧴</div><div class="stat-label">PLÁSTICO</div><div class="stat-number">${data.plasticos || 0}</div></div>
                <div class="stat-detail-card"><i class="fas fa-wine-bottle"></i><div class="stat-label">VIDRIO</div><div class="stat-number">${data.vidrios || 0}</div></div>
                <div class="stat-detail-card"><i class="fas fa-beer-mug-empty"></i><div class="stat-label">LATAS</div><div class="stat-number">${data.latas || 0}</div></div>
                <div class="stat-detail-card"><i class="fas fa-chart-line"></i><div class="stat-label">META (100 PTS)</div><div class="stat-number">${data.puntos_totales >= 100 ? '🏆 LOGRADA' : '🎯 EN PROGRESO'}</div><div class="progress-bar-mini"><div class="progress-fill-mini" style="width: ${Math.min((data.puntos_totales / 100) * 100, 100)}%"></div></div></div>
            `;
        } else {
            document.getElementById('estadisticas').innerHTML = `
                <div class="stat-detail-card" style="grid-column: 1/-1; text-align: center;">
                    <i class="fas fa-user-slash"></i>
                    <div class="stat-label">USUARIO NO ENCONTRADO</div>
                    <div class="stat-number" style="font-size: 14px;">ID ${usuario_id} no existe</div>
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
                </div>
            `;
        }
    } catch (error) {
<<<<<<< HEAD
        console.error('Error:', error);
    }
}

=======
        console.error('Error cargando estadísticas:', error);
    }
}

// ========== CARGAR RANKING ==========
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
async function cargarRanking() {
    try {
        const response = await fetch('/ranking');
        const ranking = await response.json();
<<<<<<< HEAD
        
        if (!response.ok || ranking.length === 0) {
            document.getElementById('ranking').innerHTML = '<p class="empty-msg">📭 No hay reciclajes aún</p>';
            return;
        }
        
        let html = '';
        ranking.forEach((user, index) => {
            let medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}º`;
            html += `<div class="ranking-item"><div class="ranking-position">${medal}</div><div class="ranking-name">${user.nombre}</div><div class="ranking-points">⭐ ${user.puntos} pts</div><div class="ranking-reciclajes">♻️ ${user.reciclajes} veces</div></div>`;
        });
        document.getElementById('ranking').innerHTML = html;
    } catch (error) {
        document.getElementById('ranking').innerHTML = '<p class="error-msg">❌ Error</p>';
    }
}

=======

        if (!response.ok || ranking.length === 0) {
            document.getElementById('ranking').innerHTML = '<p class="empty-msg">📭 No hay reciclajes registrados aún</p>';
            return;
        }

        let html = '';
        ranking.forEach((user, index) => {
            let medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}º`;
            html += `
                <div class="ranking-item">
                    <div class="ranking-position">${medal}</div>
                    <div class="ranking-name"><strong>${user.nombre}</strong></div>
                    <div class="ranking-points">⭐ ${user.puntos} pts</div>
                    <div class="ranking-reciclajes">♻️ ${user.reciclajes} veces</div>
                </div>
            `;
        });
        document.getElementById('ranking').innerHTML = html;
    } catch (error) {
        document.getElementById('ranking').innerHTML = '<p class="error-msg">❌ Error cargando ranking</p>';
    }
}

// ========== CARGAR STATS HEADER ==========
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
async function cargarStatsHeader() {
    try {
        const response = await fetch('/ranking');
        const ranking = await response.json();
        if (response.ok) {
            const totalPuntos = ranking.reduce((sum, user) => sum + (user.puntos || 0), 0);
            const totalReciclajes = ranking.reduce((sum, user) => sum + (user.reciclajes || 0), 0);
            document.getElementById('totalReciclajesHoy').textContent = totalReciclajes;
            document.getElementById('totalPuntosHoy').textContent = totalPuntos;
            document.getElementById('totalUsuarios').textContent = ranking.length;
        }
<<<<<<< HEAD
    } catch (error) {}
=======
    } catch (error) {
        console.error('Error cargando stats:', error);
    }
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
}

// ========== VER ESTADÍSTICAS DE OTRO USUARIO ==========
function verEstadisticasDeUsuario() {
    const selector = document.getElementById('selector_usuario');
    const usuarioId = selector.value;
    const infoDiv = document.getElementById('infoUsuarioSeleccionado');
    
    if (!usuarioId) {
        mostrarNotificacion('⚠️ Selecciona un usuario', 'warning');
        return;
    }
    
    document.getElementById('usuario_id').value = usuarioId;
    guardarUsuarioSeleccionado();
    cargarEstadisticas();
    
    const selectedOption = selector.options[selector.selectedIndex];
    const nombreUsuario = selectedOption.text.split(' - ')[1]?.split(' (')[0] || 'Usuario';
    
    infoDiv.innerHTML = `<i class="fas fa-info-circle"></i> Mostrando estadísticas de: <strong>${nombreUsuario}</strong> (ID: ${usuarioId})`;
    infoDiv.classList.add('show');
<<<<<<< HEAD
    mostrarNotificacion(`📊 Mostrando estadísticas de ${nombreUsuario}`, 'success');
=======
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
}

// ========== ELIMINAR USUARIOS ==========
async function eliminarUsuario() {
    const usuarioId = document.getElementById('eliminar_usuario_id').value;
    const mensajeDiv = document.getElementById('mensaje_eliminar');
    
    if (!usuarioId) {
<<<<<<< HEAD
        mensajeDiv.innerHTML = '<p style="color:#e74c3c;">❌ Ingresa un ID</p>';
        return;
    }
=======
        mensajeDiv.innerHTML = '<p style="color: #e74c3c;">❌ Ingresa un ID de usuario</p>';
        return;
    }
    
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
    if (!confirm(`⚠️ ¿Eliminar usuario ID ${usuarioId}?`)) return;
    
    try {
        const response = await fetch(`/eliminar_usuario/${usuarioId}`, { method: 'DELETE' });
        const data = await response.json();
<<<<<<< HEAD
        if (response.ok) {
            mensajeDiv.innerHTML = `<p style="color:#2ecc71;">✅ ${data.mensaje}</p>`;
            document.getElementById('eliminar_usuario_id').value = '';
            await cargarListaUsuarios();
            cargarRanking();
            cargarStatsHeader();
            if (parseInt(usuarioId) === parseInt(document.getElementById('usuario_id').value)) {
                document.getElementById('estadisticas').innerHTML = `
                    <div class="stat-detail-card" style="grid-column: 1/-1; text-align: center;">
=======
        
        if (response.ok && data.status === 'ok') {
            mensajeDiv.innerHTML = `<p style="color: #2ecc71;">✅ ${data.mensaje}</p>`;
            document.getElementById('eliminar_usuario_id').value = '';
            cargarRanking();
            cargarEstadisticas();
            cargarStatsHeader();
            cargarListaUsuarios();
            mostrarNotificacion(data.mensaje, 'success');
            
            // Si el usuario eliminado era el actual, limpiar estadísticas
            if (parseInt(usuarioId) === parseInt(document.getElementById('usuario_id').value)) {
                document.getElementById('estadisticas').innerHTML = `
                    <div class="stat-detail-card" style="grid-column: 1/-1; text-align: center;">
                        <i class="fas fa-user-slash"></i>
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
                        <div class="stat-label">USUARIO ELIMINADO</div>
                        <div class="stat-number" style="font-size: 14px;">El usuario ya no existe</div>
                    </div>
                `;
                document.getElementById('usuario_id').value = '';
                localStorage.removeItem('usuarioSeleccionado');
            }
        } else {
<<<<<<< HEAD
            mensajeDiv.innerHTML = `<p style="color:#e74c3c;">❌ ${data.error}</p>`;
        }
    } catch (error) {
        mensajeDiv.innerHTML = '<p style="color:#e74c3c;">❌ Error</p>';
=======
            mensajeDiv.innerHTML = `<p style="color: #e74c3c;">❌ Error: ${data.error}</p>`;
        }
    } catch (error) {
        mensajeDiv.innerHTML = '<p style="color: #e74c3c;">❌ Error al eliminar usuario</p>';
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
    }
    setTimeout(() => { mensajeDiv.innerHTML = ''; }, 5000);
}

async function eliminarTodosUsuarios() {
    if (!confirm('⚠️⚠️⚠️ ¿ELIMINAR TODOS LOS USUARIOS? Esta acción NO se puede deshacer ⚠️⚠️⚠️')) return;
<<<<<<< HEAD
    if (!confirm('ÚLTIMA OPORTUNIDAD - ¿Estás SEGURO?')) return;
=======
    if (!confirm('ÚLTIMA OPORTUNIDAD - ¿Estás ABSOLUTAMENTE SEGURO?')) return;
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
    
    try {
        const response = await fetch('/eliminar_todos_usuarios', { method: 'DELETE' });
        const data = await response.json();
<<<<<<< HEAD
        if (response.ok) {
            document.getElementById('mensaje_eliminar').innerHTML = `<p style="color:#2ecc71;">✅ ${data.mensaje}</p>`;
            await cargarListaUsuarios();
            cargarRanking();
            cargarStatsHeader();
            document.getElementById('usuario_id').value = '';
            localStorage.removeItem('usuarioSeleccionado');
=======
        const mensajeDiv = document.getElementById('mensaje_eliminar');
        
        if (response.ok && data.status === 'ok') {
            mensajeDiv.innerHTML = `<p style="color: #2ecc71;">✅ ${data.mensaje}</p>`;
            cargarRanking();
            cargarEstadisticas();
            cargarStatsHeader();
            cargarListaUsuarios();
            document.getElementById('usuario_id').value = '';
            localStorage.removeItem('usuarioSeleccionado');
            mostrarNotificacion(data.mensaje, 'success');
        } else {
            mensajeDiv.innerHTML = `<p style="color: #e74c3c;">❌ Error: ${data.error}</p>`;
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

<<<<<<< HEAD
// ========== CÁMARA ==========
=======
// ========== CÁMARA Y DETECCIÓN AUTOMÁTICA ==========
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
async function activarCamara() {
    const video = document.getElementById('videoCamara');
    const preview = document.getElementById('camaraPreview');
    const btnActivar = document.getElementById('btnActivarCamara');
    const btnDetener = document.getElementById('btnDetenerCamara');
    
    if (streamCamara && isAutoDetecting) {
        detenerCamara();
        return;
    }
    
<<<<<<< HEAD
    const usuario_id = document.getElementById('usuario_id').value;
    if (!usuario_id) {
        mostrarNotificacion('⚠️ Primero selecciona un usuario', 'warning');
=======
    // Verificar que haya un usuario seleccionado
    const usuario_id = document.getElementById('usuario_id').value;
    if (!usuario_id) {
        mostrarNotificacion('⚠️ Primero selecciona o crea un usuario', 'warning');
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
        return;
    }
    
    try {
<<<<<<< HEAD
        streamCamara = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
=======
        streamCamara = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } 
        });
        
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
        video.srcObject = streamCamara;
        preview.style.display = 'block';
        btnActivar.style.display = 'none';
        btnDetener.style.display = 'flex';
<<<<<<< HEAD
        await new Promise((resolve) => { video.onloadedmetadata = () => { video.play(); resolve(); }; });
=======
        
        await new Promise((resolve) => {
            video.onloadedmetadata = () => { video.play(); resolve(); };
        });
        
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
        iniciarDeteccionAutomatica();
        mostrarNotificacion('🎥 Escaneo automático activado', 'success');
    } catch (error) {
        mostrarNotificacion('❌ No se pudo acceder a la cámara', 'error');
    }
}

function detenerCamara() {
    detenerDeteccionAutomatica();
    if (streamCamara) {
        streamCamara.getTracks().forEach(track => track.stop());
        streamCamara = null;
    }
    document.getElementById('camaraPreview').style.display = 'none';
    document.getElementById('btnActivarCamara').style.display = 'flex';
    document.getElementById('btnDetenerCamara').style.display = 'none';
    mostrarNotificacion('⏸️ Escaneo detenido', 'warning');
}

function iniciarDeteccionAutomatica() {
    if (autoDetectInterval) clearInterval(autoDetectInterval);
    isAutoDetecting = true;
<<<<<<< HEAD
    const overlay = document.getElementById('previewOverlay');
    if (overlay) {
        overlay.innerHTML = '🟢 ESCANEANDO...';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.6)';
=======
    
    const overlay = document.getElementById('previewOverlay');
    if (overlay) {
        overlay.innerHTML = '🟢 ESCANEANDO...';
        overlay.style.background = 'rgba(46, 204, 113, 0.8)';
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
    }
    
    autoDetectInterval = setInterval(async () => {
        if (isAutoDetecting && streamCamara && streamCamara.active) {
            if (Date.now() - lastDetectionTime < DEBOUNCE_TIME) return;
            await tomarFotoAutomatica();
        }
    }, AUTO_DETECT_INTERVAL);
}

function detenerDeteccionAutomatica() {
<<<<<<< HEAD
    if (autoDetectInterval) clearInterval(autoDetectInterval);
    isAutoDetecting = false;
=======
    if (autoDetectInterval) {
        clearInterval(autoDetectInterval);
        autoDetectInterval = null;
    }
    isAutoDetecting = false;
    
    const overlay = document.getElementById('previewOverlay');
    if (overlay) {
        overlay.innerHTML = '⏸️ DETENIDO';
        overlay.style.background = 'rgba(0, 0, 0, 0.7)';
        setTimeout(() => {
            if (overlay && !isAutoDetecting) overlay.innerHTML = '🔍 Cámara activa';
        }, 2000);
    }
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
}

async function tomarFotoAutomatica() {
    const video = document.getElementById('videoCamara');
    const canvas = document.getElementById('canvasCamara');
    const usuario_id = document.getElementById('usuario_id').value;
<<<<<<< HEAD
    const overlay = document.getElementById('previewOverlay');
    
    if (!usuario_id) { detenerCamara(); return; }
    if (!video || !canvas || !video.videoWidth) return;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    
    if (overlay) {
        overlay.innerHTML = '🔍 BUSCANDO BOTELLA...';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.7)';
    }
=======
    
    if (!usuario_id) {
        detenerCamara();
        mostrarNotificacion('⚠️ Usuario no seleccionado', 'warning');
        return;
    }
    
    if (!video || !canvas || !video.videoWidth || !video.videoHeight) return;
    
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
    
    canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('imagen', blob, 'botella.jpg');
        formData.append('usuario_id', usuario_id);
        
        try {
            const response = await fetch('/clasificar_webcam', { method: 'POST', body: formData });
            const data = await response.json();
            
            if (response.ok && data.status === 'ok') {
                lastDetectionTime = Date.now();
                agregarDeteccion(data.tipo_es, data.puntos, data.confianza);
                cargarRanking();
                cargarEstadisticas();
                cargarStatsHeader();
<<<<<<< HEAD
                
                if (overlay) {
                    overlay.innerHTML = `✅ ${data.tipo_nombre} +${data.puntos} pts`;
                    overlay.style.backgroundColor = 'rgba(46,204,113,0.85)';
                    setTimeout(() => {
                        if (overlay && isAutoDetecting) {
                            overlay.innerHTML = '🟢 ESCANEANDO...';
                            overlay.style.backgroundColor = 'rgba(0,0,0,0.6)';
                        }
                    }, 1500);
                }
                mostrarNotificacion(`🎉 ${data.mensaje}`, 'success');
            } else if (data.error === 'no_bottle') {
                if (overlay) {
                    overlay.innerHTML = '📷 SIN BOTELLA - Acerca una botella';
                    overlay.style.backgroundColor = 'rgba(231,76,60,0.85)';
                    setTimeout(() => {
                        if (overlay && isAutoDetecting) {
                            overlay.innerHTML = '🟢 ESCANEANDO...';
                            overlay.style.backgroundColor = 'rgba(0,0,0,0.6)';
                        }
                    }, 1200);
                }
            } else if (data.error === 'bottle_too_small') {
                if (overlay) {
                    overlay.innerHTML = '🔍 BOTELLA MUY PEQUEÑA - Acércate más';
                    overlay.style.backgroundColor = 'rgba(241,196,15,0.85)';
                    setTimeout(() => {
                        if (overlay && isAutoDetecting) {
                            overlay.innerHTML = '🟢 ESCANEANDO...';
                            overlay.style.backgroundColor = 'rgba(0,0,0,0.6)';
                        }
                    }, 1200);
                }
                mostrarNotificacion('📱 Acerca la botella a la cámara', 'warning');
            } else if (data.error) {
                console.error('Error:', data.error);
                if (overlay && isAutoDetecting) {
                    overlay.innerHTML = '⚠️ ERROR - Reintentando...';
                    overlay.style.backgroundColor = 'rgba(231,76,60,0.85)';
                    setTimeout(() => {
                        if (overlay && isAutoDetecting) {
                            overlay.innerHTML = '🟢 ESCANEANDO...';
                            overlay.style.backgroundColor = 'rgba(0,0,0,0.6)';
                        }
                    }, 1000);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            if (overlay && isAutoDetecting) {
                overlay.innerHTML = '⚠️ ERROR DE CONEXIÓN';
                overlay.style.backgroundColor = 'rgba(231,76,60,0.85)';
                setTimeout(() => {
                    if (overlay && isAutoDetecting) {
                        overlay.innerHTML = '🟢 ESCANEANDO...';
                        overlay.style.backgroundColor = 'rgba(0,0,0,0.6)';
                    }
                }, 1500);
            }
=======
                mostrarEfectoFlash();
                
                const overlay = document.getElementById('previewOverlay');
                if (overlay && isAutoDetecting) {
                    overlay.innerHTML = `✅ ${data.tipo_nombre}! +${data.puntos} pts`;
                    overlay.style.background = 'rgba(46, 204, 113, 0.9)';
                    setTimeout(() => {
                        if (overlay && isAutoDetecting) {
                            overlay.innerHTML = '🟢 ESCANEANDO...';
                            overlay.style.background = 'rgba(46, 204, 113, 0.8)';
                        }
                    }, 1500);
                }
            }
        } catch (error) {
            // Error silencioso para no molestar
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
        }
    }, 'image/jpeg', 0.8);
}

<<<<<<< HEAD
=======
function mostrarEfectoFlash() {
    const flash = document.createElement('div');
    flash.className = 'flash-effect';
    document.body.appendChild(flash);
    setTimeout(() => flash.remove(), 300);
}

>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
function agregarDeteccion(tipo, puntos, confianza = null) {
    const hora = new Date().toLocaleTimeString();
    detecciones.unshift({ tipo, puntos, hora, confianza });
    if (detecciones.length > 15) detecciones.pop();
    
    const container = document.getElementById('ultimasDetecciones');
    if (!container) return;
    
    if (detecciones.length === 0) {
        container.innerHTML = '<p class="empty-msg">Activa la cámara para comenzar</p>';
        return;
    }
    
    let html = '';
    detecciones.forEach(det => {
        let icono = det.tipo === 'plastico' ? '🥤' : det.tipo === 'vidrio' ? '🍾' : '🥫';
<<<<<<< HEAD
        let claseColor = det.tipo === 'plastico' ? 'plastico' : det.tipo === 'vidrio' ? 'vidrio' : 'lata';
        let confianzaText = det.confianza ? ` (${det.confianza}%)` : '';
        
        html += `<div class="deteccion-item">
                    <div class="tipo-material ${claseColor}">
                        <span>${icono}</span>
                        <span>${det.tipo.toUpperCase()}${confianzaText}</span>
                    </div>
                    <span class="puntos">⭐ +${det.puntos}</span>
                    <span class="hora">${det.hora}</span>
                 </div>`;
=======
        let clase = det.tipo === 'plastico' ? 'plastico' : det.tipo === 'vidrio' ? 'vidrio' : 'lata';
        html += `
            <div class="deteccion-item">
                <span class="tipo ${clase}">${icono} ${det.tipo.toUpperCase()}</span>
                <span>⭐ +${det.puntos} pts</span>
                <span class="hora">${det.hora}</span>
            </div>
        `;
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
    });
    container.innerHTML = html;
}

<<<<<<< HEAD
// ========== EVENTOS ==========
=======
// ========== EVENTOS ADICIONALES ==========
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
document.getElementById('usuario_id')?.addEventListener('change', () => {
    guardarUsuarioSeleccionado();
    cargarEstadisticas();
});

<<<<<<< HEAD
=======
// Botón para ver estadísticas de otro usuario
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
const btnVerEstadisticas = document.getElementById('btnVerEstadisticas');
if (btnVerEstadisticas) {
    btnVerEstadisticas.addEventListener('click', verEstadisticasDeUsuario);
}

// ========== ANIMACIONES ==========
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
    @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    @keyframes flash { 0% { opacity: 0; } 50% { opacity: 0.5; } 100% { opacity: 0; } }
    .flash-effect { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: white; pointer-events: none; animation: flash 0.3s ease-out; z-index: 9999; }
`;
document.head.appendChild(style);

<<<<<<< HEAD
// ========== INICIALIZACIÓN FINAL ==========
cargarRanking();
cargarEstadisticas();
cargarStatsHeader();

console.log('✅ App.js cargado - Sin parpadeos y con persistencia de usuario');
=======
// ========== CARGAR AL INICIAR ==========
cargarRanking();
cargarEstadisticas();
cargarStatsHeader();
cargarListaUsuarios();
>>>>>>> 9c8f610d0fc3e4776aef5e8bc91acb6d559abc18
