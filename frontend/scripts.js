/* ===========================
   MemTracker Frontend (Vanilla JS)
   Mock-ready + Integration-ready
=========================== */

const CONFIG = {
    MOCK: true, // <- later set to false when backend endpoints are ready
    BASE_URL: "http://localhost:8000",
    ENDPOINTS: {
        upload: "/upload", // POST (multipart/form-data)
        chat: "/chat",     // POST (json)
        stream: (sessionId) => `/stream/${sessionId}` // GET (mjpeg/mp4/hls)
    },
    // If backend uses MJPEG stream, set STREAM_TYPE="mjpeg"
    // If backend returns mp4/hls playable by <video>, set STREAM_TYPE="video"
    STREAM_TYPE: "video"
};

const $ = (sel) => document.querySelector(sel);

const dropzone = $("#dropzone");
const fileInput = $("#fileInput");
const fileRow = $("#fileRow");
const fileName = $("#fileName");
const fileSub = $("#fileSub");
const btnClear = $("#btnClear");
const btnProcess = $("#btnProcess");
const btnPreview = $("#btnPreview");

const progressWrap = $("#progressWrap");
const progressText = $("#progressText");
const progressPct = $("#progressPct");
const progressFill = $("#progressFill");

const inlineAlert = $("#inlineAlert");
const inlineAlertText = $("#inlineAlertText");

const statusPill = $("#statusPill");
const sessionIdEl = $("#sessionId");
const streamStateEl = $("#streamState");
const lastEventEl = $("#lastEvent");

const videoPlayer = $("#videoPlayer");
const videoOverlay = $("#videoOverlay");
const overlayTitle = $("#overlayTitle");
const overlaySub = $("#overlaySub");
const spinner = $("#spinner");
const btnLoadDemo = $("#btnLoadDemo");
const btnFullscreen = $("#btnFullscreen");
const btnSnap = $("#btnSnap");

const chatBody = $("#chatBody");
const chatForm = $("#chatForm");
const chatText = $("#chatText");
const typing = $("#typing");
const btnClearChat = $("#btnClearChat");

const toastWrap = $("#toastWrap");

const btnTheme = $("#btnTheme");
const btnMock = $("#btnMock");
const mockLabel = $("#mockLabel");
const btnDocs = $("#btnDocs");
const modal = $("#modal");
const btnCloseModal = $("#btnCloseModal");
const btnExport = $("#btnExport");

const suggestions = $("#suggestions");

let selectedFile = null;
let currentSessionId = null;
let lastPreviewURL = null;

init();

function init() {
    // Restore theme
    const savedTheme = localStorage.getItem("theme") || "dark";
    setTheme(savedTheme);

    // Restore mock
    const savedMock = localStorage.getItem("mock");
    if (savedMock !== null) CONFIG.MOCK = savedMock === "true";
    refreshMockLabel();

    bindUploadUI();
    bindVideoUI();
    bindChatUI();
    bindTopbar();

    seedChat();

    toast("Ready", "Upload a video or load demo. Mock mode simulates backend.", "✅");
    setTimeline("upload");
}

function bindTopbar() {
    btnTheme.addEventListener("click", () => {
        const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
        setTheme(next);
    });

    btnMock.addEventListener("click", () => {
        CONFIG.MOCK = !CONFIG.MOCK;
        localStorage.setItem("mock", String(CONFIG.MOCK));
        refreshMockLabel();
        toast("Mode switched", CONFIG.MOCK ? "Mock mode is ON." : "Mock mode is OFF. Endpoints required.", "🧪");
    });

    btnDocs.addEventListener("click", () => modal.showModal());
    btnCloseModal.addEventListener("click", () => modal.close());
    modal.addEventListener("click", (e) => {
        const r = modal.getBoundingClientRect();
        const inDialog = (r.top <= e.clientY && e.clientY <= r.bottom && r.left <= e.clientX && e.clientX <= r.right);
        if (!inDialog) modal.close();
    });

    btnExport.addEventListener("click", (e) => {
        e.preventDefault();
        exportChat();
    });
}

function refreshMockLabel() {
    mockLabel.textContent = `Mock: ${CONFIG.MOCK ? "ON" : "OFF"}`;
}

