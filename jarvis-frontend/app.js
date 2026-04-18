// ══════════════════════════════════════════════════════════
// JARVIS v2.0 — app.js
// Dual-Brain | Agentic Core | Full WS Integration
// ══════════════════════════════════════════════════════════

const BACKEND_WS = 'ws://localhost:8765';
let socket = null;
let isListening = false;
let recognition = null;
let wsLatencyStart = 0;

// ── Local deadline store (persisted in memory) ──
let deadlines = JSON.parse(localStorage.getItem('jarvis_deadlines') || '[]');

// ── DOM refs ──
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
const arcCore = document.getElementById('arc-core');
const activeBrain = document.getElementById('active-brain-badge');
const wsStatusEl = document.getElementById('ws-status');
const latencyEl = document.getElementById('latency-val');
const lastBrainEl = document.getElementById('last-brain-used');

// ══════════════════════════════════════════════════════════
// CLOCK
// ══════════════════════════════════════════════════════════
function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    if (clockEl) clockEl.textContent = `${h}:${m}:${s}`;
    if (dateEl) dateEl.textContent = `${months[now.getMonth()]} ${now.getDate()}`;
}
setInterval(updateClock, 1000);
updateClock();

// ══════════════════════════════════════════════════════════
// BATTERY
// ══════════════════════════════════════════════════════════
async function updateBattery() {
    try {
        const battery = await navigator.getBattery();
        const refresh = () => {
            const pct = Math.round(battery.level * 100);
            if (batteryEl) batteryEl.textContent = pct;
            if (batteryFill) batteryFill.style.width = pct + '%';
            // warn if critical
            if (pct < 15 && batteryFill) {
                batteryFill.style.background = 'linear-gradient(90deg,#ff4d4d,#ff7700)';
            }
        };
        refresh();
        battery.addEventListener('levelchange', refresh);
    } catch {
        if (batteryEl) batteryEl.textContent = 'N/A';
    }
}
updateBattery();

// ══════════════════════════════════════════════════════════
// WEATHER
// ══════════════════════════════════════════════════════════
async function fetchWeather() {
    try {
        const pos = await new Promise((res, rej) =>
            navigator.geolocation.getCurrentPosition(res, rej, { timeout: 6000 })
        );
        const { latitude: lat, longitude: lon } = pos.coords;

        const [wRes, gRes] = await Promise.all([
            fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`),
            fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`, { headers: { 'Accept-Language': 'en' } })
        ]);
        const [wData, gData] = await Promise.all([wRes.json(), gRes.json()]);

        const tempEl = document.getElementById('temp-val');
        const cityEl = document.getElementById('city-name');
        const condEl = document.getElementById('condition');

        if (tempEl) tempEl.textContent = Math.round(wData.current_weather.temperature);

        const city = (gData.address?.city || gData.address?.town || gData.address?.village || 'UNKNOWN').toUpperCase();
        if (cityEl) cityEl.textContent = city;

        const codes = {
            0: 'CLEAR SKIES', 1: 'MAINLY CLEAR', 2: 'PARTLY CLOUDY',
            3: 'OVERCAST', 45: 'FOGGY', 51: 'DRIZZLE', 61: 'LIGHT RAIN',
            63: 'MODERATE RAIN', 71: 'LIGHT SNOW', 80: 'RAIN SHOWERS',
            95: 'THUNDERSTORM', 96: 'HAIL STORM'
        };
        if (condEl) condEl.textContent = codes[wData.current_weather.weathercode] || 'ATMOSPHERIC';
    } catch { /* silent fail */ }
}
fetchWeather();

// ══════════════════════════════════════════════════════════
// ACTIVITY LOG
// ══════════════════════════════════════════════════════════
function addLog(msg) {
    if (!logList) return;
    const item = document.createElement('div');
    item.className = 'log-item new-log';
    item.textContent = msg;
    logList.prepend(item);
    setTimeout(() => item.classList.remove('new-log'), 2500);
    while (logList.children.length > 15) logList.removeChild(logList.lastChild);
}

