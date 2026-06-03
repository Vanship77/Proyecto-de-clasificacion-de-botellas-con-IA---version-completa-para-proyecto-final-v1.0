// static/js/app.js - Versión con selector de usuarios

const nombresTipos = {
    'plastic': '🥤 PLÁSTICO',
    'glass': '🍾 VIDRIO',
    'metal': '🥫 LATA'
};

// Modo oscuro/claro
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

// Slider de confianza
const confianzaSlider = document.getElementById('confianza');
const confianzaValue = document.getElementById('confianzaValue');
const confidenceFill = document.getElementById('confidenceFill');

if (confianzaSlider) {
    confianzaSlider.addEventListener('input', function() {
        const value = this.value;
        confianzaValue.textContent = value + '%';
        if (confidenceFill) {
            confidenceFill.style.width = value + '%';
        }
    });
}

// Registrar reciclaje
async function registrarReciclaje() {
    const usuario_id = document.getElementById('usuario_id').value;
    const tipo = document.getElementById('tipo_residuo').value;
    const confianza = parseFloat(document.getElementById('confianza').value);

    const loading = document.getElementById('loading');
    const resultado = document.getElementById('resultado');
    
    loading.style.display = 'block';
    resultado.className = 'resultado';
    resultado.style.display = 'none';

    try {
        const response = await fetch('/reciclar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                usuario_id: parseInt(usuario_id),
                tipo: tipo,
                confianza: confianza
            })
        });

        const data = await response.json();

        if (response.ok && data.status === 'ok') {
            resultado.className = 'resultado exito';
            resultado.innerHTML = `
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <div style="font-size: 50px;">🎉</div>
                    <div style="flex: 1;">
                        <h3>✅ ¡RECICLAJE EXITOSO!</h3>
                        <p>📦 Has ingresado una botella de <strong>${nombresTipos[tipo]}</strong></p>
                        <p>⭐ Ganaste <strong>${data.puntos_ganados} puntos</strong></p>
                        <p>🏆 Total acumulado: <strong>${data.puntos_totales} puntos</strong></p>
                    </div>
                </div>
                <div class="confidence-bar" style="margin-top: 15px;">
                    <div class="confidence-fill" style="width: ${confianza}%; background: #28a745;"></div>
                </div>
                <p style="margin-top: 15px; font-size: 14px;">🌍 ¡Gracias por reciclar! Sigue así.</p>
            `;
            mostrarNotificacion('¡Reciclaje registrado!', 'success');
        } else {
            throw new Error(data.mensaje || data.error || 'Error al registrar');
        }
    } catch (error) {
        resultado.className = 'resultado error';
        resultado.innerHTML = `
            <h3>❌ ERROR</h3>
            <p>${error.message}</p>
            <p>⚠️ Verifica que el usuario exista en la base de datos.</p>
            <p>💡 Crea un usuario en la sección "Crear Nuevo Usuario"</p>
        `;
        mostrarNotificacion(error.message, 'error');
    } finally {
        loading.style.display = 'none';
        cargarRanking();
        cargarEstadisticas();
        cargarStatsHeader();
        cargarListaUsuarios();
    }
}