function setTheme(theme) {
    document.documentElement.dataset.theme = theme === "light" ? "light" : "dark";
    localStorage.setItem("theme", document.documentElement.dataset.theme);
}

/* ===========================
   Upload + Process
=========================== */
function bindUploadUI() {
    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") fileInput.click();
    });

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        const file = e.dataTransfer?.files?.[0];
        if (file) onFileSelected(file);
    });

    fileInput.addEventListener("change", () => {
        const file = fileInput.files?.[0];
        if (file) onFileSelected(file);
    });

    btnClear.addEventListener("click", clearFile);

    btnPreview.addEventListener("click", () => {
        if (!selectedFile) return;
        previewVideo(selectedFile);
        toast("Preview", "Showing local preview.", "👁️");
        setTimeline("upload");
    });

    btnProcess.addEventListener("click", async () => {
        if (!selectedFile) return;
        hideInlineError();
        await startProcessingFlow(selectedFile);
    });

    btnLoadDemo.addEventListener("click", () => loadDemoVideo());

    suggestions.addEventListener("click", (e) => {
        const btn = e.target.closest(".sug");
        if (!btn) return;
        chatText.value = btn.textContent.trim();
        chatText.focus();
    });
}

function onFileSelected(file) {
    if (!file.type.startsWith("video/")) {
        showInlineError("Please upload a valid video file.");
        toast("Invalid file", "Only video files are allowed.", "⚠️");
        return;
    }

    selectedFile = file;

    fileRow.hidden = false;
    fileName.textContent = file.name;
    fileSub.textContent = `${formatBytes(file.size)} • ${file.type || "video"}`;

    btnPreview.disabled = false;
    btnProcess.disabled = false;

    setStatus("Ready");
    setEvent("Video selected");
    setTimeline("upload");
    overlayTitle.textContent = "Ready to preview or process";
    overlaySub.textContent = "Click Preview to see local video, or Process to start streaming results.";
    spinner.hidden = true;
    videoOverlay.style.display = "flex";

    toast("Video selected", "You can preview or process now.", "🎬");
}

function clearFile() {
    selectedFile = null;
    fileInput.value = "";
    fileRow.hidden = true;
    btnPreview.disabled = true;
    btnProcess.disabled = true;

    setStatus("Idle");
    setEvent("Cleared file");
    currentSessionId = null;
    sessionIdEl.textContent = "—";
    streamStateEl.textContent = "Not started";
    setTimeline("upload");

    stopVideo();
    showVideoOverlay("No video loaded", "Upload a video to preview, then process to stream results.", false);

    toast("Cleared", "File removed.", "🧹");
}

async function startProcessingFlow(file) {
    setStatus("Uploading");
    setEvent("Upload started");
    setTimeline("upload");
    showProgress("Uploading…", 0);
    showVideoOverlay("Uploading", "Sending video to backend…", true);

    try {
        // 1) Upload (or mock)
        const uploadResult = CONFIG.MOCK ? await mockUpload(file) : await realUpload(file);

        // 2) Use session/video ID returned
        currentSessionId = uploadResult.session_id || uploadResult.video_id || uploadResult.id || randomId();
        sessionIdEl.textContent = currentSessionId;

        setStatus("Processing");
        setEvent("Processing started");
        setTimeline("process");
        showProgress("Processing…", 0);
        showVideoOverlay("Processing", "Running detection, tracking, and activity recognition…", true);

        // 3) Simulate processing progress (or poll)
        if (CONFIG.MOCK) {
            await mockProcessingProgress();
        } else {
            // If your backend returns progress endpoints, you can poll here.
            // For now we just show an indeterminate-like animation using increments.
            await fakeProgressRamp("Processing…", 6000);
        }

        // 4) Start Stream
        setStatus("Streaming");
        setEvent("Streaming started");
        setTimeline("stream");
        streamStateEl.textContent = "Live";

        const streamURL = uploadResult.stream_url
            || (CONFIG.BASE_URL + CONFIG.ENDPOINTS.stream(currentSessionId));

        await startStream(streamURL);

        hideProgress();
        setStatus("Ready");
        setEvent("Ready for chat");
        setTimeline("chat");

        toast("Stream ready", "Processed stream is now playing.", "✅");
        systemMessage("Stream is ready. Ask me questions about the video.");
    } catch (err) {
        hideProgress();
        setStatus("Error");
        setEvent("Failed");
        showInlineError(err?.message || "Something went wrong.");
        showVideoOverlay("Error", "Could not process video. Check connection or endpoint configuration.", false);
        toast("Error", err?.message || "Processing failed.", "❌");
    }
}