// ══════════════════════════════════════════════════════════
// STATUS & ARC REACTOR
// ══════════════════════════════════════════════════════════
function setStatus(status) {
    if (!statusBadge) return;
    const s = status.toUpperCase();
    statusBadge.className = 'status-badge';
    statusBadge.textContent = s;
    if (arcCore) arcCore.className = 'core';

    if (s === 'LISTENING') {
        statusBadge.classList.add('listening');
        if (arcCore) arcCore.classList.add('listening');
    } else if (s === 'THINKING') {
        statusBadge.classList.add('thinking');
        if (arcCore) arcCore.classList.add('thinking');
    } else if (s === 'SPEAKING') {
        statusBadge.classList.add('speaking');
        if (arcCore) arcCore.classList.add('speaking');
    }
}

// ══════════════════════════════════════════════════════════
// BRAIN DISPLAY
// ══════════════════════════════════════════════════════════
function showActiveBrain(brain) {
    if (!activeBrain) return;
    const labels = {
        PERSONAL: '◈ PERSONAL BRAIN',
        GENERAL: '◉ GENERAL BRAIN',
        LOCAL: '◎ LOCAL FALLBACK',
        VISION: '◑ SCREEN VISION',
        AGENTIC: '⚡ AGENTIC CORE',
        SYSTEM: '⚙ SYSTEM',
    };
    activeBrain.textContent = labels[brain] || brain;
    activeBrain.className = `active-brain-badge visible ${brain}`;
    if (lastBrainEl) lastBrainEl.textContent = `BRAIN: ${brain}`;

    // Highlight brain status bar
    document.querySelectorAll('.brain-indicator').forEach(el => el.classList.remove('active'));
    if (brain === 'PERSONAL') document.getElementById('brain-personal')?.classList.add('active');
    if (brain === 'GENERAL') document.getElementById('brain-general')?.classList.add('active');

    setTimeout(() => { if (activeBrain) activeBrain.classList.remove('visible'); }, 6000);
}

// ══════════════════════════════════════════════════════════
// RESPONSE DISPLAY
// ══════════════════════════════════════════════════════════
function showUserCommand(text) {
    if (transcriptYou) transcriptYou.textContent = '▷ YOU: ' + text.toUpperCase();
}

function showJarvisResponse(text, brain = '') {
    if (jarvisResp) jarvisResp.textContent = text;
    setStatus('SPEAKING');
    if (brain) showActiveBrain(brain);

    // Store conversation automatically
    const userText = transcriptYou?.textContent?.replace('▷ YOU: ', '') || '';
    if (userText && text) {
        storeConversation(userText, text, brain || 'GENERAL');
    }

    addLog('[ JARVIS ] ' + text.substring(0, 50) + (text.length > 50 ? '...' : ''));
    setTimeout(() => setStatus('STANDBY'), 6000);
}

// ══════════════════════════════════════════════════════════
// WEBSOCKET
// ══════════════════════════════════════════════════════════
function connectBackend() {
    try {
        socket = new WebSocket(BACKEND_WS);

        socket.onopen = () => {
            addLog('[ NET ] BACKEND CONNECTED — v2.0');
            if (wsStatusEl) wsStatusEl.textContent = 'WS: CONNECTED';
            setStatus('STANDBY');
            // Request memory stats on connect
            setTimeout(requestMemory, 1500);
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // Latency measurement
                if (wsLatencyStart && latencyEl) {
                    latencyEl.textContent = Date.now() - wsLatencyStart;
                    wsLatencyStart = 0;
                }

                if (data.type === 'response') {
                    showJarvisResponse(data.text, data.brain || '');
                } else if (data.type === 'status') {
                    setStatus(data.status.toUpperCase());
                } else if (data.type === 'log') {
                    addLog(data.message);
                } else if (data.type === 'memory_response') {
                    updateMemoryPanel(data.summary);
                } else if (data.type === 'agentic') {
                    handleAgenticEvent(data);
                } else if (data.type === 'pong') {
                    // heartbeat ok
                }
            } catch { /* malformed message */ }
        };

        socket.onclose = () => {
            addLog('[ NET ] DISCONNECTED — RETRYING IN 3s...');
            if (wsStatusEl) wsStatusEl.textContent = 'WS: RECONNECTING...';
            setTimeout(connectBackend, 3000);
        };

        socket.onerror = () => {
            if (wsStatusEl) wsStatusEl.textContent = 'WS: ERROR';
        };

    } catch { /* connection refused */ }
}
connectBackend();

