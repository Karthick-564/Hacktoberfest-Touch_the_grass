// Field Guide - Category-Agnostic Mobile App Engine

let appConfig = null;
let currentCategory = "birds";
let currentQuestionIndex = 0;
let answers = {};
let freeText = "";
let currentLang = "en"; // "en" | "ta"

// Elements
const homeView = document.getElementById("home-view");
const questionView = document.getElementById("question-view");
const summaryView = document.getElementById("summary-view");
const resultsView = document.getElementById("results-view");
const langToggleBtn = document.getElementById("lang-toggle-btn");
const micBtn = document.getElementById("mic-btn");
const micStatus = document.getElementById("mic-status");
const transcriptBox = document.getElementById("transcript-box");
const transcriptText = document.getElementById("transcript-text");
const narratorAudio = document.getElementById("narrator-audio");

let recognition = null;
let isRecording = false;
let currentTranscript = "";

// Register Service Worker for Offline Airplane Mode
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}

// Initialize Application
async function init() {
  try {
    const res = await fetch("/api/categories");
    appConfig = await res.json();
  } catch (e) {
    console.error("Failed to load categories config:", e);
  }

  setupEventListeners();
  loadStats();
  renderHomeScreen();
}

window.setPreset = function(text) {
  const spokenInput = document.getElementById("spoken-input");
  if (spokenInput) {
    spokenInput.value = text;
    spokenInput.focus();
    micStatus.textContent = "Example loaded! Tap Match Observation below.";
  }
};

let audioContext = null;
let analyser = null;
let micStream = null;
let animFrameId = null;

function stopVolumeMeter() {
  if (animFrameId) cancelAnimationFrame(animFrameId);
  if (micStream) {
    micStream.getTracks().forEach((t) => t.stop());
    micStream = null;
  }
  if (audioContext && audioContext.state !== "closed") {
    audioContext.close().catch(() => {});
  }
  const volumeMeterBox = document.getElementById("volume-meter-box");
  if (volumeMeterBox) volumeMeterBox.style.display = "none";
}

let mediaRecorder = null;
let audioChunks = [];
let recordedMimeType = "audio/webm";

async function startVoiceRecording() {
  const spokenInput = document.getElementById("spoken-input");
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    micStream = stream;
    audioChunks = [];

    // Detect browser supported audio mime type
    if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
      recordedMimeType = "audio/webm;codecs=opus";
    } else if (MediaRecorder.isTypeSupported("audio/webm")) {
      recordedMimeType = "audio/webm";
    } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
      recordedMimeType = "audio/mp4";
    } else if (MediaRecorder.isTypeSupported("audio/ogg")) {
      recordedMimeType = "audio/ogg";
    } else {
      recordedMimeType = "";
    }

    const options = recordedMimeType ? { mimeType: recordedMimeType } : {};
    mediaRecorder = new MediaRecorder(stream, options);

    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      stopVolumeMeter();
      micBtn.classList.remove("listening");
      isRecording = false;

      const blobType = recordedMimeType || "audio/webm";
      const audioBlob = new Blob(audioChunks, { type: blobType });
      if (audioBlob.size < 400) {
        micStatus.textContent = "Recording too short. Speak clearly and tap red mic when done.";
        return;
      }

      micStatus.textContent = "⏳ Transcribing with ElevenLabs AI...";
      try {
        const res = await fetch("/api/transcribe", {
          method: "POST",
          headers: { "Content-Type": blobType },
          body: audioBlob
        });
        const data = await res.json();
        if (data.text && data.text.trim()) {
          const transcribed = data.text.trim();
          if (spokenInput) spokenInput.value = transcribed;
          micStatus.textContent = "Transcribed: \"" + transcribed + "\"";
          // Automatically trigger matching
          submitSpokenObservation(transcribed);
        } else {
          micStatus.textContent = "No words detected. Try speaking again or pick an example below.";
        }
      } catch (err) {
        console.error("Transcription error:", err);
        micStatus.textContent = "Transcription error. You can type or pick an example below.";
      }
    };

    mediaRecorder.start(250);
    isRecording = true;
    micBtn.classList.add("listening");
    micStatus.textContent = "🎙️ Recording... Speak now! Tap red mic when finished.";
    startVolumeMeterWithStream(stream);

  } catch (err) {
    console.error("Microphone access error:", err);
    micStatus.textContent = "Microphone access blocked. Click the lock/camera icon in URL bar to allow!";
  }
}

function stopVoiceRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
}

function startVolumeMeterWithStream(stream) {
  try {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(stream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    const volumeMeterBox = document.getElementById("volume-meter-box");
    const volumeFill = document.getElementById("volume-fill");
    if (volumeMeterBox) volumeMeterBox.style.display = "block";

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    function checkVolume() {
      if (!isRecording) return;
      analyser.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
      const avg = sum / dataArray.length;
      const pct = Math.min(100, Math.round((avg / 128) * 100));
      if (volumeFill) {
        volumeFill.style.width = pct + "%";
        if (pct > 12) {
          micStatus.textContent = "🎙️ Recording voice (" + pct + "% volume)... Tap red mic when done.";
        }
      }
      animFrameId = requestAnimationFrame(checkVolume);
    }
    checkVolume();
  } catch (e) {
    console.log("Audio meter notice:", e);
  }
}

function setupEventListeners() {
  langToggleBtn.addEventListener("click", () => {
    currentLang = currentLang === "en" ? "ta" : "en";
    langToggleBtn.textContent = currentLang === "en" ? "தமிழ்" : "English";
    refreshCurrentScreen();
  });

  const spokenInput = document.getElementById("spoken-input");

  if (micBtn) {
    micBtn.addEventListener("click", () => {
      if (isRecording) {
        stopVoiceRecording();
      } else {
        startVoiceRecording();
      }
    });
  }


  const voiceMatchBtn = document.getElementById("voice-match-btn");
  if (voiceMatchBtn) {
    voiceMatchBtn.addEventListener("click", () => {
      const text = spokenInput ? spokenInput.value.trim() : currentTranscript.trim();
      if (text) {
        submitSpokenObservation(text);
      } else {
        alert("Please speak or enter what you see (or tap one of the examples below)");
      }
    });
  }

  document.getElementById("start-observation-btn").addEventListener("click", startObservation);
  document.getElementById("skip-btn").addEventListener("click", skipQuestion);
  document.getElementById("next-btn").addEventListener("click", nextQuestion);
  document.getElementById("submit-matches-btn").addEventListener("click", submitObservation);
  document.getElementById("new-observation-btn").addEventListener("click", resetToHome);
  document.getElementById("home-link").addEventListener("click", resetToHome);
}

// Submit Spoken Observation directly to /api/match
async function submitSpokenObservation(spokenText) {
  const matchBtn = document.getElementById("voice-match-btn");
  if (matchBtn) {
    matchBtn.disabled = true;
    matchBtn.textContent = "Analyzing spoken observation...";
  }

  const payload = {
    category: currentCategory,
    answers: { spoken_text: spokenText },
    free_text: spokenText
  };

  try {
    const res = await fetch("/api/match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const matchData = await res.json();
    renderResultsScreen(matchData);
  } catch (e) {
    console.error("Match error:", e);
  } finally {
    if (matchBtn) {
      matchBtn.disabled = false;
      matchBtn.textContent = "Match Spoken Observation →";
    }
  }
}


// Load Collection Stats for Selected Category
async function loadStats() {
  try {
    const res = await fetch(`/api/stats?category=${currentCategory}`);
    const data = await res.json();
    const statText = currentLang === "en"
      ? `${data.unlocked_species} of ${data.total_species} ${data.region_name} ${currentCategory}`
      : `${data.total_species} இல் ${data.unlocked_species} ${currentCategory === 'birds' ? 'பறவைகள்' : 'மரங்கள்'} கண்டறியப்பட்டது`;
    document.getElementById("stats-display").textContent = statText;
  } catch (e) {
    document.getElementById("stats-display").textContent = "Field pack loaded";
  }
}

// Render Home Category Selector
function renderHomeScreen() {
  if (!appConfig) return;
  const grid = document.getElementById("category-grid");
  grid.innerHTML = "";

  appConfig.categories.forEach((cat) => {
    const card = document.createElement("div");
    card.className = `category-card ${cat.id === currentCategory ? "selected" : ""}`;
    card.innerHTML = `
      <div class="category-icon">${cat.emoji}</div>
      <div class="category-name">${currentLang === "en" ? cat.name_en : cat.name_ta}</div>
      <div class="category-name-ta">${currentLang === "en" ? cat.name_ta : cat.name_en}</div>
    `;
    card.addEventListener("click", () => {
      currentCategory = cat.id;
      document.querySelectorAll(".category-card").forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      loadStats();
    });
    grid.appendChild(card);
  });
}

function startObservation() {
  answers = {};
  freeText = "";
  currentQuestionIndex = 0;
  showView("question-view");
  renderCurrentQuestion();
}

function getCategoryConfig() {
  return appConfig?.categories?.find((c) => c.id === currentCategory);
}

// Render Question Screen
function renderCurrentQuestion() {
  const catConfig = getCategoryConfig();
  if (!catConfig || !catConfig.questions[currentQuestionIndex]) {
    renderSummaryScreen();
    return;
  }

  const q = catConfig.questions[currentQuestionIndex];
  const totalQ = catConfig.questions.length;

  // Progress Bar
  const pct = ((currentQuestionIndex + 1) / totalQ) * 100;
  document.getElementById("progress-fill").style.width = `${pct}%`;

  document.getElementById("step-counter").textContent = currentLang === "en"
    ? `Question ${currentQuestionIndex + 1} of ${totalQ}`
    : `கேள்வி ${currentQuestionIndex + 1} / ${totalQ}`;

  // Trees Safety Banner
  const safetyBanner = document.getElementById("safety-banner");
  if (catConfig.safety_warning_en) {
    safetyBanner.style.display = "flex";
    safetyBanner.textContent = currentLang === "en" ? catConfig.safety_warning_en : catConfig.safety_warning_ta;
  } else {
    safetyBanner.style.display = "none";
  }

  // Prompts
  document.getElementById("question-prompt").textContent = currentLang === "en" ? q.prompt_en : q.prompt_ta;
  document.getElementById("question-prompt-sub").textContent = currentLang === "en" ? q.prompt_ta : q.prompt_en;

  const container = document.getElementById("options-container");
  container.innerHTML = "";

  // Render Swatches vs Options
  if (q.type === "multi" && q.options[0]?.swatch) {
    const grid = document.createElement("div");
    grid.className = "color-swatches-grid";
    q.options.forEach((opt) => {
      const card = document.createElement("div");
      const isSelected = Array.isArray(answers[q.id]) && answers[q.id].includes(opt.id);
      card.className = `swatch-card ${isSelected ? "selected" : ""}`;
      card.innerHTML = `
        <div class="swatch-circle" style="background-color: ${opt.swatch};"></div>
        <div class="swatch-label-en">${currentLang === "en" ? opt.label_en : opt.label_ta}</div>
        <div class="swatch-label-ta">${currentLang === "en" ? opt.label_ta : opt.label_en}</div>
      `;
      card.addEventListener("click", () => {
        if (!Array.isArray(answers[q.id])) answers[q.id] = [];
        if (answers[q.id].includes(opt.id)) {
          answers[q.id] = answers[q.id].filter((x) => x !== opt.id);
          card.classList.remove("selected");
        } else {
          answers[q.id].push(opt.id);
          card.classList.add("selected");
        }
      });
      grid.appendChild(card);
    });
    container.appendChild(grid);
  } else {
    const list = document.createElement("div");
    list.className = "options-list";
    q.options.forEach((opt) => {
      const isSelected = answers[q.id] === opt.id;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `option-btn ${isSelected ? "selected" : ""}`;
      btn.innerHTML = `
        <div class="option-content-left">
          ${opt.emoji ? `<span class="option-emoji">${opt.emoji}</span>` : ""}
          <div class="option-labels">
            <span class="option-label-en">${currentLang === "en" ? opt.label_en : opt.label_ta}</span>
            <span class="option-label-ta">${currentLang === "en" ? opt.label_ta : opt.label_en}</span>
          </div>
        </div>
        <div class="check-indicator">${isSelected ? "✓" : ""}</div>
      `;
      btn.addEventListener("click", () => {
        answers[q.id] = opt.id;
        // Fast tap advance for single selection after brief visual confirmation
        btn.classList.add("selected");
        btn.querySelector(".check-indicator").textContent = "✓";
        setTimeout(() => nextQuestion(), 160);
      });
      list.appendChild(btn);
    });
    container.appendChild(list);
  }

  // Free Text input for sounds or notes
  const freeTextBox = document.getElementById("free-text-section");
  if (q.has_free_text) {
    freeTextBox.style.display = "block";
    document.getElementById("free-text-title").textContent = currentLang === "en"
      ? q.free_text_prompt_en
      : q.free_text_prompt_ta;
    const input = document.getElementById("free-text-input");
    input.placeholder = currentLang === "en" ? q.free_text_placeholder_en : q.free_text_placeholder_ta;
    input.value = freeText;
    input.oninput = (e) => (freeText = e.target.value);
  } else {
    freeTextBox.style.display = "none";
  }
}

function skipQuestion() {
  const catConfig = getCategoryConfig();
  const q = catConfig.questions[currentQuestionIndex];
  if (!answers[q.id]) answers[q.id] = null;
  nextQuestion();
}

function nextQuestion() {
  const catConfig = getCategoryConfig();
  currentQuestionIndex++;
  if (currentQuestionIndex < catConfig.questions.length) {
    renderCurrentQuestion();
  } else {
    renderSummaryScreen();
  }
}

// Render Summary Screen
function renderSummaryScreen() {
  showView("summary-view");
  const catConfig = getCategoryConfig();
  const list = document.getElementById("summary-items");
  list.innerHTML = "";

  catConfig.questions.forEach((q) => {
    const val = answers[q.id];
    let displayVal = currentLang === "en" ? "Skipped" : "தவிர்க்கப்பட்டது";

    if (val) {
      if (Array.isArray(val)) {
        displayVal = val.join(", ");
      } else {
        const opt = q.options.find((o) => o.id === val);
        displayVal = opt ? (currentLang === "en" ? opt.label_en : opt.label_ta) : val;
      }
    }

    const item = document.createElement("div");
    item.className = "summary-item";
    item.innerHTML = `
      <span class="summary-q">${currentLang === "en" ? q.prompt_en.slice(0, 30) : q.prompt_ta.slice(0, 30)}...</span>
      <span class="summary-a">${displayVal}</span>
    `;
    list.appendChild(item);
  });

  if (freeText.trim()) {
    const item = document.createElement("div");
    item.className = "summary-item";
    item.innerHTML = `
      <span class="summary-q">${currentLang === "en" ? "Sound / Call" : "குரல்"}</span>
      <span class="summary-a">"${freeText}"</span>
    `;
    list.appendChild(item);
  }
}

// Submit Observation Payload to /api/match
async function submitObservation() {
  const submitBtn = document.getElementById("submit-matches-btn");
  submitBtn.disabled = true;
  submitBtn.textContent = currentLang === "en" ? "Matching candidate species..." : "பொருத்தமானவற்றைத் தேடுகிறது...";

  const payload = {
    category: currentCategory,
    answers: answers,
    free_text: freeText
  };

  try {
    const res = await fetch("/api/match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const matchData = await res.json();
    renderResultsScreen(matchData);
  } catch (e) {
    console.error("Match error:", e);
    renderResultsScreen({
      status: "matched",
      candidates: []
    });
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = currentLang === "en" ? "Find Candidate Matches" : "பொருத்தங்களைக் காண்க";
  }
}

// Render Candidate Cards
function renderResultsScreen(data) {
  showView("results-view");
  const container = document.getElementById("candidates-container");
  container.innerHTML = "";

  // Auto-play ElevenLabs guide audio
  if (data.audio_url && narratorAudio) {
    narratorAudio.src = data.audio_url;
    narratorAudio.play().catch((err) => {
      console.log("Audio autoplay prevented by browser policy (tap to play):", err);
    });
  }

  const candidates = data.candidates || [];

  if (candidates.length === 0) {
    container.innerHTML = `
      <div class="hero-card">
        <p style="color: var(--text-muted); margin-bottom: 12px;">
          ${currentLang === "en" ? "No precise matches found. Try describing what you see again." : "துல்லியமான பொருத்தம் இல்லை. மீண்டும் குரலில் விவரிக்கவும்."}
        </p>
      </div>
    `;
    return;
  }

  // Display Extracted Words and Detected Traits
  if (data.extracted_traits) {
    const et = data.extracted_traits;
    const traitsCard = document.createElement("div");
    traitsCard.className = "voice-card";
    traitsCard.style.textAlign = "left";
    traitsCard.style.padding = "16px";
    traitsCard.style.marginBottom = "14px";
    traitsCard.innerHTML = `
      <div style="font-size: 0.78rem; font-weight: 700; color: var(--accent); text-transform: uppercase; margin-bottom: 6px;">
        🔍 EXTRACTED FIELD WORDS & TRAITS
      </div>
      <div style="font-size: 0.95rem; margin-bottom: 10px; color: var(--text-main);">
        <strong>Observed:</strong> "${et.raw_text}"
      </div>
      <div style="display: flex; flex-wrap: wrap; gap: 8px; font-size: 0.82rem;">
        <span class="badge" style="background: rgba(132, 204, 22, 0.2); color: #a3e635;">🎨 Colors: ${et.detected_colors.join(", ")}</span>
        <span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #60a5fa;">👑 Features: ${et.detected_features.join(", ")}</span>
        <span class="badge" style="background: rgba(168, 85, 247, 0.2); color: #c084fc;">🔑 Keywords: ${et.keywords.join(", ")}</span>
      </div>
    `;
    container.appendChild(traitsCard);
  }

  // Audio guide banner
  if (data.audio_url) {
    const audioBanner = document.createElement("div");
    audioBanner.className = "voice-card";
    audioBanner.style.padding = "14px";
    audioBanner.style.marginBottom = "14px";
    audioBanner.innerHTML = `
      <button type="button" class="start-btn" style="padding: 10px; font-size: 0.95rem;" onclick="document.getElementById('narrator-audio').play()">
        🔊 Replay Naturalist Guide Voice
      </button>
    `;
    container.appendChild(audioBanner);
  }

  candidates.forEach((cand) => {
    const card = document.createElement("div");
    card.className = "candidate-card";

    const badgeClass = cand.rarity === "Everyday" ? "badge-everyday"
      : cand.rarity === "Regular" ? "badge-regular" : "badge-special";

    const tamilText = cand.tamil_name ? `<div class="candidate-tamil">${cand.tamil_name}</div>` : "";
    const imgSrc = cand.image_local_path || "/static/images/fallback.jpg";

    card.innerHTML = `
      <div class="candidate-header">
        <img class="candidate-img" src="${imgSrc}" alt="${cand.common_name}" onerror="this.style.display='none'">
        <div class="candidate-meta">
          <span class="badge ${badgeClass}">${cand.rarity}</span>
          <div class="candidate-title">${cand.common_name}</div>
          ${tamilText}
          <div class="candidate-sci">${cand.scientific_name}</div>
        </div>
      </div>
      <div class="confirm-box">
        <div class="confirm-label">${currentLang === "en" ? "LOOK TO CONFIRM" : "உறுதிப்படுத்தப் பாருங்கள்"}</div>
        <div class="confirm-question">${cand.confirm_question}</div>
        <button class="unlock-btn" onclick="alert('Confirmed! Species card added to your collection.')">
          ${currentLang === "en" ? "✓ Yes, that matches" : "✓ ஆம், பொருந்துகிறது"}
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

function refreshCurrentScreen() {
  renderHomeScreen();
  if (questionView.classList.contains("active")) {
    renderCurrentQuestion();
  } else if (summaryView.classList.contains("active")) {
    renderSummaryScreen();
  }
}

function resetToHome() {
  showView("home-view");
  loadStats();
}

function showView(viewId) {
  [homeView, questionView, summaryView, resultsView].forEach((v) => v.classList.remove("active"));
  document.getElementById(viewId).classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

window.addEventListener("DOMContentLoaded", init);
