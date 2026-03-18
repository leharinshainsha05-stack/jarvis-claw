// ─────────────────────────────────────────────
// JARVIS FRONTEND — app.js
// WebSocket integration with Python backend
// ─────────────────────────────────────────────

const BACKEND_WS = 'ws://localhost:8765';
let socket = null;
let isListening = false;
let recognition = null;
let startTime = Date.now();

// ── DOM Elements ──
const clockEl = document.getElementById('clock');
const dateEl = document.getElementById('date');
const batteryEl = document.getElementById('battery-level');
const batteryFill = document.getElementById('battery-fill');
const statusBadge = document.getElementById('status-badge');
const transcriptYou = document.getElementById('transcript-you');
const jarvisResp = document.getElementById('jarvis-response');
const logList = document.getElementById('log-list');
const commandInput = document.getElementById('command-input');
const speakBtn = document.getElementById('bottom-speak-btn');

// ── Clock ──
function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    if (clockEl) clockEl.textContent = `${h}:${m}:${s}`;
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    if (dateEl) dateEl.textContent = `${months[now.getMonth()]} ${now.getDate()}`;
}
setInterval(updateClock, 1000);
updateClock();

// ── Battery ──
async function updateBattery() {
    try {
        const battery = await navigator.getBattery();
        const update = () => {
            const pct = Math.round(battery.level * 100);
            if (batteryEl) batteryEl.textContent = pct;
            if (batteryFill) batteryFill.style.width = pct + '%';
        };
        update();
        battery.addEventListener('levelchange', update);
    } catch (e) {
        if (batteryEl) batteryEl.textContent = 'N/A';
    }
}
updateBattery();

// ── Weather ──
async function fetchWeather() {
    try {
        const pos = await new Promise((res, rej) =>
            navigator.geolocation.getCurrentPosition(res, rej, { timeout: 5000 })
        );
        const { latitude: lat, longitude: lon } = pos.coords;
        const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`);
        const data = await res.json();
        const tempEl = document.getElementById('temp-val');
        if (tempEl) tempEl.textContent = Math.round(data.current_weather.temperature);

        const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`, { headers: { 'Accept-Language': 'en' } });
        const geoData = await geoRes.json();
        const city = (geoData.address.city || geoData.address.town || geoData.address.village || 'UNKNOWN').toUpperCase();
        const cityEl = document.querySelector('.city');
        if (cityEl) cityEl.textContent = city;

        const codes = { 0: 'CLEAR SKIES', 1: 'MAINLY CLEAR', 2: 'PARTLY CLOUDY', 3: 'OVERCAST', 61: 'LIGHT RAIN', 80: 'RAIN SHOWERS', 95: 'THUNDERSTORM' };
        const condEl = document.querySelector('.condition');
        if (condEl) condEl.textContent = codes[data.current_weather.weathercode] || 'CLEAR';
    } catch (e) { }
}
fetchWeather();

// ── Activity Log ──
function addLog(msg) {
    if (!logList) return;
    const item = document.createElement('div');
    item.className = 'log-item new-log';
    item.textContent = msg;
    logList.prepend(item);
    setTimeout(() => item.classList.remove('new-log'), 2000);
    while (logList.children.length > 12) logList.removeChild(logList.lastChild);
}

// ── Status ──
function setStatus(status) {
    if (!statusBadge) return;
    statusBadge.className = 'status-badge';
    statusBadge.textContent = status;
    if (status === 'LISTENING') statusBadge.classList.add('listening');
    else if (status === 'THINKING') statusBadge.classList.add('thinking');
    else if (status === 'SPEAKING') statusBadge.classList.add('speaking');
}

// ── Display ──
function showUserCommand(text) {
    if (transcriptYou) transcriptYou.textContent = '▷ YOU: ' + text.toUpperCase();
}

function showJarvisResponse(text) {
    if (jarvisResp) jarvisResp.textContent = text;
    setStatus('SPEAKING');
    setTimeout(() => setStatus('STANDBY'), 5000);
}

// ── WebSocket ──
function connectBackend() {
    try {
        socket = new WebSocket(BACKEND_WS);

        socket.onopen = () => {
            addLog('[ NET ] BACKEND CONNECTED');
            setStatus('STANDBY');
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'response') {
                    showJarvisResponse(data.text);
                    addLog('[ JARVIS ] ' + data.text.substring(0, 45) + '...');
                } else if (data.type === 'status') {
                    setStatus(data.status.toUpperCase());
                } else if (data.type === 'log') {
                    addLog(data.message);
                }
            } catch (e) { }
        };

        socket.onclose = () => {
            addLog('[ NET ] DISCONNECTED — RETRYING...');
            setTimeout(connectBackend, 3000);
        };

        socket.onerror = () => { };
    } catch (e) { }
}
connectBackend();

// ── Send Command ──
function sendCommand() {
    const cmd = commandInput.value.trim();
    if (!cmd) return;
    showUserCommand(cmd);
    setStatus('THINKING');
    addLog('[ CMD ] ' + cmd);

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'command', text: cmd }));
    } else {
        handleDemoMode(cmd);
    }
    commandInput.value = '';
}

// ── Enter key ──
if (commandInput) {
    commandInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendCommand();
    });
}

// ── Demo Mode ──
function handleDemoMode(cmd) {
    const lower = cmd.toLowerCase();
    let reply = 'Backend offline. Running in demo mode, sir.';
    if (lower.includes('time')) reply = 'The time is ' + new Date().toLocaleTimeString();
    else if (lower.includes('date')) reply = 'Today is ' + new Date().toDateString();
    else if (lower.includes('hello') || lower.includes('hi')) reply = 'Hello Thambii. All systems online.';
    setTimeout(() => showJarvisResponse(reply), 500);
}

// ── Voice Input ──
function toggleListening() {
    if (isListening) stopListening();
    else startListening();
}

function startListening() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        showJarvisResponse('Speech recognition not supported. Please use Chrome.');
        return;
    }
    recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';

    recognition.onstart = () => {
        isListening = true;
        if (speakBtn) speakBtn.classList.add('mic-active');
        setStatus('LISTENING');
        addLog('[ MIC ] VOICE INPUT ACTIVE');
    };

    recognition.onresult = (e) => {
        const transcript = Array.from(e.results).map(r => r[0].transcript).join('');
        if (transcriptYou) transcriptYou.textContent = '▷ YOU: ' + transcript.toUpperCase();
        if (e.results[0].isFinal) commandInput.value = transcript;
    };

    recognition.onend = () => {
        isListening = false;
        if (speakBtn) speakBtn.classList.remove('mic-active');
        if (commandInput.value.trim()) sendCommand();
        else setStatus('STANDBY');
    };

    recognition.onerror = (e) => {
        isListening = false;
        if (speakBtn) speakBtn.classList.remove('mic-active');
        setStatus('STANDBY');
        addLog('[ MIC ] ERROR: ' + e.error.toUpperCase());
    };

    recognition.start();
}

function stopListening() {
    if (recognition) recognition.stop();
}

// ── Speak button ──
if (speakBtn) speakBtn.addEventListener('click', toggleListening);

// ── Init logs ──
setTimeout(() => addLog('[ SYS ] HUD INITIALIZED'), 400);
setTimeout(() => addLog('[ MURF ] VOICE ENGINE READY'), 900);
setTimeout(() => addLog('[ AI ] OLLAMA GEMMA3 ONLINE'), 1500);