// Heartbeat ping every 30s
setInterval(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000);

// ══════════════════════════════════════════════════════════
// SEND COMMAND
// ══════════════════════════════════════════════════════════
function sendCommand(cmdOverride) {
    const cmd = cmdOverride || (commandInput ? commandInput.value.trim() : '');
    if (!cmd) return;

    showUserCommand(cmd);
    setStatus('THINKING');
    addLog('[ CMD ] ' + cmd);
    wsLatencyStart = Date.now();

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'command', text: cmd }));
    } else {
        handleDemoMode(cmd);
    }
    if (commandInput) commandInput.value = '';
}

// Quick command helper (for comms tab icons)
function sendQuickCmd(cmd) {
    showUserCommand(cmd);
    setStatus('THINKING');
    addLog('[ QUICK ] ' + cmd);
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'command', text: cmd }));
    }
}

// Enter key on input
if (commandInput) {
    commandInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') sendCommand();
    });
}

// ══════════════════════════════════════════════════════════
// DEMO MODE (backend offline)
// ══════════════════════════════════════════════════════════
function handleDemoMode(cmd) {
    const lower = cmd.toLowerCase();
    let reply = 'Backend offline. Running in demo mode, Thambii.';
    if (lower.includes('time')) reply = 'The time is ' + new Date().toLocaleTimeString();
    else if (lower.includes('date')) reply = 'Today is ' + new Date().toDateString();
    else if (lower.includes('hello') || lower.includes('hi')) reply = 'Hello, Thambii. All systems operational in demo mode.';
    else if (lower.includes('brief')) reply = 'Morning brief unavailable in demo mode. Connect backend to enable.';
    setTimeout(() => showJarvisResponse(reply, 'LOCAL'), 500);
}

// ══════════════════════════════════════════════════════════
// VOICE INPUT
// ══════════════════════════════════════════════════════════
function toggleListening() {
    isListening ? stopListening() : startListening();
}

function startListening() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        showJarvisResponse('Speech recognition requires Chrome or Edge, Thambii.');
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

    recognition.onresult = e => {
        const transcript = Array.from(e.results).map(r => r[0].transcript).join('');
        if (transcriptYou) transcriptYou.textContent = '▷ YOU: ' + transcript.toUpperCase();
        if (e.results[0].isFinal && commandInput) commandInput.value = transcript;
    };

    recognition.onend = () => {
        isListening = false;
        if (speakBtn) speakBtn.classList.remove('mic-active');
        if (commandInput?.value.trim()) sendCommand();
        else setStatus('STANDBY');
    };

    recognition.onerror = e => {
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

if (speakBtn) speakBtn.addEventListener('click', toggleListening);

// ══════════════════════════════════════════════════════════
// THEME TOGGLE
// ══════════════════════════════════════════════════════════
let ironManMode = false;
const themeBtn = document.getElementById('theme-toggle');
if (themeBtn) {
    themeBtn.addEventListener('click', () => {
        ironManMode = !ironManMode;
        document.body.classList.toggle('iron-man', ironManMode);
        addLog(ironManMode ? '[ SYS ] IRON MAN PROTOCOL ACTIVE' : '[ SYS ] JARVIS PROTOCOL RESTORED');
    });
}

// ══════════════════════════════════════════════════════════
// AGENTIC TAB SWITCHER
// ══════════════════════════════════════════════════════════
function switchTab(btn, tabName) {
    document.querySelectorAll('.atab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.atab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    const tabEl = document.getElementById('tab-' + tabName);
    if (tabEl) tabEl.classList.add('active');
}

// ══════════════════════════════════════════════════════════
// DEADLINE MANAGER (frontend)
// ══════════════════════════════════════════════════════════
function addDeadline() {
    const title = document.getElementById('dl-title')?.value.trim();
    const dueDate = document.getElementById('dl-date')?.value;
    if (!title || !dueDate) return;

    const dl = { id: Date.now(), title, dueDate, created: new Date().toISOString() };
    deadlines.push(dl);
    localStorage.setItem('jarvis_deadlines', JSON.stringify(deadlines));

    // Send to backend too
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'command',
            text: `set deadline ${title} due ${dueDate}`
        }));
    }

    document.getElementById('dl-title').value = '';
    document.getElementById('dl-date').value = '';
    renderDeadlines();
    addLog(`[ DL ] DEADLINE ADDED: ${title}`);
}