/* ===========================
   Video: preview + stream
=========================== */
function bindVideoUI() {
    btnFullscreen.addEventListener("click", () => {
        if (!videoPlayer.src) return;
        if (videoPlayer.requestFullscreen) videoPlayer.requestFullscreen();
    });

    btnSnap.addEventListener("click", () => snapFrame());

    videoPlayer.addEventListener("play", () => {
        videoOverlay.style.display = "none";
    });
}

function previewVideo(file) {
    if (lastPreviewURL) URL.revokeObjectURL(lastPreviewURL);
    lastPreviewURL = URL.createObjectURL(file);
    videoPlayer.src = lastPreviewURL;
    videoPlayer.play().catch(() => { });
    btnFullscreen.disabled = false;
    btnSnap.disabled = false;
    streamStateEl.textContent = "Previewing";
    setEvent("Preview playing");
    showVideoOverlay("Preview loaded", "Press play if it doesn't auto-start.", false);
    videoOverlay.style.display = "none";
}

async function startStream(streamURL) {
    // For MJPEG streams, the usual approach is <img src="...">.
    // For MP4/HLS, <video src="..."> works depending on backend.
    // We keep it simple and use <video> by default.

    showVideoOverlay("Starting stream", "Connecting to processed video…", true);

    if (CONFIG.STREAM_TYPE === "mjpeg") {
        // Replace the video tag with an img dynamically (safe, reversible)
        // But to keep markup simple, we will just show a notice for now.
        // If your backend uses MJPEG, tell me and I’ll switch implementation in 2 mins.
        throw new Error("STREAM_TYPE is set to 'mjpeg' but UI uses <video>. Tell me your stream format and I’ll adapt it.");
    }

    videoPlayer.src = streamURL;
    btnFullscreen.disabled = false;
    btnSnap.disabled = false;

    try {
        await videoPlayer.play();
    } catch {
        // Autoplay might be blocked; show overlay with hint
        showVideoOverlay("Stream connected", "Press play to start the stream (autoplay may be blocked).", false);
    }

    videoOverlay.style.display = "none";
}

function stopVideo() {
    videoPlayer.pause();
    videoPlayer.removeAttribute("src");
    videoPlayer.load();
    btnFullscreen.disabled = true;
    btnSnap.disabled = true;
}

function showVideoOverlay(title, sub, loading) {
    overlayTitle.textContent = title;
    overlaySub.textContent = sub;
    spinner.hidden = !loading;
    videoOverlay.style.display = "flex";
}

function loadDemoVideo() {
    // A tiny “demo” created by using a blank video is not reliable in browsers.
    // Instead, we simulate: show a helpful overlay and let user upload a real file.
    toast("Demo", "For best results, upload any short video from your laptop.", "✨");
    showVideoOverlay("Upload any short video", "Demo mode works best with a real file from your device.", false);
}

/* Screenshot frame (client-side) */
function snapFrame() {
    if (!videoPlayer.videoWidth) {
        toast("Not ready", "Play the video first, then take a snapshot.", "⚠️");
        return;
    }
    const c = document.createElement("canvas");
    c.width = videoPlayer.videoWidth;
    c.height = videoPlayer.videoHeight;
    const ctx = c.getContext("2d");
    ctx.drawImage(videoPlayer, 0, 0, c.width, c.height);

    const a = document.createElement("a");
    a.href = c.toDataURL("image/png");
    a.download = `memtracker_snapshot_${Date.now()}.png`;
    a.click();
    toast("Saved", "Snapshot downloaded.", "📸");
}

