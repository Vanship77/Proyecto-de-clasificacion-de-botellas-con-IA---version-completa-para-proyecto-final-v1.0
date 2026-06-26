// static/js/app.js - Basurero Inteligente con EfficientNetB0 (SIN PARPADEOS)

let streamCamara = null;
let detecciones = [];
let autoDetectInterval = null;
let isAutoDetecting = false;
let lastDetectionTime = 0;

const AUTO_DETECT_INTERVAL = 2000;
const DEBOUNCE_TIME = 3000;

// ========== INICIALIZACIÓN ==========
document.addEventListener('DOMContentLoaded', () => {
    // Mostrar placeholder mientras carga
    mostrarPlaceholder();
    
    cargarListaUsuarios();
    cargarRanking();
    cargarEstadisticas();
    cargarStatsHeader();
    
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

function mostrarNotificacion(mensaje, tipo) {
    const toast = document.createElement('div');
    let icono = tipo === 'success' ? 'fa-check-circle' : tipo === 'warning' ? 'fa-exclamation-triangle' : 'fa-exclamation-circle';
    let color = tipo === 'success' ? '#2ecc71' : tipo === 'warning' ? '#f39c12' : '#e74c3c';
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
        const opcionExiste = Array.from(select.options).some(opt => opt.value == usuarioGuardado);
        if (opcionExiste) {
            select.value = usuarioGuardado;
            cargarEstadisticas();
            
            const selectorEst = document.getElementById('selector_usuario');
            if (selectorEst && Array.from(selectorEst.options).some(opt => opt.value == usuarioGuardado)) {
                selectorEst.value = usuarioGuardado;
            }
        }
    }
}

// ========== USUARIOS ==========
async function crearUsuario() {
    const nombre = document.getElementById('nuevo_nombre').value;
    const email = document.getElementById('nuevo_email').value;
    const mensajeDiv = document.getElementById('mensaje_usuario');
    
    if (!nombre || !email) {
        mensajeDiv.innerHTML = '<p style="color:#e74c3c;">❌ Completa todos los campos</p>';
        return;
    }
    
    try {
        const response = await fetch('/crear_usuario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, email })
        });
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

async function cargarListaUsuarios() {
    try {
        const response = await fetch('/usuarios');
        const usuarios = await response.json();
        const select = document.getElementById('usuario_id');
        if (!select) return;
        
        const valorActual = select.value;
        
        if (usuarios.length === 0) {
            select.innerHTML = '<option value="">No hay usuarios - Crea uno</option>';
            return;
        }
        
        select.innerHTML = '<option value="">-- Selecciona un usuario --</option>';
        usuarios.forEach(usuario => {
            select.innerHTML += `<option value="${usuario.id}">${usuario.nombre} (⭐ ${usuario.puntos} pts)</option>`;
        });
        
        const usuarioGuardado = localStorage.getItem('usuarioSeleccionado');
        
        if (usuarioGuardado && usuarios.some(u => u.id == usuarioGuardado)) {
            select.value = usuarioGuardado;
        } else if (valorActual && usuarios.some(u => u.id == valorActual)) {
            select.value = valorActual;
        } else if (usuarios.length > 0 && !select.value) {
            select.value = usuarios[0].id;
        }
        
        if (select.value && select.value !== '') {
            cargarEstadisticas();
        }
        
        const selectorEstadisticas = document.getElementById('selector_usuario');
        if (selectorEstadisticas) {
            const valorActualEst = selectorEstadisticas.value;
            selectorEstadisticas.innerHTML = '<option value="">-- Selecciona un usuario --</option>';
            usuarios.forEach(usuario => {
                selectorEstadisticas.innerHTML += `<option value="${usuario.id}">🆔 ${usuario.id} - ${usuario.nombre} (⭐ ${usuario.puntos} pts)</option>`;
            });
            if (valorActualEst && usuarios.some(u => u.id == valorActualEst)) {
                selectorEstadisticas.value = valorActualEst;
            } else if (select.value && usuarios.some(u => u.id == select.value)) {
                selectorEstadisticas.value = select.value;
            }
        }
    } catch (error) {
        console.error('Error cargando usuarios:', error);
    }
}

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
                </div>
            `;
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function cargarRanking() {
    try {
        const response = await fetch('/ranking');
        const ranking = await response.json();
        
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
    } catch (error) {}
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
    mostrarNotificacion(`📊 Mostrando estadísticas de ${nombreUsuario}`, 'success');
}

// ========== ELIMINAR USUARIOS ==========
async function eliminarUsuario() {
    const usuarioId = document.getElementById('eliminar_usuario_id').value;
    const mensajeDiv = document.getElementById('mensaje_eliminar');
    
    if (!usuarioId) {
        mensajeDiv.innerHTML = '<p style="color:#e74c3c;">❌ Ingresa un ID</p>';
        return;
    }
    if (!confirm(`⚠️ ¿Eliminar usuario ID ${usuarioId}?`)) return;
    
    try {
        const response = await fetch(`/eliminar_usuario/${usuarioId}`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok) {
            mensajeDiv.innerHTML = `<p style="color:#2ecc71;">✅ ${data.mensaje}</p>`;
            document.getElementById('eliminar_usuario_id').value = '';
            await cargarListaUsuarios();
            cargarRanking();
            cargarStatsHeader();
            if (parseInt(usuarioId) === parseInt(document.getElementById('usuario_id').value)) {
                document.getElementById('estadisticas').innerHTML = `
                    <div class="stat-detail-card" style="grid-column: 1/-1; text-align: center;">
                        <div class="stat-label">USUARIO ELIMINADO</div>
                        <div class="stat-number" style="font-size: 14px;">El usuario ya no existe</div>
                    </div>
                `;
                document.getElementById('usuario_id').value = '';
                localStorage.removeItem('usuarioSeleccionado');
            }
        } else {
            mensajeDiv.innerHTML = `<p style="color:#e74c3c;">❌ ${data.error}</p>`;
        }
    } catch (error) {
        mensajeDiv.innerHTML = '<p style="color:#e74c3c;">❌ Error</p>';
    }
    setTimeout(() => { mensajeDiv.innerHTML = ''; }, 5000);
}

async function eliminarTodosUsuarios() {
    if (!confirm('⚠️⚠️⚠️ ¿ELIMINAR TODOS LOS USUARIOS? Esta acción NO se puede deshacer ⚠️⚠️⚠️')) return;
    if (!confirm('ÚLTIMA OPORTUNIDAD - ¿Estás SEGURO?')) return;
    
    try {
        const response = await fetch('/eliminar_todos_usuarios', { method: 'DELETE' });
        const data = await response.json();
        if (response.ok) {
            document.getElementById('mensaje_eliminar').innerHTML = `<p style="color:#2ecc71;">✅ ${data.mensaje}</p>`;
            await cargarListaUsuarios();
            cargarRanking();
            cargarStatsHeader();
            document.getElementById('usuario_id').value = '';
            localStorage.removeItem('usuarioSeleccionado');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// ================================================================
// 🔥 CÁMARA - VERSIÓN MEJORADA (CON DETECCIÓN DE ENLACE MÓVIL)
// ================================================================

async function activarCamara() {
    const video = document.getElementById('videoCamara');
    const preview = document.getElementById('camaraPreview');
    const btnActivar = document.getElementById('btnActivarCamara');
    const btnDetener = document.getElementById('btnDetenerCamara');
    
    if (streamCamara && isAutoDetecting) {
        detenerCamara();
        return;
    }
    
    const usuario_id = document.getElementById('usuario_id').value;
    if (!usuario_id) {
        mostrarNotificacion('⚠️ Primero selecciona un usuario', 'warning');
        return;
    }
    
    console.log('👤 Usuario activo ID:', usuario_id);
    
    try {
        // 🔥 1. OBTENER LISTA DE CÁMARAS DISPONIBLES
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');
        
        console.log('📷 Cámaras disponibles:');
        videoDevices.forEach((d, i) => console.log(`   ${i+1}. ${d.label}`));
        
        // 🔥 2. BUSCAR CÁMARA QUE NO SEA OBS (ENLACE MÓVIL O CÁMARA REAL)
        let deviceId = null;
        let nombreCamara = '';
        
        // Intentar encontrar Enlace Móvil o cámara real
        const camaraReal = videoDevices.find(d => 
            !d.label.toLowerCase().includes('obs') && 
            !d.label.toLowerCase().includes('virtual') &&
            !d.label.toLowerCase().includes('screen')
        );
        
        if (camaraReal) {
            deviceId = camaraReal.deviceId;
            nombreCamara = camaraReal.label;
            console.log('📱 Usando cámara:', nombreCamara);
        } else if (videoDevices.length > 0) {
            deviceId = videoDevices[0].deviceId;
            nombreCamara = videoDevices[0].label;
            console.log('📷 Usando primera cámara disponible:', nombreCamara);
        }
        
        if (!deviceId) {
            throw new Error('No se encontró ninguna cámara');
        }
        
        // 🔥 3. SOLICITAR ACCESO CON EL DEVICE ID ESPECÍFICO
        streamCamara = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                deviceId: { exact: deviceId },
                width: { ideal: 640 },
                height: { ideal: 480 }
            } 
        });
        
        video.srcObject = streamCamara;
        preview.style.display = 'block';
        btnActivar.style.display = 'none';
        btnDetener.style.display = 'flex';
        
        await new Promise((resolve) => { 
            video.onloadedmetadata = () => { 
                video.play(); 
                resolve(); 
            }; 
        });
        
        iniciarDeteccionAutomatica();
        mostrarNotificacion(`🎥 Cámara activada: ${nombreCamara || 'correctamente'}`, 'success');
        
    } catch (error) {
        console.error('❌ Error al activar cámara:', error);
        
        // 🔥 4. SI FALLA, INTENTAR CON facingMode (modo compatibilidad)
        try {
            console.log('🔄 Intentando con facingMode: environment...');
            streamCamara = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            
            video.srcObject = streamCamara;
            preview.style.display = 'block';
            btnActivar.style.display = 'none';
            btnDetener.style.display = 'flex';
            
            await new Promise((resolve) => { 
                video.onloadedmetadata = () => { 
                    video.play(); 
                    resolve(); 
                }; 
            });
            
            iniciarDeteccionAutomatica();
            mostrarNotificacion('🎥 Cámara activada (modo compatibilidad)', 'success');
            
        } catch (error2) {
            console.error('❌ Error final:', error2);
            mostrarNotificacion('❌ No se pudo acceder a la cámara: ' + error2.message, 'error');
        }
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
    const overlay = document.getElementById('previewOverlay');
    if (overlay) {
        overlay.innerHTML = '🟢 ESCANEANDO...';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.6)';
    }
    
    autoDetectInterval = setInterval(async () => {
        if (isAutoDetecting && streamCamara && streamCamara.active) {
            if (Date.now() - lastDetectionTime < DEBOUNCE_TIME) return;
            await tomarFotoAutomatica();
        }
    }, AUTO_DETECT_INTERVAL);
}

function detenerDeteccionAutomatica() {
    if (autoDetectInterval) clearInterval(autoDetectInterval);
    isAutoDetecting = false;
}

// 🔥 TOMAR FOTO - VERSIÓN MEJORADA
async function tomarFotoAutomatica() {
    const video = document.getElementById('videoCamara');
    const canvas = document.getElementById('canvasCamara');
    const usuario_id = document.getElementById('usuario_id').value;
    const overlay = document.getElementById('previewOverlay');
    
    if (!usuario_id) { 
        console.error('❌ No hay usuario_id, deteniendo cámara');
        detenerCamara(); 
        return; 
    }
    
    if (!video || !canvas || !video.videoWidth) {
        console.error('❌ Video no disponible');
        return;
    }
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    
    if (overlay) {
        overlay.innerHTML = '🔍 BUSCANDO BOTELLA...';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.7)';
    }
    
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
                mostrarNotificacion('📷 No se detectó ninguna botella', 'warning');
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
            } else if (data.error === 'baja_confianza') {
                // 🔥 NUEVO: Manejar confianza baja
                if (overlay) {
                    overlay.innerHTML = `⚠️ ${data.mensaje}`;
                    overlay.style.backgroundColor = 'rgba(241,196,15,0.85)';
                    setTimeout(() => {
                        if (overlay && isAutoDetecting) {
                            overlay.innerHTML = '🟢 ESCANEANDO...';
                            overlay.style.backgroundColor = 'rgba(0,0,0,0.6)';
                        }
                    }, 2000);
                }
                mostrarNotificacion(data.mensaje, 'warning');
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
        }
    }, 'image/jpeg', 0.8);
}

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
    });
    container.innerHTML = html;
}

// ========== EVENTOS ==========
document.getElementById('usuario_id')?.addEventListener('change', () => {
    guardarUsuarioSeleccionado();
    cargarEstadisticas();
});

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

// ========== INICIALIZACIÓN FINAL ==========
cargarRanking();
cargarEstadisticas();
cargarStatsHeader();

console.log('✅ App.js cargado - Sin parpadeos y con persistencia de usuario');