function renderDeadlines() {
    const list = document.getElementById('deadline-list');
    if (!list) return;

    if (deadlines.length === 0) {
        list.innerHTML = '<div class="deadline-item empty">No active deadlines.</div>';
        return;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    list.innerHTML = deadlines
        .filter(dl => !dl.done)
        .sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate))
        .map(dl => {
            const due = new Date(dl.dueDate);
            due.setHours(0, 0, 0, 0);
            const daysLeft = Math.ceil((due - today) / 86400000);

            let urgClass = 'ok';
            let urgLabel = `${daysLeft}d LEFT`;
            if (daysLeft < 0) { urgClass = 'urgent'; urgLabel = `${Math.abs(daysLeft)}d OVERDUE`; }
            else if (daysLeft <= 1) { urgClass = 'urgent'; urgLabel = daysLeft === 0 ? 'TODAY' : 'TOMORROW'; }
            else if (daysLeft <= 3) { urgClass = 'warning'; urgLabel = `${daysLeft}d LEFT`; }

            return `
                <div class="deadline-item" id="dl-${dl.id}">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div class="dl-title">${dl.title.toUpperCase()}</div>
                        <div class="dl-days ${urgClass}">${urgLabel}</div>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:3px">
                        <div class="dl-due">${dl.dueDate}</div>
                        <button class="hud-btn" style="padding:2px 6px;font-size:0.45rem"
                            onclick="completeDeadline(${dl.id})">✓ DONE</button>
                    </div>
                </div>`;
        }).join('');
}

function completeDeadline(id) {
    deadlines = deadlines.map(dl => dl.id === id ? { ...dl, done: true } : dl);
    localStorage.setItem('jarvis_deadlines', JSON.stringify(deadlines));
    renderDeadlines();
    addLog('[ DL ] DEADLINE COMPLETED');
}

renderDeadlines();

// Deadline urgency check every minute
setInterval(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    deadlines.filter(dl => !dl.done).forEach(dl => {
        const due = new Date(dl.dueDate);
        const daysLeft = Math.ceil((due - today) / 86400000);
        if (daysLeft === 1) {
            showJarvisResponse(`Thambii, ${dl.title} is due tomorrow. Make sure you are on track.`, 'AGENTIC');
        }
    });
}, 60000);

// ══════════════════════════════════════════════════════════
// MEMORY PANEL
// ══════════════════════════════════════════════════════════
function requestMemory() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'memory_request' }));
    }
}

function updateMemoryPanel(summary) {
    const memLog = document.getElementById('memory-log');
    if (!memLog) return;

    if (typeof summary === 'object') {
        // Stats object
        if (summary.total_tasks !== undefined) setMemStat('ms-tasks', summary.total_tasks);
        if (summary.total_conversations !== undefined) setMemStat('ms-convs', summary.total_conversations);
        if (summary.active_deadlines !== undefined) setMemStat('ms-reminders', summary.active_deadlines);
        if (summary.vector_memories !== undefined) setMemStat('ms-vectors', summary.vector_memories);
    } else if (typeof summary === 'string') {
        // Text log
        const lines = summary.split('\n').slice(-8);
        memLog.innerHTML = lines.map(l =>
            `<div class="log-item">${l}</div>`
        ).join('');
    }
}

