// ══════════════════════════════════════════════════════════
// SLAYER HUB (Jarvis v3.0) — app.js
// Japanese Noir Cyber-Athletic Architecture
// ══════════════════════════════════════════════════════════

const rootStyle = document.documentElement.style;

// ── 1. SLASH TRANSITION & NAVIGATION ──
const views = {
    'hub': document.getElementById('view-hub'),
    'dashboard': document.getElementById('view-dashboard'),
    'profile': document.getElementById('view-profile')
};
const slashOverlay = document.getElementById('slash-overlay');

function navTo(viewId, navElement) {
    if (views[viewId].classList.contains('active')) return;

    // Update nav icons
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    if (navElement) navElement.classList.add('active');

    // Trigger Slash Anim
    slashOverlay.classList.remove('slash-anim');
    void slashOverlay.offsetWidth; // trigger reflow
    slashOverlay.classList.add('slash-anim');

    // Switch views at the peak of the slash (0.3s)
    setTimeout(() => {
        Object.values(views).forEach(v => v.classList.remove('active'));
        views[viewId].classList.add('active');

        // Fire specific view triggers
        if (viewId === 'dashboard') startTelemetry();
        else stopTelemetry();

        if (viewId === 'profile') drawSpiderGraph();

    }, 300);
}

// ── 2. MISSION HUB ──
function openMission(title, icon) {
    const card = document.getElementById('mission-card');
    card.classList.remove('show');
    
    setTimeout(() => {
        document.getElementById('mc-title').innerText = title;
        document.getElementById('mc-icon').innerText = icon;
        
        // Randomize progress
        const max = 10;
        const current = Math.floor(Math.random() * 8) + 1;
        document.getElementById('mc-progress-text').innerText = `${current}/${max}`;
        document.getElementById('mc-progress-fill').style.width = `${(current/max)*100}%`;

        document.getElementById('btn-join-mission').classList.remove('clicked');
        document.getElementById('btn-join-mission').innerText = 'JOIN MISSION';

        card.classList.add('show');
    }, 300);
}

function joinMission(btn) {
    if (btn.classList.contains('clicked')) return;
    
    btn.classList.add('clicked');
    btn.innerText = 'MISSION ACCEPTED';

    // Haptic Clink
    if (navigator.vibrate) {
        // Double sharp pulse mimicking katana clink
        navigator.vibrate([100, 50, 100]);
    }
}

// Initialize first view
setTimeout(() => document.getElementById('mission-card').classList.add('show'), 500);

// ── 3. DYNAMIC THEMING (BREATHING STYLES) ──
const breathingColors = {
    sun: '#FFD700',
    water: '#00D1FF',
    flame: '#FF4D00',
    thunder: '#FFEA00'
};