/* ===========================
   Chat
=========================== */
function bindChatUI() {
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = chatText.value.trim();
        if (!text) return;

        addMessage("user", text);
        chatText.value = "";

        if (!currentSessionId) {
            typingOn(true);
            await sleep(600);
            typingOn(false);
            addMessage("bot", "Upload and process a video first so I can answer with context.");
            toast("No session", "Process a video before asking questions.", "⚠️");
            return;
        }

        typingOn(true);

        try {
            const reply = CONFIG.MOCK
                ? await mockChat(text, currentSessionId)
                : await realChat(text, currentSessionId);

            typingOn(false);
            addMessage("bot", reply.answer || reply.response || String(reply));
            setTimeline("chat");
        } catch (err) {
            typingOn(false);
            addMessage("bot", "I couldn’t reach the chat service. Please try again.");
            toast("Chat error", err?.message || "Failed to fetch chat response.", "❌");
        }
    });

    btnClearChat.addEventListener("click", () => {
        chatBody.innerHTML = "";
        seedChat();
        toast("Cleared", "Chat reset.", "🧹");
    });
}

function seedChat() {
    systemMessage("Hi! I’m MemTracker. Upload a video, process it, then ask questions like: “Who took the laptop at 3 PM?”");
}

function systemMessage(text) {
    addMessage("bot", text, { badge: "system" });
}