function setMemStat(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

// ══════════════════════════════════════════════════════════
// AGENTIC EVENTS
// ══════════════════════════════════════════════════════════
function handleAgenticEvent(data) {
    if (data.event === 'morning_brief') {
        showJarvisResponse(data.text, 'AGENTIC');
        addLog('[ AGENTIC ] MORNING BRIEF DELIVERED');
    } else if (data.event === 'deadline_alert') {
        showJarvisResponse(data.text, 'AGENTIC');
        addLog('[ AGENTIC ] DEADLINE ALERT');
    } else if (data.event === 'proactive_error') {
        showJarvisResponse(data.text, 'VISION');
        addLog('[ VISION ] ERROR DETECTED ON SCREEN');
    }
}

// ── Morning brief shortcut — opens dedicated brief page ──
function sendMorningBrief() {
    // Open the brief page in a new tab
    window.open('brief.html', '_blank');
    // Also request brief from backend
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'command', text: 'morning brief' }));
    }
    addLog('[ AGENTIC ] BRIEF PAGE OPENED');
}

// ══════════════════════════════════════════════════════════
// MEMORY STAT DISPLAY (simulated until backend provides)
// ══════════════════════════════════════════════════════════
function updateMemStatsLocal() {
    const tasksEl = document.getElementById('ms-tasks');
    const convsEl = document.getElementById('ms-convs');
    const vecsEl = document.getElementById('ms-vectors');
    const reminEl = document.getElementById('ms-reminders');

    // Pull from localStorage deadlines as a proxy
    if (reminEl) reminEl.textContent = deadlines.filter(d => !d.done).length;
    if (tasksEl) tasksEl.textContent = '—';
    if (convsEl) convsEl.textContent = '—';
    if (vecsEl) vecsEl.textContent = '—';
}
updateMemStatsLocal();

// ══════════════════════════════════════════════════════════
// BOOT SEQUENCE LOGS
// ══════════════════════════════════════════════════════════
const bootLogs = [
    '[ SYS ] JARVIS v2.0 HUD INITIALIZED',
    '[ BRAIN ] DUAL-BRAIN ARCHITECTURE LOADED',
    '[ ROUTER ] SEMANTIC ROUTER READY',
    '[ MEM ] SQLite MEMORY ONLINE',
    '[ AGENTIC ] MORNING BRIEF SCHEDULED 07:30',
    '[ NET ] CONNECTING TO BACKEND...',
];
bootLogs.forEach((msg, i) => setTimeout(() => addLog(msg), 400 + i * 300));

// ══════════════════════════════════════════════════════════
// CONVERSATION STORAGE ENGINE
// Separate: GENERAL + PERSONAL (auto-segregated by emotion)
// Emotion detected by Jarvis only — never by user
// ══════════════════════════════════════════════════════════

const EMOTION_KEYWORDS = {
    happy: ['happy', 'great', 'amazing', 'love it', 'excited', 'proud', 'joy', 'wonderful', 'good news', 'glad', 'thrilled', 'awesome', 'yay', 'best day'],
    sad: ['sad', 'cry', 'miss', 'lonely', 'heartbroken', 'depressed', 'down', 'upset', 'grief', 'lost', 'empty', 'hopeless', 'tears', 'crying'],
    angry: ['angry', 'frustrated', 'furious', 'hate', 'rage', 'mad', 'annoyed', 'irritated', 'fed up', 'sick of', 'disgusted'],
    anxious: ['anxious', 'worried', 'scared', 'nervous', 'fear', 'stress', 'stressed', 'panic', 'uneasy', 'dread', 'terrified'],
    motivated: ["motivated", "ready", "let's go", 'determined', 'focused', 'productive', 'pumped', 'energised', 'inspired', 'grind'],
    betrayal: ['betrayed', 'backstab', 'lied', 'cheated', 'broke my trust', 'used me', 'fake', 'two-faced', 'manipulated'],
    love: ['love', 'crush', 'like someone', 'heart', 'relationship', 'boyfriend', 'girlfriend', 'date', 'miss him', 'miss her', 'feelings for'],
};

function detectEmotion(text) {
    const lower = text.toLowerCase();
    for (const [emotion, keywords] of Object.entries(EMOTION_KEYWORDS)) {
        if (keywords.some(kw => lower.includes(kw))) return emotion;
    }
    return 'neutral';
}