function setBreathingStyle(styleName) {
    document.querySelectorAll('.style-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`.sb-${styleName}`).classList.add('active');

    const color = breathingColors[styleName];
    rootStyle.setProperty('--theme-color', color);

    // Redraw graph if needed
    if (views['profile'].classList.contains('active')) {
        drawSpiderGraph();
    }
}

// ── 4. TELEMETRY & PARTICLES ──
let telemetryInterval;
let particleRAF;
let isTelemetryActive = false;
const hrVal = document.getElementById('hr-val');
const telemetryBox = document.getElementById('telemetry-box');

function startTelemetry() {
    isTelemetryActive = true;
    let baseHR = 140;
    
    // Fake HR fluctuation
    telemetryInterval = setInterval(() => {
        baseHR += Math.floor(Math.random() * 7) - 3;
        if (baseHR < 120) baseHR = 120;
        if (baseHR > 180) baseHR = 180;
        hrVal.innerText = baseHR;
    }, 2000);

    emitParticles();
}

function stopTelemetry() {
    isTelemetryActive = false;
    clearInterval(telemetryInterval);
    cancelAnimationFrame(particleRAF);
}

function emitParticles() {
    if (!isTelemetryActive) return;

    if (Math.random() > 0.8) {
        createParticle();
    }
    particleRAF = requestAnimationFrame(emitParticles);
}

function createParticle() {
    const p = document.createElement('div');
    p.classList.add('particle');
    
    // Spawn around the ring
    const size = Math.random() * 6 + 2;
    p.style.width = `${size}px`;
    p.style.height = `${size}px`;

    const angle = Math.random() * Math.PI * 2;
    const r = 100; // rough radius of telemetry ring
    const originX = 160 + Math.cos(angle) * r; // assuming roughly 320px width box
    const originY = 160 + Math.sin(angle) * r;

    p.style.left = `50%`;
    p.style.top = `50%`;
    p.style.transform = `translate(-50%, -50%)`;

    telemetryBox.appendChild(p);

    // Animate out
    requestAnimationFrame(() => {
        p.style.transform = `translate(calc(-50% + ${Math.cos(angle)*150}px), calc(-50% + ${Math.sin(angle)*150}px)) scale(0)`;
        p.style.opacity = '0';
    });

    setTimeout(() => { if(telemetryBox.contains(p)) p.remove(); }, 1000);
}

// ── 5. GYROSCOPE RANK BADGE ──
const badge = document.getElementById('rank-badge');
if (window.DeviceOrientationEvent) {
    window.addEventListener('deviceorientation', (e) => {
        // Gamma is left/right tilt [-90 to 90]
        // Beta is front/back tilt [-180 to 180]
        const tiltX = Math.min(Math.max(e.beta - 45, -30), 30); // offset assuming phone held at 45deg
        const tiltY = Math.min(Math.max(e.gamma, -30), 30);

        badge.style.transform = `rotateX(${-tiltX}deg) rotateY(${tiltY}deg)`;
    });
}
// Fallback mouse movement for desktop testing
badge.addEventListener('mousemove', (e) => {
    const rect = badge.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    badge.style.transform = `rotateX(${-y/5}deg) rotateY(${x/5}deg)`;
});
badge.addEventListener('mouseleave', () => {
    badge.style.transform = `rotateX(0deg) rotateY(0deg)`;
});

// ── 6. ATTRIBUTE SPIDER GRAPH ──
function drawSpiderGraph() {
    const canvas = document.getElementById('spider-graph');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Scale for retina
    const size = canvas.parentElement.clientWidth;
    canvas.width = size * 2;
    canvas.height = size * 2;
    ctx.scale(2, 2);

    const cx = size / 2;
    const cy = size / 2;
    const radius = (size / 2) - 30;

    const attributes = ['Power', 'Speed', 'Stamina', 'Technique', 'Co-op'];
    // Randomize stats a bit for demo
    const stats = attributes.map(() => 0.4 + Math.random() * 0.6);

    ctx.clearRect(0, 0, size, size);

    // Get current theme color
    const style = getComputedStyle(document.body);
    const themeColor = style.getPropertyValue('--theme-color').trim();

    // Draw background web
    ctx.strokeStyle = 'rgba(255,255,255,0.1)';
    ctx.lineWidth = 1;
    for (let level = 1; level <= 4; level++) {
        const r = radius * (level / 4);
        ctx.beginPath();
        for (let i = 0; i < attributes.length; i++) {
            const angle = (Math.PI * 2 * i / attributes.length) - Math.PI / 2;
            const x = cx + Math.cos(angle) * r;
            const y = cy + Math.sin(angle) * r;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.stroke();
    }

    // Draw axes & labels
    ctx.font = "12px Outfit";
    ctx.fillStyle = "rgba(255,255,255,0.6)";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    for (let i = 0; i < attributes.length; i++) {
        const angle = (Math.PI * 2 * i / attributes.length) - Math.PI / 2;
        const x = cx + Math.cos(angle) * radius;
        const y = cy + Math.sin(angle) * radius;
        
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(x, y);
        ctx.stroke();

        // Labels
        const lx = cx + Math.cos(angle) * (radius + 20);
        const ly = cy + Math.sin(angle) * (radius + 20);
        ctx.fillText(attributes[i].toUpperCase(), lx, ly);
    }

    // Draw stats polygon
    ctx.beginPath();
    for (let i = 0; i < attributes.length; i++) {
        const angle = (Math.PI * 2 * i / attributes.length) - Math.PI / 2;
        const val = Math.max(0.2, stats[i]); // min 0.2
        const x = cx + Math.cos(angle) * (radius * val);
        const y = cy + Math.sin(angle) * (radius * val);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    
    // Fill
    ctx.fillStyle = themeColor + '60'; // 60 is roughly 40% opacity in hex
    ctx.fill();
    // Stroke
    ctx.strokeStyle = themeColor;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Data points
    ctx.fillStyle = '#fff';
    for (let i = 0; i < attributes.length; i++) {
        const angle = (Math.PI * 2 * i / attributes.length) - Math.PI / 2;
        const val = Math.max(0.2, stats[i]);
        const x = cx + Math.cos(angle) * (radius * val);
        const y = cy + Math.sin(angle) * (radius * val);
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
    }
}

// ── 7. KASUGAI CHAT & JARVIS WEBSOCKET BACKEND ──
const chatLayer = document.getElementById('kasugai-layer');
const chatStream = document.getElementById('chat-stream');
const chatInput = document.getElementById('chat-input');
const fabChat = document.getElementById('fab-chat');
const chatTitle = document.querySelector('.chat-title');

const BACKEND_WS = 'ws://localhost:8765';
let socket = null;
let wsConnected = false;
let pendingCrowMsg = null;

function updateWsBadge(status) {
    if (!chatTitle) return;
    let badge = document.getElementById('kasugai-ws-badge');
    if (!badge) {
        badge = document.createElement('span');
        badge.id = 'kasugai-ws-badge';
        badge.style.fontSize = '0.75rem';
        badge.style.marginLeft = '10px';
        badge.style.padding = '2px 8px';
        badge.style.borderRadius = '10px';
        badge.style.fontFamily = 'var(--font-body, sans-serif)';
        badge.style.verticalAlign = 'middle';
        badge.style.transition = 'all 0.3s ease';
        chatTitle.appendChild(badge);
    }
    if (status === 'connected') {
        badge.textContent = 'ONLINE';
        badge.style.background = 'rgba(0, 209, 255, 0.2)';
        badge.style.color = '#00d1ff';
        badge.style.border = '1px solid rgba(0, 209, 255, 0.4)';
    } else if (status === 'connecting') {
        badge.textContent = 'CONNECTING...';
        badge.style.background = 'rgba(255, 215, 0, 0.2)';
        badge.style.color = '#ffd700';
        badge.style.border = '1px solid rgba(255, 215, 0, 0.4)';
    } else {
        badge.textContent = 'OFFLINE';
        badge.style.background = 'rgba(255, 77, 0, 0.2)';
        badge.style.color = '#ff4d00';
        badge.style.border = '1px solid rgba(255, 77, 0, 0.4)';
    }
}

function connectBackend() {
    updateWsBadge('connecting');
    try {
        socket = new WebSocket(BACKEND_WS);

        socket.onopen = () => {
            wsConnected = true;
            updateWsBadge('connected');
            console.log('[Kasugai WS] Connected to Jarvis backend at ' + BACKEND_WS);
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'status' && data.status === 'thinking') {
                    if (!pendingCrowMsg) {
                        pendingCrowMsg = appendCrowMessage('Caw! Consulting the estate...');
                    }
                } else if (data.type === 'response') {
                    if (pendingCrowMsg && pendingCrowMsg.parentNode) {
                        pendingCrowMsg.innerText = (data.brain ? `[${data.brain}] ` : '') + data.text;
                        pendingCrowMsg = null;
                    } else {
                        appendCrowMessage((data.brain ? `[${data.brain}] ` : '') + data.text);
                    }
                    if (!chatLayer.classList.contains('active')) {
                        fabChat.classList.add('pulse');
                    }
                } else if (data.type === 'pong') {
                    console.log('[Kasugai WS] Pong received');
                }
            } catch (err) {
                console.error('[Kasugai WS] Parse error:', err);
            }
        };

        socket.onerror = () => {
            wsConnected = false;
            updateWsBadge('offline');
        };

        socket.onclose = () => {
            wsConnected = false;
            updateWsBadge('offline');
            console.log('[Kasugai WS] Disconnected. Retrying in 3s...');
            setTimeout(connectBackend, 3000);
        };
    } catch (e) {
        wsConnected = false;
        updateWsBadge('offline');
        setTimeout(connectBackend, 3000);
    }
}

function appendCrowMessage(text) {
    const cDiv = document.createElement('div');
    cDiv.className = 'msg crow';
    cDiv.innerText = text;
    chatStream.appendChild(cDiv);
    chatStream.scrollTop = chatStream.scrollHeight;
    return cDiv;
}

function toggleChat() {
    chatLayer.classList.toggle('active');
    if (chatLayer.classList.contains('active')) {
        chatInput.focus();
        fabChat.classList.remove('pulse'); // Read
    }
}

function sendChat() {
    const text = chatInput.value.trim();
    if (!text) return;

    // User MSG
    const uDiv = document.createElement('div');
    uDiv.className = 'msg user';
    uDiv.innerText = text;
    chatStream.appendChild(uDiv);
    
    chatInput.value = '';
    chatStream.scrollTop = chatStream.scrollHeight;

    if (wsConnected && socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'command', text: text }));
    } else {
        // Offline / Error feedback
        setTimeout(() => {
            appendCrowMessage("Caw! Jarvis backend is offline (ws://localhost:8765). Ensure Jarvis is running.");
            if (!chatLayer.classList.contains('active')) {
                fabChat.classList.add('pulse');
            }
        }, 400);
    }
}

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendChat();
});

// Auto-connect on load
connectBackend();