function addMessage(role, text, opts = {}) {
    const msg = document.createElement("div");
    msg.className = `msg ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    const meta = document.createElement("div");
    meta.className = "meta";

    const time = new Date();
    const hh = String(time.getHours()).padStart(2, "0");
    const mm = String(time.getMinutes()).padStart(2, "0");
    meta.innerHTML = `<span class="mono">${hh}:${mm}</span>`;

    if (opts.badge) {
        const b = document.createElement("span");
        b.className = "badge";
        b.textContent = opts.badge;
        meta.appendChild(b);
    }

    const wrap = document.createElement("div");
    wrap.appendChild(bubble);
    wrap.appendChild(meta);

    msg.appendChild(wrap);
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function typingOn(on) {
    typing.hidden = !on;
    if (on) chatBody.scrollTop = chatBody.scrollHeight;
}

function exportChat() {
    const lines = [];
    chatBody.querySelectorAll(".msg").forEach((m) => {
        const role = m.classList.contains("user") ? "You" : "MemTracker";
        const text = m.querySelector(".bubble")?.textContent || "";
        const time = m.querySelector(".meta .mono")?.textContent || "";
        lines.push(`[${time}] ${role}: ${text}`);
    });

    const blob = new Blob([lines.join("\n\n")], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `memtracker_chat_${Date.now()}.txt`;
    a.click();

    toast("Exported", "Chat transcript downloaded.", "⬇️");
}

/* ===========================
   Integration: real API calls
=========================== */
async function realUpload(file) {
    const url = CONFIG.BASE_URL + CONFIG.ENDPOINTS.upload;

    // Most FastAPI upload endpoints accept: FormData with a key like "file"
    // If backend uses a different key, change 'file' below.
    const form = new FormData();
    form.append("file", file);

    // fetch doesn't provide upload progress by default.
    // For real progress, we'd use XMLHttpRequest. For now: spinner + fake progress ramp.
    await fakeProgressRamp("Uploading…", 2500);

    const res = await fetch(url, {
        method: "POST",
        body: form
    });

    if (!res.ok) {
        const text = await safeReadText(res);
        throw new Error(`Upload failed (${res.status}). ${text}`);
    }

    // expected: { session_id: "...", stream_url: "..." } (example)
    return await res.json();
}

async function realChat(question, sessionId) {
    const url = CONFIG.BASE_URL + CONFIG.ENDPOINTS.chat;

    const payload = {
        session_id: sessionId, // adjust if backend expects "video_id" or something else
        question
    };

    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        const text = await safeReadText(res);
        throw new Error(`Chat failed (${res.status}). ${text}`);
    }

    return await res.json();
}

async function safeReadText(res) {
    try { return await res.text(); } catch { return ""; }
}

/* ===========================
   Mock (demo today)
=========================== */
async function mockUpload(file) {
    // Simulate upload progress
    for (let i = 0; i <= 100; i += 8) {
        showProgress("Uploading…", i);
        await sleep(80 + Math.random() * 80);
    }
    showProgress("Uploading…", 100);
    await sleep(250);

    // Pretend backend returns session + stream URL
    const id = randomId();
    return {
        session_id: id,
        stream_url: lastPreviewURL ? lastPreviewURL : "" // reuse preview as "stream"
    };
}

async function mockProcessingProgress() {
    for (let i = 0; i <= 100; i += 6) {
        showProgress("Processing…", i);
        await sleep(90 + Math.random() * 90);
    }
    showProgress("Processing…", 100);
    await sleep(300);
}

async function mockChat(question, sessionId) {
    await sleep(900 + Math.random() * 700);

    // Simple “smart” mock response style
    const q = question.toLowerCase();

    if (q.includes("summarize") || q.includes("summary")) {
        return { answer: "Mock summary: A person enters, interacts with objects, and leaves. (Replace with real AI summary later.)" };
    }
    if (q.includes("when") && (q.includes("enter") || q.includes("entered"))) {
        return { answer: "Mock: The person enters around 00:12 in the video. (Backend will provide exact timestamps.)" };
    }
    if (q.includes("laptop") || q.includes("phone")) {
        return { answer: "Mock: An object that looks like a laptop is handled around mid-video. (Replace with detection/tracking results.)" };
    }
    if (q.includes("who")) {
        return { answer: "Mock: Person A performs the action. (Real model will identify based on tracked entities.)" };
    }

    return { answer: `Mock answer for session ${sessionId}: I understood your question (“${question}”). Connect the real chat endpoint to get real answers.` };
}

/* ===========================
   UI helpers
=========================== */
function setStatus(text) {
    statusPill.textContent = text;

    // subtle coloring through emoji-like states (keeps design consistent)
    if (text.toLowerCase().includes("error")) statusPill.style.borderColor = "rgba(255,77,109,.35)";
    else if (text.toLowerCase().includes("stream")) statusPill.style.borderColor = "rgba(51,209,122,.35)";
    else if (text.toLowerCase().includes("process")) statusPill.style.borderColor = "rgba(255,176,32,.35)";
    else statusPill.style.borderColor = "";
}

function setEvent(text) {
    lastEventEl.textContent = text;
}

function showProgress(label, pct) {
    progressWrap.hidden = false;
    progressText.textContent = label;
    progressPct.textContent = `${pct}%`;
    progressFill.style.width = `${pct}%`;
}

function hideProgress() {
    progressWrap.hidden = true;
}

function showInlineError(msg) {
    inlineAlert.hidden = false;
    inlineAlertText.textContent = msg;
}

function hideInlineError() {
    inlineAlert.hidden = true;
}

function setTimeline(step) {
    document.querySelectorAll(".t-step").forEach((s) => s.classList.remove("active"));
    const el = document.querySelector(`.t-step[data-step="${step}"]`);
    if (el) el.classList.add("active");
}

function toast(title, message, icon = "ℹ️") {
    const t = document.createElement("div");
    t.className = "toast";
    t.innerHTML = `
    <div class="t-ic" aria-hidden="true">${icon}</div>
    <div>
      <div class="t-title">${escapeHtml(title)}</div>
      <div class="t-msg">${escapeHtml(message)}</div>
    </div>
    <button class="t-close" aria-label="Close toast">✕</button>
  `;
    t.querySelector(".t-close").addEventListener("click", () => t.remove());
    toastWrap.appendChild(t);
    setTimeout(() => { if (t.isConnected) t.remove(); }, 4200);
}

function escapeHtml(s) {
    return String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function randomId() {
    return Math.random().toString(16).slice(2, 10);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const val = bytes / Math.pow(k, i);
    return `${val.toFixed(val >= 100 || i === 0 ? 0 : 1)} ${sizes[i]}`;
}

async function fakeProgressRamp(label, msTotal) {
    // A smooth ramp to make UI feel alive when fetch has no progress
    const steps = 18;
    for (let i = 0; i <= steps; i++) {
        const pct = Math.min(95, Math.round((i / steps) * 95));
        showProgress(label, pct);
        await sleep(msTotal / steps);
    }
}