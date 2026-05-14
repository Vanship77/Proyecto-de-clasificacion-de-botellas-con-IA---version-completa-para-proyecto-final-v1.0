// static/js/app.js

const nombresTipos = {
    'plastic': '🥤 PLÁSTICO',
    'glass': '🍾 VIDRIO',
    'metal': '🥫 LATA'
};

// Registrar reciclaje
async function registrarReciclaje() {
    const usuario_id = document.getElementById('usuario_id').value;
    const tipo = document.getElementById('tipo_residuo').value;
    const confianza = parseFloat(document.getElementById('confianza').value);

    document.getElementById('loading').style.display = 'block';
    document.getElementById('resultado').className = 'resultado';
    document.getElementById('resultado').style.display = 'none';

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
            document.getElementById('resultado').className = 'resultado exito';
            document.getElementById('resultado').innerHTML = `
                <h3>✅ ¡RECICLAJE EXITOSO!</h3>
                <p>📦 Has ingresado una botella de <strong>${nombresTipos[tipo]}</strong></p>
                <p>⭐ Ganaste <strong>${data.puntos_ganados} puntos</strong></p>
                <p>🏆 Total acumulado: <strong>${data.puntos_totales} puntos</strong></p>
                <p>🤖 Confianza de la IA: <strong>${confianza}%</strong></p>
                <hr>
                <p>🌍 ¡Gracias por reciclar! Sigue así.</p>
            `;
        } else {
            throw new Error(data.mensaje || data.error || 'Error al registrar');
        }
    } catch (error) {
        document.getElementById('resultado').className = 'resultado error';
        document.getElementById('resultado').innerHTML = `
            <h3>❌ ERROR</h3>
            <p>${error.message}</p>
            <p>⚠️ Verifica que el usuario exista en la base de datos.</p>
            <p>💡 Crea un usuario en la sección "Crear Nuevo Usuario"</p>
        `;
    } finally {
        document.getElementById('loading').style.display = 'none';
        cargarRanking();
        cargarEstadisticas();
    }
}

// Crear nuevo usuario
async function crearUsuario() {
    const nombre = document.getElementById('nuevo_nombre').value;
    const email = document.getElementById('nuevo_email').value;

    if (!nombre || !email) {
        document.getElementById('mensaje_usuario').innerHTML = '<p style="color: red;">⚠️ Completa nombre y email</p>';
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
            document.getElementById('mensaje_usuario').innerHTML = `
                <p style="color: green;">✅ Usuario creado exitosamente! ID: ${data.id}</p>
            `;
            document.getElementById('nuevo_nombre').value = '';
            document.getElementById('nuevo_email').value = '';
            cargarRanking();
            // Actualizar el ID del usuario al nuevo creado
            document.getElementById('usuario_id').value = data.id;
        } else {
            document.getElementById('mensaje_usuario').innerHTML = `<p style="color: red;">❌ Error: ${data.error}</p>`;
        }
    } catch (error) {
        document.getElementById('mensaje_usuario').innerHTML = `<p style="color: red;">❌ Error al crear usuario</p>`;
    }
}

// Cargar ranking
async function cargarRanking() {
    try {
        const response = await fetch('/ranking');
        const ranking = await response.json();

        if (!response.ok || ranking.error) {
            document.getElementById('ranking').innerHTML = '<p>❌ Error cargando ranking</p>';
            return;
        }

        if (ranking.length === 0) {
            document.getElementById('ranking').innerHTML = '<p>📭 No hay reciclajes registrados aún</p>';
            return;
        }

        let html = '<tr><thead><tr><th>#</th><th>Nombre</th><th>Puntos</th><th>Reciclajes</th></tr></thead><tbody>';
        ranking.forEach((user, index) => {
            html += `<tr>
                        <td>${index + 1}</td>
                        <td><strong>${user.nombre}</strong></td>
                        <td>⭐ ${user.puntos} pts</td>
                        <td>♻️ ${user.reciclajes} veces</td>
                     </tr>`;
        });
        html += '</tbody></table>';
        document.getElementById('ranking').innerHTML = html;
    } catch (error) {
        document.getElementById('ranking').innerHTML = '<p>❌ Error cargando ranking</p>';
    }
}

// Cargar estadísticas
async function cargarEstadisticas() {
    const usuario_id = document.getElementById('usuario_id').value;

    if (!usuario_id) return;

    try {
        const response = await fetch(`/estadisticas/${usuario_id}`);
        const data = await response.json();

        if (response.ok && !data.error) {
            document.getElementById('estadisticas').innerHTML = `
                <table>
                    <thead><tr><th>Métrica</th><th>Valor</th></tr></thead>
                    <tbody>
                        <tr><td>👤 Usuario</td><td><strong>${data.nombre}</strong></td></tr>
                        <tr><td>⭐ Puntos Totales</td><td><strong>${data.puntos_totales}</strong> puntos</td></tr>
                        <tr><td>♻️ Total Reciclajes</td><td><strong>${data.total_reciclajes}</strong> veces</td></tr>
                        <tr><td>🥤 Botellas de Plástico</td><td><span class="badge badge-plastico">${data.plasticos || 0}</span></td></tr>
                        <tr><td>🍾 Botellas de Vidrio</td><td><span class="badge badge-vidrio">${data.vidrios || 0}</span></td></tr>
                        <tr><td>🥫 Latas de Metal</td><td><span class="badge badge-lata">${data.latas || 0}</span></td></tr>
                    </tbody>
                </table>
            `;
        } else {
            document.getElementById('estadisticas').innerHTML = `
                <p>⚠️ Usuario ID ${usuario_id} no encontrado</p>
                <p>💡 Crea un usuario en la sección de arriba</p>
            `;
        }
    } catch (error) {
        document.getElementById('estadisticas').innerHTML = '<p>❌ Error cargando estadísticas</p>';
    }
}

// Eventos
document.getElementById('usuario_id').addEventListener('change', cargarEstadisticas);
document.getElementById('usuario_id').addEventListener('input', cargarEstadisticas);

// Auto-refrescar cada 5 segundos
setInterval(() => {
    cargarRanking();
    cargarEstadisticas();
}, 5000);

// Cargar al iniciar
cargarRanking();
cargarEstadisticas();