// Notificaciones toast
function mostrarNotificacion(mensaje, tipo) {
    const toast = document.createElement('div');
    toast.className = `toast-notification ${tipo}`;
    
    let icono = '';
    if (tipo === 'success') icono = 'fa-check-circle';
    else if (tipo === 'error') icono = 'fa-exclamation-circle';
    else icono = 'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fas ${icono}"></i>
        <span>${mensaje}</span>
    `;
    
    let color = '#2ecc71';
    if (tipo === 'error') color = '#e74c3c';
    else if (tipo === 'warning') color = '#f39c12';
    
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${color};
        color: white;
        padding: 12px 20px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 2000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Crear nuevo usuario
async function crearUsuario() {
    const nombre = document.getElementById('nuevo_nombre').value;
    const email = document.getElementById('nuevo_email').value;
    const mensajeDiv = document.getElementById('mensaje_usuario');

    if (!nombre || !email) {
        mensajeDiv.innerHTML = '<p style="color: #e74c3c;"><i class="fas fa-times-circle"></i> Completa nombre y email</p>';
        return;
    }

    try {
        const response = await fetch('/crear_usuario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre: nombre, email: email })
        });

        const data = await response.json();

        if (response.status === 201) {
            mensajeDiv.innerHTML = `<p style="color: #2ecc71;"><i class="fas fa-check-circle"></i> Usuario creado exitosamente! ID: ${data.id}</p>`;
            document.getElementById('nuevo_nombre').value = '';
            document.getElementById('nuevo_email').value = '';
            document.getElementById('usuario_id').value = data.id;
            cargarRanking();
            cargarStatsHeader();
            cargarListaUsuarios();
            mostrarNotificacion(`Usuario ${nombre} creado`, 'success');
        } else {
            mensajeDiv.innerHTML = `<p style="color: #e74c3c;">❌ Error: ${data.error}</p>`;
        }
    } catch (error) {
        mensajeDiv.innerHTML = `<p style="color: #e74c3c;">❌ Error al crear usuario</p>`;
    }
}

// Cargar ranking mejorado
async function cargarRanking() {
    try {
        const response = await fetch('/ranking');
        const ranking = await response.json();

        if (!response.ok || ranking.error) {
            document.getElementById('ranking').innerHTML = '<p class="error-msg">❌ Error cargando ranking</p>';
            return;
        }

        if (ranking.length === 0) {
            document.getElementById('ranking').innerHTML = '<p class="empty-msg">📭 No hay reciclajes registrados aún</p>';
            return;
        }

        let html = '';
        ranking.forEach((user, index) => {
            let positionClass = '';
            let medal = '';
            if (index === 0) {
                positionClass = 'top-1';
                medal = '🥇';
            } else if (index === 1) {
                positionClass = 'top-2';
                medal = '🥈';
            } else if (index === 2) {
                positionClass = 'top-3';
                medal = '🥉';
            } else {
                medal = `${index + 1}º`;
            }
            
            html += `
                <div class="ranking-item">
                    <div class="ranking-position ${positionClass}">${medal}</div>
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

// Cargar estadísticas mejorado CON ETIQUETAS CLARAS
async function cargarEstadisticas() {
    const usuario_id = document.getElementById('usuario_id').value;
    if (!usuario_id) return;

    try {
        const response = await fetch(`/estadisticas/${usuario_id}`);
        const data = await response.json();

        if (response.ok && !data.error) {
            document.getElementById('estadisticas').innerHTML = `
                <!-- Tarjeta 1: Información del usuario -->
                <div class="stat-detail-card">
                    <i class="fas fa-user-circle"></i>
                    <div class="stat-label">USUARIO</div>
                    <div class="stat-number">${data.nombre}</div>
                    <div class="stat-sub">ID: ${usuario_id}</div>
                </div>
                
                <!-- Tarjeta 2: Puntos totales -->
                <div class="stat-detail-card">
                    <i class="fas fa-star"></i>
                    <div class="stat-label">PUNTOS TOTALES</div>
                    <div class="stat-number">${data.puntos_totales}</div>
                    <div class="stat-sub">⭐ puntos acumulados</div>
                </div>
                
                <!-- Tarjeta 3: Total reciclajes -->
                <div class="stat-detail-card">
                    <i class="fas fa-recycle"></i>
                    <div class="stat-label">TOTAL RECICLAJES</div>
                    <div class="stat-number">${data.total_reciclajes}</div>
                    <div class="stat-sub">♻️ veces reciclado</div>
                </div>
                
                <!-- Tarjeta 4: Promedio por reciclaje -->
                <div class="stat-detail-card">
                    <i class="fas fa-chart-simple"></i>
                    <div class="stat-label">PROMEDIO POR RECICLAJE</div>
                    <div class="stat-number">${data.total_reciclajes > 0 ? Math.round(data.puntos_totales / data.total_reciclajes) : 0} pts</div>
                    <div class="stat-sub">📊 puntos promedio</div>
                </div>
                
                <!-- Tarjeta 5: Botellas de Plástico -->
                    <div class="stat-detail-card">
                    <div style="font-size: 35px; margin-bottom: 8px;">🧴</div>
                    <div class="stat-label">BOTELLAS DE PLÁSTICO</div>
                    <div class="stat-number">${data.plasticos || 0}</div>
                    <div class="stat-sub">🥤 unidades recicladas</div>
                </div>
                
                <!-- Tarjeta 6: Botellas de Vidrio -->
                <div class="stat-detail-card">
                    <i class="fas fa-wine-bottle"></i>
                    <div class="stat-label">BOTELLAS DE VIDRIO</div>
                    <div class="stat-number">${data.vidrios || 0}</div>
                    <div class="stat-sub">🍾 unidades recicladas</div>
                </div>
                
                <!-- Tarjeta 7: Latas de Metal -->
                <div class="stat-detail-card">
                    <i class="fas fa-beer-mug-empty"></i>
                    <div class="stat-label">LATAS DE METAL</div>
                    <div class="stat-number">${data.latas || 0}</div>
                    <div class="stat-sub">🥫 unidades recicladas</div>
                </div>
                
                <!-- Tarjeta 8: Meta de puntos -->
                <div class="stat-detail-card">
                    <i class="fas fa-chart-line"></i>
                    <div class="stat-label">META (100 PUNTOS)</div>
                    <div class="stat-number">${data.puntos_totales >= 100 ? '🏆 LOGRADA' : '🎯 EN PROGRESO'}</div>
                    <div class="stat-sub">${data.puntos_totales}/100 puntos</div>
                    <div class="progress-bar-mini">
                        <div class="progress-fill-mini" style="width: ${Math.min((data.puntos_totales / 100) * 100, 100)}%"></div>
                    </div>
                </div>
            `;
        } else {
            document.getElementById('estadisticas').innerHTML = `
                <div class="stat-detail-card" style="grid-column: 1/-1; text-align: center;">
                    <i class="fas fa-user-slash"></i>
                    <div class="stat-label">USUARIO NO ENCONTRADO</div>
                    <div class="stat-number" style="font-size: 14px;">ID ${usuario_id} no existe</div>
                    <div class="stat-sub">💡 Crea un usuario en la sección de arriba</div>
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('estadisticas').innerHTML = '<p class="error-msg">❌ Error cargando estadísticas</p>';
    }
}

// Cargar lista de usuarios para el selector
async function cargarListaUsuarios() {
    try {
        const response = await fetch('/usuarios');
        const usuarios = await response.json();
        
        const selector = document.getElementById('selector_usuario');
        if (!selector) return;
        
        selector.innerHTML = '<option value="">-- Selecciona un usuario --</option>';
        
        if (usuarios.length === 0) {
            selector.innerHTML += '<option value="" disabled>📭 No hay usuarios registrados</option>';
            return;
        }
        
        usuarios.forEach(usuario => {
            selector.innerHTML += `
                <option value="${usuario.id}">
                    🆔 ${usuario.id} - ${usuario.nombre} (⭐ ${usuario.puntos} pts)
                </option>
            `;
        });
    } catch (error) {
        console.error('Error cargando usuarios:', error);
        const selector = document.getElementById('selector_usuario');
        if (selector) {
            selector.innerHTML = '<option value="">-- Error cargando usuarios --</option>';
        }
    }
}

// Ver estadísticas del usuario seleccionado
function verEstadisticasDeUsuario() {
    const selector = document.getElementById('selector_usuario');
    const usuarioId = selector.value;
    const infoDiv = document.getElementById('infoUsuarioSeleccionado');
    
    if (!usuarioId) {
        mostrarNotificacion('⚠️ Por favor, selecciona un usuario primero', 'warning');
        infoDiv.classList.remove('show');
        return;
    }
    
    document.getElementById('usuario_id').value = usuarioId;
    cargarEstadisticas();
    
    const selectedOption = selector.options[selector.selectedIndex];
    const textoCompleto = selectedOption.text;
    const nombreUsuario = textoCompleto.split(' - ')[1]?.split(' (')[0] || 'Usuario';
    
    infoDiv.innerHTML = `
        <i class="fas fa-info-circle"></i>
        Mostrando estadísticas de: <strong>${nombreUsuario}</strong> (ID: ${usuarioId})
    `;
    infoDiv.classList.add('show');
    
    mostrarNotificacion(`Mostrando estadísticas del usuario ${nombreUsuario}`, 'success');
}

// Cargar stats del header
async function cargarStatsHeader() {
    try {
        const response = await fetch('/ranking');
        const ranking = await response.json();
        
        if (response.ok && !ranking.error) {
            const totalPuntos = ranking.reduce((sum, user) => sum + (user.puntos || 0), 0);
            const totalReciclajes = ranking.reduce((sum, user) => sum + (user.reciclajes || 0), 0);
            
            document.getElementById('totalReciclajesHoy').textContent = totalReciclajes;
            document.getElementById('totalPuntosHoy').textContent = totalPuntos;
            document.getElementById('totalUsuarios').textContent = ranking.length;
        }
    } catch (error) {
        console.error('Error cargando stats:', error);
    }
}

// Eventos
document.getElementById('usuario_id').addEventListener('change', () => {
    cargarEstadisticas();
});
document.getElementById('usuario_id').addEventListener('input', () => {
    cargarEstadisticas();
});

// Evento para el botón de ver estadísticas
const btnVerEstadisticas = document.getElementById('btnVerEstadisticas');
if (btnVerEstadisticas) {
    btnVerEstadisticas.addEventListener('click', verEstadisticasDeUsuario);
}

// Auto-refrescar cada 5 segundos
setInterval(() => {
    cargarRanking();
    cargarEstadisticas();
    cargarStatsHeader();
    cargarListaUsuarios();
}, 5000);

// Animación extra de salida para notificaciones
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Cargar al iniciar
cargarRanking();
cargarEstadisticas();
cargarStatsHeader();
cargarListaUsuarios();

// ========== FUNCIONES PARA ELIMINAR USUARIOS ==========

// Eliminar un usuario específico
async function eliminarUsuario() {
    const usuarioId = document.getElementById('eliminar_usuario_id').value;
    const mensajeDiv = document.getElementById('mensaje_eliminar');
    
    if (!usuarioId) {
        mensajeDiv.innerHTML = '<p style="color: #e74c3c;"><i class="fas fa-times-circle"></i> Ingresa un ID de usuario</p>';
        return;
    }
    
    // Confirmar antes de eliminar
    const confirmar = confirm(`⚠️ ¿Estás seguro de eliminar al usuario ID ${usuarioId}?\n\nSe eliminarán TODOS sus reciclajes y puntos. Esta acción no se puede deshacer.`);
    
    if (!confirmar) return;
    
    try {
        const response = await fetch(`/eliminar_usuario/${usuarioId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'ok') {
            mensajeDiv.innerHTML = `<p style="color: #2ecc71;"><i class="fas fa-check-circle"></i> ${data.mensaje}</p>`;
            document.getElementById('eliminar_usuario_id').value = '';
            // Actualizar todo
            cargarRanking();
            cargarEstadisticas();
            cargarStatsHeader();
            cargarListaUsuarios();
            // Si el usuario eliminado era el actual, limpiar estadísticas
            if (parseInt(usuarioId) === parseInt(document.getElementById('usuario_id').value)) {
                document.getElementById('estadisticas').innerHTML = `
                    <div class="stat-detail-card" style="grid-column: 1/-1; text-align: center;">
                        <i class="fas fa-user-slash"></i>
                        <div class="stat-label">USUARIO ELIMINADO</div>
                        <div class="stat-number" style="font-size: 14px;">El usuario ya no existe</div>
                    </div>
                `;
            }
            mostrarNotificacion(data.mensaje, 'success');
        } else {
            mensajeDiv.innerHTML = `<p style="color: #e74c3c;">❌ Error: ${data.error}</p>`;
            mostrarNotificacion(data.error, 'error');
        }
    } catch (error) {
        mensajeDiv.innerHTML = `<p style="color: #e74c3c;">❌ Error al eliminar usuario</p>`;
        mostrarNotificacion('Error al eliminar usuario', 'error');
    }
    
    // Limpiar mensaje después de 5 segundos
    setTimeout(() => {
        if (mensajeDiv.innerHTML !== '') {
            mensajeDiv.innerHTML = '';
        }
    }, 5000);
}

// ========== FUNCIONES PARA EL SENSOR INFRARROJO Y CÁMARA ==========

// Variables globales
let streamCamara = null;
let detecciones = [];

// Cargar estado del sensor
async function cargarEstadoSensor() {
    try {
        const response = await fetch('/estado_sensor');
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('sensorUsuario').textContent = data.usuario_id;
            
            const led = document.getElementById('sensorLed');
            const estadoText = document.getElementById('sensorEstado');
            
            if (data.conectado) {
                led.className = 'led led-green';
                estadoText.textContent = 'Conectado';
                estadoText.style.color = '#2ecc71';
            } else {
                led.className = 'led led-red';
                estadoText.textContent = 'Desconectado';
                estadoText.style.color = '#e74c3c';
            }
        }
    } catch (error) {
        console.error('Error cargando estado del sensor:', error);
    }
}

// Activar cámara web
async function activarCamara() {
    const video = document.getElementById('videoCamara');
    const preview = document.getElementById('camaraPreview');
    const btnActivar = document.getElementById('btnActivarCamara');
    const btnTomar = document.getElementById('btnTomarFoto');
    
    try {
        streamCamara = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = streamCamara;
        preview.style.display = 'block';
        btnActivar.style.display = 'none';
        btnTomar.style.display = 'flex';
        document.getElementById('camaraEstado').textContent = 'Activa';
        mostrarNotificacion('Cámara activada correctamente', 'success');
    } catch (error) {
        console.error('Error al acceder a la cámara:', error);
        mostrarNotificacion('No se pudo acceder a la cámara', 'error');
    }
}

// Tomar foto y clasificar con IA
async function tomarFoto() {
    const video = document.getElementById('videoCamara');
    const canvas = document.getElementById('canvasCamara');
    const context = canvas.getContext('2d');
    
    // Configurar canvas del tamaño del video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Dibujar la imagen del video en el canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convertir canvas a blob (archivo de imagen)
    canvas.toBlob(async (blob) => {
        const usuario_id = document.getElementById('usuario_id').value;
        
        // Mostrar loading
        const resultado = document.getElementById('resultado');
        resultado.className = 'resultado';
        resultado.style.display = 'none';
        document.getElementById('loading').style.display = 'block';
        
        // Crear FormData para enviar la imagen
        const formData = new FormData();
        formData.append('imagen', blob, 'botella.jpg');
        formData.append('usuario_id', usuario_id);
        
        try {
            const response = await fetch('/clasificar_webcam', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'ok') {
                // Mostrar resultado
                resultado.className = 'resultado exito';
                resultado.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                        <div style="font-size: 50px;">🤖</div>
                        <div style="flex: 1;">
                            <h3>✅ ¡CLASIFICACIÓN EXITOSA!</h3>
                            <p>📦 Botella detectada: <strong>${data.tipo_nombre}</strong></p>
                            <p>⭐ Se han añadido <strong>${data.puntos} puntos</strong></p>
                            <p>📊 Confianza de la IA: <strong>${data.confianza}%</strong></p>
                        </div>
                    </div>
                `;
                
                // Agregar al historial
                agregarDeteccion(data.tipo_es, data.puntos, data.confianza);
                mostrarNotificacion(`Botella de ${data.tipo_nombre} clasificada! +${data.puntos} pts`, 'success');
                
                // Actualizar ranking y estadísticas
                cargarRanking();
                cargarEstadisticas();
                cargarStatsHeader();
            } else {
                throw new Error(data.error || 'Error al clasificar');
            }
        } catch (error) {
            resultado.className = 'resultado error';
            resultado.innerHTML = `
                <h3>❌ ERROR</h3>
                <p>${error.message}</p>
                <p>⚠️ No se pudo clasificar la imagen. Intenta de nuevo.</p>
            `;
            mostrarNotificacion(error.message, 'error');
        } finally {
            document.getElementById('loading').style.display = 'none';
        }
    }, 'image/jpeg', 0.9);
}

// Agregar detección al historial
function agregarDeteccion(tipo, puntos, confianza = null) {
    const ahora = new Date();
    const hora = ahora.toLocaleTimeString();
    
    detecciones.unshift({
        tipo: tipo,
        puntos: puntos,
        hora: hora,
        confianza: confianza
    });
    
    if (detecciones.length > 15) detecciones.pop();
    actualizarListaDetecciones();
}

// Actualizar lista de detecciones en el HTML
function actualizarListaDetecciones() {
    const container = document.getElementById('ultimasDetecciones');
    
    if (detecciones.length === 0) {
        container.innerHTML = '<p class="empty-msg">Esperando detecciones...</p>';
        return;
    }
    
    let html = '';
    detecciones.forEach(det => {
        let tipoClase = '';
        let tipoIcono = '';
        if (det.tipo === 'plastico') {
            tipoClase = 'plastico';
            tipoIcono = '🥤';
        } else if (det.tipo === 'vidrio') {
            tipoClase = 'vidrio';
            tipoIcono = '🍾';
        } else {
            tipoClase = 'lata';
            tipoIcono = '🥫';
        }
        
        let confianzaText = det.confianza ? `<span class="confianza">🤖 ${det.confianza}%</span>` : '';
        
        html += `
            <div class="deteccion-item">
                <span class="tipo ${tipoClase}">${tipoIcono} ${det.tipo.toUpperCase()}</span>
                <span>⭐ +${det.puntos} pts</span>
                ${confianzaText}
                <span class="hora">${det.hora}</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Inicializar eventos de cámara
document.addEventListener('DOMContentLoaded', () => {
    cargarEstadoSensor();
    setInterval(cargarEstadoSensor, 10000);
});

// Eliminar todos los usuarios
async function eliminarTodosUsuarios() {
    const mensajeDiv = document.getElementById('mensaje_eliminar');
    
    // Confirmación más estricta
    const confirmar = confirm(`⚠️⚠️⚠️ ¡ADVERTENCIA! ⚠️⚠️⚠️\n\nEstás a punto de ELIMINAR TODOS los usuarios y TODOS sus reciclajes.\n\nEsta acción NO SE PUEDE DESHACER.\n\n¿Estás ABSOLUTAMENTE SEGURO?`);
    
    if (!confirmar) return;
    
    // Segunda confirmación
    const confirmar2 = confirm(`ÚLTIMA OPORTUNIDAD\n\n¿Realmente quieres eliminar TODOS los usuarios?\n\nSe perderán todos los puntos y reciclajes.`);
    
    if (!confirmar2) return;
    
    try {
        const response = await fetch('/eliminar_todos_usuarios', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'ok') {
            mensajeDiv.innerHTML = `<p style="color: #2ecc71;"><i class="fas fa-check-circle"></i> ${data.mensaje}</p>`;
            // Actualizar todo
            cargarRanking();
            cargarEstadisticas();
            cargarStatsHeader();
            cargarListaUsuarios();
            // Limpiar ID actual
            document.getElementById('usuario_id').value = '1';
            document.getElementById('estadisticas').innerHTML = `
                <div class="stat-detail-card" style="grid-column: 1/-1; text-align: center;">
                    <i class="fas fa-database"></i>
                    <div class="stat-label">BASE DE DATOS VACÍA</div>
                    <div class="stat-number" style="font-size: 14px;">Crea un nuevo usuario</div>
                </div>
            `;
            mostrarNotificacion(data.mensaje, 'success');
        } else {
            mensajeDiv.innerHTML = `<p style="color: #e74c3c;">❌ Error: ${data.error}</p>`;
            mostrarNotificacion(data.error, 'error');
        }
    } catch (error) {
        mensajeDiv.innerHTML = `<p style="color: #e74c3c;">❌ Error al eliminar usuarios</p>`;
        mostrarNotificacion('Error al eliminar usuarios', 'error');
    }
    
    // Limpiar mensaje después de 5 segundos
    setTimeout(() => {
        if (mensajeDiv.innerHTML !== '') {
            mensajeDiv.innerHTML = '';
        }
    }, 5000);
}