const STORAGE_GENERAL = 'jarvis_convos_general';
const STORAGE_PERSONAL = 'jarvis_convos_personal';

function loadConvos(key) {
    try { return JSON.parse(localStorage.getItem(key) || '[]'); } catch { return []; }
}
function saveConvos(key, data) {
    localStorage.setItem(key, JSON.stringify(data.slice(-500)));
}

function storeConversation(userText, jarvisText, brain) {
    const timestamp = new Date().toISOString();
    const entry = {
        id: Date.now(), timestamp, userText, jarvisText, brain,
        emotion: brain === 'PERSONAL' ? detectEmotion(userText) : 'general',
    };
    if (brain === 'PERSONAL') {
        const data = loadConvos(STORAGE_PERSONAL);
        data.push(entry); saveConvos(STORAGE_PERSONAL, data);
    } else {
        const data = loadConvos(STORAGE_GENERAL);
        data.push(entry); saveConvos(STORAGE_GENERAL, data);
    }
    if (document.getElementById('memory-modal')?.classList.contains('open')) refreshMemoryCounts();
    // Update memory stats
    const allCount = loadConvos(STORAGE_GENERAL).length + loadConvos(STORAGE_PERSONAL).length;
    const convsEl = document.getElementById('ms-convs');
    if (convsEl) convsEl.textContent = allCount;
}

// ══════════════════════════════════════════════════════════
// MEMORY BROWSER
// ══════════════════════════════════════════════════════════
let currentFilter = 'all';
let selectedConvoId = null;

function openMemoryBrowser() {
    document.getElementById('memory-modal').classList.add('open');
    refreshMemoryCounts();
    filterByEmotion('all');
    addLog('[ MEM ] MEMORY BROWSER OPENED');
}
function closeMemoryBrowser() {
    document.getElementById('memory-modal').classList.remove('open');
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMemoryBrowser(); });

function getAllConvos() {
    return [
        ...loadConvos(STORAGE_GENERAL).map(c => ({ ...c, brain: c.brain || 'GENERAL' })),
        ...loadConvos(STORAGE_PERSONAL).map(c => ({ ...c, brain: c.brain || 'PERSONAL' })),
    ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

function refreshMemoryCounts() {
    const all = getAllConvos();
    const general = all.filter(c => c.brain !== 'PERSONAL');
    const counts = { all: all.length, general: general.length };
    for (const e of ['happy', 'sad', 'angry', 'anxious', 'motivated', 'betrayal', 'love', 'neutral']) {
        counts[e] = all.filter(c => c.brain === 'PERSONAL' && c.emotion === e).length;
    }
    for (const [key, val] of Object.entries(counts)) {
        const el = document.getElementById(`count-${key}`);
        if (el) el.textContent = val;
    }
}

function filterByEmotion(filter) {
    currentFilter = filter; selectedConvoId = null;
    document.querySelectorAll('.emotion-folder').forEach(el => el.classList.remove('active'));
    document.getElementById(`ef-${filter}`)?.classList.add('active');
    const titles = { all: 'ALL CONVERSATIONS', general: 'GENERAL CONVERSATIONS', happy: 'HAPPY MOMENTS', sad: 'SAD MOMENTS', angry: 'ANGRY MOMENTS', anxious: 'ANXIOUS MOMENTS', motivated: 'MOTIVATED MOMENTS', betrayal: 'BETRAYAL', love: 'LOVE & RELATIONSHIPS', neutral: 'NEUTRAL CHATS' };
    const titleEl = document.getElementById('conv-list-title');
    if (titleEl) titleEl.textContent = titles[filter] || filter.toUpperCase();
    renderConvCards(getFilteredConvos(filter));
    renderDetailEmpty();
}

function getFilteredConvos(filter) {
    const all = getAllConvos();
    if (filter === 'all') return all;
    if (filter === 'general') return all.filter(c => c.brain !== 'PERSONAL');
    return all.filter(c => c.brain === 'PERSONAL' && c.emotion === filter);
}

const EMOTION_COLORS = { happy: '#ffd700', sad: '#6bb5ff', angry: '#ff4d4d', anxious: '#ff9d00', motivated: '#00ff88', betrayal: '#c084fc', love: '#f472b6', neutral: 'rgba(0,210,255,0.5)', general: 'var(--primary)' };
const EMOTION_ICONS = { happy: '😊', sad: '💧', angry: '🔥', anxious: '⚡', motivated: '🚀', betrayal: '🗡', love: '💜', neutral: '◎', general: '💡' };

function renderConvCards(convos) {
    const container = document.getElementById('conv-cards-container');
    if (!container) return;
    if (!convos.length) {
        container.innerHTML = `<div style="opacity:0.4;text-align:center;padding:30px;font-family:var(--font-mono);font-size:0.85rem;">No conversations in this folder.</div>`;
        return;
    }
    container.innerHTML = convos.map(c => {
        const date = new Date(c.timestamp).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
        const time = new Date(c.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
        const preview = (c.userText || '').substring(0, 65) + ((c.userText || '').length > 65 ? '…' : '');
        const emotion = c.emotion || (c.brain === 'PERSONAL' ? 'neutral' : 'general');
        const color = EMOTION_COLORS[emotion] || 'var(--primary)';
        const icon = EMOTION_ICONS[emotion] || '◎';
        return `<div class="conv-card" onclick="showConvDetail(${c.id})" data-id="${c.id}">
            <div class="cc-date">${date} · ${time}</div>
            <div class="cc-preview">${preview}</div>
            <div class="cc-emotion" style="color:${color};border:1px solid ${color}40;background:${color}12;">${icon} ${emotion.toUpperCase()}</div>
        </div>`;
    }).join('');
}

function showConvDetail(id) {
    selectedConvoId = id;
    const conv = getAllConvos().find(c => c.id === id);
    if (!conv) return;
    document.querySelectorAll('.conv-card').forEach(el => el.classList.remove('active'));
    document.querySelector(`[data-id="${id}"]`)?.classList.add('active');
    const detail = document.getElementById('conv-detail');
    if (!detail) return;
    const date = new Date(conv.timestamp).toLocaleString('en-IN');
    const emotion = conv.emotion || 'general';
    const brain = conv.brain || 'GENERAL';
    const color = EMOTION_COLORS[emotion] || 'var(--primary)';
    detail.innerHTML = `
        <div style="margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;">
            <div style="font-family:var(--font-mono);font-size:0.78rem;opacity:0.6;">${date}</div>
            <div style="display:flex;gap:10px;">
                <span style="font-family:var(--font-mono);font-size:0.72rem;padding:3px 10px;border:1px solid ${color}40;color:${color};background:${color}10;">${emotion.toUpperCase()}</span>
                <span style="font-family:var(--font-mono);font-size:0.72rem;padding:3px 10px;border:1px solid var(--border);color:var(--text-dim);">${brain} BRAIN</span>
            </div>
        </div>
        <div class="conv-message user"><div class="msg-role">▷ YOU</div><div class="msg-text">${conv.userText || ''}</div><div class="msg-time">${date}</div></div>
        <div class="conv-message jarvis"><div class="msg-role">◈ JARVIS</div><div class="msg-text">${conv.jarvisText || ''}</div><div class="msg-time">${brain} BRAIN · ${emotion}</div></div>`;
}

function renderDetailEmpty() {
    const detail = document.getElementById('conv-detail');
    if (detail) detail.innerHTML = '<div class="detail-empty">SELECT A CONVERSATION</div>';
}

// Memory search
const memSearchInput = document.getElementById('memory-search-input');
if (memSearchInput) {
    memSearchInput.addEventListener('input', e => {
        const query = e.target.value.toLowerCase().trim();
        if (!query) { filterByEmotion(currentFilter); return; }
        const results = getAllConvos().filter(c =>
            (c.userText || '').toLowerCase().includes(query) ||
            (c.jarvisText || '').toLowerCase().includes(query)
        );
        renderConvCards(results);
    });
}