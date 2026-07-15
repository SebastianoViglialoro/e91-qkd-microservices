const API_GATEWAY_URL = "http://localhost:18000";
const BASIS_MODEL = "TWO_KEY_BASES_ONE_CHECK_BASIS";
const AUTO_REFRESH_MS = 15000;
const TSIRELSON_BOUND = 2.8284271247461903;
const LOSS_DEGRADED_THRESHOLD_DB = 5.0;
const LOSS_CRITICAL_THRESHOLD_DB = 7.0;

const state = {
  latestResult: null,
  latestKeys: [],
  summary: null,
  preview: null,
  isRunning: false,
  autoRefreshTimer: null,
  animationFrame: null,
};

const dom = {};

document.addEventListener("DOMContentLoaded", () => {
  bindDom();
  bindEvents();
  setStatus("idle");
  renderEmptyResult();
  renderEmptySummary();
  renderLivePreview();
  startProtocolAnimation();
  logEvent("dashboard loaded", "ok");
  refreshData();
  state.autoRefreshTimer = window.setInterval(() => refreshData({ silent: true }), AUTO_REFRESH_MS);
});

function bindDom() {
  dom.form = document.getElementById("simulation-form");
  dom.refreshButton = document.getElementById("refresh-button");
  dom.runButton = document.getElementById("run-button");
  dom.status = document.getElementById("current-status");
  dom.protocolState = document.getElementById("protocol-state");
  dom.protocolMap = document.getElementById("protocol-map");
  dom.noiseNode = document.getElementById("noise-node");
  dom.eveNode = document.getElementById("eve-node");
  dom.protocolCanvas = document.getElementById("protocol-canvas");
  dom.liveEstimateStatus = document.getElementById("live-estimate-status");
  dom.latestResultGrid = document.getElementById("latest-result-grid");
  dom.latestSessionChip = document.getElementById("latest-session-chip");
  dom.summaryGrid = document.getElementById("summary-grid");
  dom.kmsTableBody = document.getElementById("kms-table-body");
  dom.keyDetailPanel = document.getElementById("key-detail-panel");
  dom.keyDetailSubtitle = document.getElementById("key-detail-subtitle");
  dom.keyDetailGrid = document.getElementById("key-detail-grid");
  dom.closeDetailButton = document.getElementById("close-detail-button");
  dom.logList = document.getElementById("log-list");
  dom.chartWarning = document.getElementById("chart-warning");
  dom.metricAbsChsh = document.getElementById("metric-abs-chsh");
  dom.metricQber = document.getElementById("metric-qber");
  dom.metricSecurity = document.getElementById("metric-security");
  dom.metricKey = document.getElementById("metric-key");
  dom.inputShots = document.getElementById("shots");
  dom.inputEnableNoise = document.getElementById("enable-noise");
  dom.inputNoiseLevel = document.getElementById("noise-level");
  dom.inputEnableEve = document.getElementById("enable-eve");
  dom.inputEveAttackProbability = document.getElementById("eve-attack-probability");
  dom.inputEnableLinkLoss = document.getElementById("enable-link-loss");
  dom.inputSourceAliceDistanceKm = document.getElementById("source-alice-distance-km");
  dom.inputSourceBobDistanceKm = document.getElementById("source-bob-distance-km");
  dom.inputAttenuationDbPerKm = document.getElementById("attenuation-db-per-km");
}

function bindEvents() {
  dom.form.addEventListener("submit", (event) => {
    event.preventDefault();
    runSimulation();
  });
  dom.refreshButton.addEventListener("click", () => refreshData());
  dom.closeDetailButton.addEventListener("click", hideKeyDetail);
  document.querySelectorAll(".scenario-button").forEach((button) => {
    button.addEventListener("click", () => applyScenario(button.dataset.scenario));
  });
  dom.form.addEventListener("input", () => renderLivePreview());
  dom.form.addEventListener("change", () => renderLivePreview());
  window.addEventListener("resize", debounce(() => {
    renderCharts(state.latestKeys, state.summary);
    renderLivePreview();
  }, 150));
}

function applyScenario(scenario) {
  const presets = {
    baseline: {
      enable_noise: false,
      noise_level: 0,
      enable_eve: false,
      eve_attack_probability: 0,
      enable_link_loss: true,
      source_alice_distance_km: 25,
      source_bob_distance_km: 25,
      attenuation_db_per_km: 0.02,
    },
    degraded: {
      enable_noise: true,
      noise_level: 0.10,
      enable_eve: false,
      eve_attack_probability: 0,
      enable_link_loss: true,
      source_alice_distance_km: 25,
      source_bob_distance_km: 25,
      attenuation_db_per_km: 0.02,
    },
    insecure: {
      enable_noise: true,
      noise_level: 0.25,
      enable_eve: false,
      eve_attack_probability: 0,
      enable_link_loss: true,
      source_alice_distance_km: 25,
      source_bob_distance_km: 25,
      attenuation_db_per_km: 0.02,
    },
    "link-nominal": {
      enable_noise: false,
      noise_level: 0,
      enable_eve: false,
      eve_attack_probability: 0,
      enable_link_loss: true,
      source_alice_distance_km: 25,
      source_bob_distance_km: 25,
      attenuation_db_per_km: 0.02,
    },
    "link-degraded": {
      enable_noise: false,
      noise_level: 0,
      enable_eve: false,
      eve_attack_probability: 0,
      enable_link_loss: true,
      source_alice_distance_km: 150,
      source_bob_distance_km: 150,
      attenuation_db_per_km: 0.02,
    },
    "link-critical": {
      enable_noise: false,
      noise_level: 0,
      enable_eve: false,
      eve_attack_probability: 0,
      enable_link_loss: true,
      source_alice_distance_km: 200,
      source_bob_distance_km: 200,
      attenuation_db_per_km: 0.02,
    },
  };
  const preset = presets[scenario] || presets.baseline;
  dom.inputEnableNoise.checked = preset.enable_noise;
  dom.inputNoiseLevel.value = preset.noise_level.toFixed(2);
  dom.inputEnableEve.checked = preset.enable_eve;
  dom.inputEveAttackProbability.value = preset.eve_attack_probability.toFixed(2);
  dom.inputEnableLinkLoss.checked = preset.enable_link_loss;
  dom.inputSourceAliceDistanceKm.value = String(preset.source_alice_distance_km);
  dom.inputSourceBobDistanceKm.value = String(preset.source_bob_distance_km);
  dom.inputAttenuationDbPerKm.value = preset.attenuation_db_per_km.toFixed(2);
  renderLivePreview();
  logEvent(`scenario applied: ${scenario}`, "ok");
}

async function runSimulation() {
  const payload = readSimulationPayload();
  state.isRunning = true;
  setStatus("running");
  setBusy(true);
  hideKeyDetail();
  applyProtocolHighlights({
    security_status: "running",
    enable_noise: payload.enable_noise,
    enable_eve: payload.enable_eve,
  });
  logEvent("simulation started", "warn");

  try {
    const result = await fetchJson(`${API_GATEWAY_URL}/simulations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.latestResult = result;
    renderLatestResult(result);
    const extracted = extractSimulation(result);
    setStatus(extracted.security_status || "idle");
    applyProtocolHighlights({
      security_status: extracted.security_status,
      enable_noise: getNested(result, ["request", "enable_noise"], payload.enable_noise),
      enable_eve: getNested(result, ["request", "enable_eve"], payload.enable_eve),
    });
    logEvent(`simulation completed: ${shortSession(result.session_id)}`, "ok");
    await refreshData({ silent: true });
  } catch (error) {
    setStatus("error");
    applyProtocolHighlights({ security_status: "error" });
    logEvent(errorMessage(error), "error");
  } finally {
    state.isRunning = false;
    renderLivePreview();
    setBusy(false);
  }
}

async function refreshData(options = {}) {
  if (!options.silent) {
    logEvent("data refresh started", "warn");
  }
  try {
    const [summary, latestKeys] = await Promise.all([
      fetchJson(`${API_GATEWAY_URL}/keys/summary`),
      fetchJson(`${API_GATEWAY_URL}/keys/latest?limit=10`),
    ]);
    state.summary = summary;
    state.latestKeys = Array.isArray(latestKeys) ? latestKeys : [];
    renderSummary(summary);
    renderKmsTable(state.latestKeys);
    renderCharts(state.latestKeys, summary);
    if (!options.silent) {
      logEvent("data refreshed", "ok");
    }
  } catch (error) {
    logEvent(errorMessage(error), "error");
    renderApiError();
  }
}

async function showKeyDetail(sessionId) {
  if (!sessionId) return;
  dom.keyDetailPanel.classList.remove("hidden");
  dom.keyDetailSubtitle.textContent = `loading ${shortSession(sessionId)}`;
  renderKeyValueGrid(dom.keyDetailGrid, [["status", "loading"]], "result-item");
  try {
    const record = await fetchJson(`${API_GATEWAY_URL}/keys/${encodeURIComponent(sessionId)}`);
    dom.keyDetailSubtitle.textContent = `GET /keys/${shortSession(sessionId)}`;
    renderKeyDetail(record);
    logEvent(`key detail loaded: ${shortSession(sessionId)}`, "ok");
  } catch (error) {
    renderKeyValueGrid(dom.keyDetailGrid, [["error", errorMessage(error)]], "result-item");
    logEvent(errorMessage(error), "error");
  }
}

function hideKeyDetail() {
  dom.keyDetailPanel.classList.add("hidden");
}

function renderLivePreview() {
  const payload = readSimulationPayload();
  const preview = estimateScenario(payload);
  state.preview = preview;

  dom.liveEstimateStatus.className = `status-pill status-${preview.security_status}`;
  dom.liveEstimateStatus.textContent = `preview ${preview.security_status}`;

  if (!state.isRunning) {
    dom.protocolState.textContent = `preview ${preview.security_status}`;
    applyProtocolHighlights({
      security_status: preview.security_status,
      enable_noise: payload.enable_noise,
      enable_eve: payload.enable_eve,
    });
  }

  drawBarChart("live-key-chart", {
    labels: ["raw key", "clean est.", "final key"],
    values: [preview.raw_key_estimate, preview.clean_key_estimate, preview.final_key_estimate],
    colors: ["#00e5ff", preview.status_color, "#39ff14"],
  });
}

function estimateScenario(payload) {
  const noise = payload.enable_noise ? clampNumber(payload.noise_level, 0, 1) : 0;
  const eve = payload.enable_eve ? clampNumber(payload.eve_attack_probability, 0, 1) : 0;
  const link = computeLinkPreview(payload);
  const qber = clampNumber(1 - (1 - noise) * (1 - eve * 0.5), 0, 1);
  const chshNoiseFactor = Math.max(0, 1 - 2 * noise);
  const chshEveFactor = Math.max(0, 1 - eve);
  const absChsh = Math.max(0, TSIRELSON_BOUND * chshNoiseFactor * chshEveFactor);
  const effectiveShots = Math.max(0, Math.round(payload.shots - link.lost_pair_estimate));
  const keySubsetEstimate = Math.round(effectiveShots * (2 / 9));
  const cleanKeyEstimate = Math.max(0, Math.round(keySubsetEstimate * (1 - qber)));
  const securityStatus = classifyPreview(absChsh, qber);
  const finalKeyEstimate = securityStatus === "secure" && cleanKeyEstimate > 0 ? 256 : 0;

  return {
    ...payload,
    noise,
    eve,
    ...link,
    effective_shots_estimate: effectiveShots,
    qber,
    abs_chsh: absChsh,
    raw_key_estimate: keySubsetEstimate,
    clean_key_estimate: cleanKeyEstimate,
    final_key_estimate: finalKeyEstimate,
    security_status: securityStatus,
    status_color: statusColor(securityStatus),
  };
}

function computeLinkPreview(payload) {
  const aliceDistance = clampNumber(payload.source_alice_distance_km, 0, Number.MAX_SAFE_INTEGER);
  const bobDistance = clampNumber(payload.source_bob_distance_km, 0, Number.MAX_SAFE_INTEGER);
  const attenuation = clampNumber(payload.attenuation_db_per_km, 0, Number.MAX_SAFE_INTEGER);
  const aliceLoss = aliceDistance * attenuation;
  const bobLoss = bobDistance * attenuation;
  const totalLoss = aliceLoss + bobLoss;
  const transmittance = Math.pow(10, -totalLoss / 10);
  const linkStatus = classifyLinkStatus(totalLoss);
  const lostPairEstimate = payload.enable_link_loss
    ? Math.round(payload.shots * (1 - transmittance))
    : 0;

  return {
    alice_loss_db: aliceLoss,
    bob_loss_db: bobLoss,
    total_quantum_loss_db: totalLoss,
    transmittance,
    link_status: linkStatus,
    lost_pair_estimate: lostPairEstimate,
    link_color: linkStatusColor(linkStatus),
  };
}

function classifyLinkStatus(totalLossDb) {
  if (totalLossDb >= LOSS_CRITICAL_THRESHOLD_DB) return "critical";
  if (totalLossDb >= LOSS_DEGRADED_THRESHOLD_DB) return "degraded";
  return "nominal";
}

function classifyPreview(absChsh, qber) {
  if (absChsh <= 2.0 || qber > 0.15) return "insecure";
  if ((absChsh > 2.0 && absChsh < 2.4) || (qber > 0.08 && qber <= 0.15)) return "degraded";
  return "secure";
}

function startProtocolAnimation() {
  const animate = (timestamp) => {
    drawProtocolCanvas(timestamp);
    state.animationFrame = window.requestAnimationFrame(animate);
  };
  state.animationFrame = window.requestAnimationFrame(animate);
}

function drawProtocolCanvas(timestamp) {
  if (!dom.protocolCanvas) return;
  const { ctx, width, height } = prepareCanvas(dom.protocolCanvas);
  clearCanvas(ctx, width, height);

  const preview = state.preview || estimateScenario(readSimulationPayload());
  const source = { x: width * 0.17, y: height * 0.48, label: "EPR", sublabel: "Entangled Source", color: "#bd00ff" };
  const alice = { x: width * 0.66, y: height * 0.28, label: "Alice", sublabel: "C / K0 / K1", color: "#00e5ff" };
  const bob = { x: width * 0.66, y: height * 0.69, label: "Bob", sublabel: "K0 / K1 / C", color: "#39ff14" };
  const eve = { x: width * 0.43, y: height * 0.16, label: "Eve", sublabel: preview.enable_eve ? `attack ${formatNumber(preview.eve, 2)}` : "disabled", color: "#ff3d3d" };
  const noise = { x: width * 0.43, y: height * 0.82, label: "Noise", sublabel: preview.enable_noise ? `level ${formatNumber(preview.noise, 2)}` : "disabled", color: "#ffb300" };
  const kms = { x: width * 0.88, y: height * 0.49, label: "Mini KMS", sublabel: `${preview.clean_key_estimate} clean bits`, color: preview.status_color };
  const linkColor = preview.enable_link_loss ? preview.link_color : "#8b949e";

  drawLink(ctx, source, alice, linkColor, 0.8);
  drawLink(ctx, source, bob, linkColor, 0.8);
  drawLink(ctx, alice, kms, preview.status_color, 0.45);
  drawLink(ctx, bob, kms, preview.status_color, 0.45);
  drawLinkLabel(
    ctx,
    source,
    alice,
    `${formatNumber(preview.source_alice_distance_km, 0)} km | ${formatNumber(preview.alice_loss_db, 2)} dB`,
    linkColor,
    -14,
  );
  drawLinkLabel(
    ctx,
    source,
    bob,
    `${formatNumber(preview.source_bob_distance_km, 0)} km | ${formatNumber(preview.bob_loss_db, 2)} dB`,
    linkColor,
    16,
  );
  drawCanvasTag(
    ctx,
    width * 0.36,
    height * 0.49,
    `${formatNumber(preview.total_quantum_loss_db, 2)} dB | ${preview.link_status}`,
    linkColor,
  );

  if (preview.enable_eve) {
    drawLink(ctx, eve, source, "#ff3d3d", 0.7, true);
  }
  if (preview.enable_noise) {
    drawLink(ctx, noise, source, "#ffb300", 0.7, true);
  }

  drawMovingPacket(ctx, source, alice, timestamp, "#00e5ff", 0);
  drawMovingPacket(ctx, source, bob, timestamp, "#39ff14", 0.35);
  drawMovingPacket(ctx, alice, kms, timestamp, preview.status_color, 0.15);
  drawMovingPacket(ctx, bob, kms, timestamp, preview.status_color, 0.55);
  if (preview.enable_eve) drawMovingPacket(ctx, eve, source, timestamp, "#ff3d3d", 0.2);
  if (preview.enable_noise) drawMovingPacket(ctx, noise, source, timestamp, "#ffb300", 0.65);

  drawNode(ctx, source, 54);
  drawNode(ctx, alice, 52);
  drawNode(ctx, bob, 52);
  drawNode(ctx, kms, 54);
  drawSideNode(ctx, eve, preview.enable_eve);
  drawSideNode(ctx, noise, preview.enable_noise);
  drawPreviewStats(ctx, preview, width, height);
}

function drawLink(ctx, from, to, color, alpha = 1, dashed = false) {
  ctx.save();
  ctx.strokeStyle = colorWithAlpha(color, alpha);
  ctx.lineWidth = dashed ? 1.4 : 2;
  ctx.shadowBlur = 9;
  ctx.shadowColor = colorWithAlpha(color, 0.45);
  if (dashed) ctx.setLineDash([6, 6]);
  ctx.beginPath();
  ctx.moveTo(from.x, from.y);
  const midX = (from.x + to.x) / 2;
  ctx.bezierCurveTo(midX, from.y, midX, to.y, to.x, to.y);
  ctx.stroke();
  ctx.restore();
}

function drawLinkLabel(ctx, from, to, text, color, offsetY = 0) {
  const midX = (from.x + to.x) / 2;
  const midY = (from.y + to.y) / 2 + offsetY;
  drawCanvasTag(ctx, midX, midY, text, color);
}

function drawCanvasTag(ctx, x, y, text, color) {
  ctx.save();
  ctx.font = "700 10px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const width = ctx.measureText(text).width + 16;
  const height = 22;
  ctx.fillStyle = "rgba(13, 17, 23, 0.9)";
  ctx.strokeStyle = colorWithAlpha(color, 0.7);
  ctx.lineWidth = 1;
  ctx.beginPath();
  roundedRect(ctx, x - width / 2, y - height / 2, width, height, 6);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = color;
  ctx.fillText(text, x, y + 0.5);
  ctx.restore();
}

function drawMovingPacket(ctx, from, to, timestamp, color, offset = 0) {
  const phase = ((timestamp / 1700 + offset) % 1);
  const x = from.x + (to.x - from.x) * phase;
  const y = from.y + (to.y - from.y) * phase;
  ctx.save();
  ctx.fillStyle = color;
  ctx.shadowBlur = 14;
  ctx.shadowColor = color;
  ctx.beginPath();
  ctx.arc(x, y, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawNode(ctx, node, radius) {
  ctx.save();
  ctx.fillStyle = "rgba(22, 27, 34, 0.96)";
  ctx.strokeStyle = node.color;
  ctx.lineWidth = 1.8;
  ctx.shadowBlur = 18;
  ctx.shadowColor = colorWithAlpha(node.color, 0.35);
  ctx.beginPath();
  ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.shadowBlur = 0;
  ctx.fillStyle = node.color;
  ctx.font = "700 15px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(node.label, node.x, node.y - 5);
  ctx.fillStyle = "#8b949e";
  ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.fillText(node.sublabel, node.x, node.y + 14);
  ctx.restore();
}

function drawSideNode(ctx, node, active) {
  const radius = active ? 36 : 30;
  ctx.save();
  ctx.globalAlpha = active ? 1 : 0.42;
  ctx.fillStyle = active ? "rgba(22, 27, 34, 0.96)" : "rgba(13, 17, 23, 0.88)";
  ctx.strokeStyle = node.color;
  ctx.lineWidth = active ? 1.8 : 1;
  ctx.setLineDash(active ? [] : [4, 4]);
  ctx.beginPath();
  ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = node.color;
  ctx.font = "700 12px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.textAlign = "center";
  ctx.fillText(node.label, node.x, node.y - 4);
  ctx.fillStyle = "#8b949e";
  ctx.font = "9px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.fillText(node.sublabel, node.x, node.y + 12);
  ctx.restore();
}

function drawPreviewStats(ctx, preview, width, height) {
  const boxWidth = Math.min(285, width * 0.38);
  const x = Math.max(12, width - boxWidth - 12);
  const y = 12;
  ctx.save();
  ctx.fillStyle = "rgba(13, 17, 23, 0.86)";
  ctx.strokeStyle = colorWithAlpha(preview.status_color, 0.65);
  ctx.lineWidth = 1;
  ctx.beginPath();
  roundedRect(ctx, x, y, boxWidth, 136, 8);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = preview.status_color;
  ctx.font = "800 11px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.fillText(`preview ${preview.security_status}`, x + 12, y + 20);
  ctx.fillStyle = "#f0f6fc";
  ctx.font = "11px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.fillText(`abs_chsh ~= ${formatNumber(preview.abs_chsh, 3)}`, x + 12, y + 43);
  ctx.fillText(`qber ~= ${formatNumber(preview.qber, 3)}`, x + 12, y + 61);
  ctx.fillText(`raw key ~= ${preview.raw_key_estimate}`, x + 12, y + 79);
  ctx.fillStyle = preview.link_color;
  ctx.fillText(`loss ~= ${formatNumber(preview.total_quantum_loss_db, 2)} dB (${preview.link_status})`, x + 12, y + 98);
  ctx.fillText(`lost pairs ~= ${preview.lost_pair_estimate}`, x + 12, y + 116);
  ctx.fillStyle = "#8b949e";
  ctx.font = "9px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.fillText("heuristic preview only", x + 12, y + 130);
  ctx.restore();
}

function roundedRect(ctx, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2);
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + width - r, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + r);
  ctx.lineTo(x + width, y + height - r);
  ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  ctx.lineTo(x + r, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
}

function statusColor(status) {
  const normalized = normalizeStatus(status);
  if (normalized === "secure") return "#39ff14";
  if (normalized === "degraded") return "#ffb300";
  if (normalized === "insecure" || normalized === "error") return "#ff3d3d";
  return "#00e5ff";
}

function linkStatusColor(status) {
  const value = String(status || "").toLowerCase();
  if (value === "critical") return "#ff3d3d";
  if (value === "degraded") return "#ffb300";
  return "#39ff14";
}

function colorWithAlpha(hex, alpha) {
  const clean = hex.replace("#", "");
  const red = parseInt(clean.slice(0, 2), 16);
  const green = parseInt(clean.slice(2, 4), 16);
  const blue = parseInt(clean.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

async function fetchJson(url, options = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(`HTTP ${response.status} from API Gateway: ${detail}`);
    }
    return await response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(`Request timed out. Check that API Gateway is running on ${API_GATEWAY_URL}.`);
    }
    if (String(error.message || "").includes("Failed to fetch")) {
      throw new Error(`Cannot reach API Gateway. Check that API Gateway is running on ${API_GATEWAY_URL}.`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

function readSimulationPayload() {
  const shots = clampNumber(readNumber("shots", 10000), 1, Number.MAX_SAFE_INTEGER);
  const noiseLevel = clampNumber(readNumber("noise-level", 0), 0, 1);
  const eveAttackProbability = clampNumber(readNumber("eve-attack-probability", 0), 0, 1);
  const sourceAliceDistanceKm = clampNumber(readNumber("source-alice-distance-km", 25), 0, Number.MAX_SAFE_INTEGER);
  const sourceBobDistanceKm = clampNumber(readNumber("source-bob-distance-km", 25), 0, Number.MAX_SAFE_INTEGER);
  const attenuationDbPerKm = clampNumber(readNumber("attenuation-db-per-km", 0.02), 0, Number.MAX_SAFE_INTEGER);
  return {
    shots,
    enable_noise: dom.inputEnableNoise.checked,
    noise_level: noiseLevel,
    enable_eve: dom.inputEnableEve.checked,
    eve_attack_probability: eveAttackProbability,
    enable_link_loss: dom.inputEnableLinkLoss.checked,
    source_alice_distance_km: sourceAliceDistanceKm,
    source_bob_distance_km: sourceBobDistanceKm,
    attenuation_db_per_km: attenuationDbPerKm,
    loss_degraded_threshold_db: LOSS_DEGRADED_THRESHOLD_DB,
    loss_critical_threshold_db: LOSS_CRITICAL_THRESHOLD_DB,
  };
}

function readNumber(id, fallback) {
  const value = Number(document.getElementById(id).value);
  return Number.isFinite(value) ? value : fallback;
}

function clampNumber(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function extractSimulation(result) {
  const evaluation = result?.sifting_bell_test || result?.evaluation || {};
  const key = result?.key || result?.key_processing || {};
  const link = result?.link_metrics || result?.transmission?.link_metrics || {};
  return {
    session_id: result?.session_id,
    basis_model: evaluation.basis_model || result?.basis_model || BASIS_MODEL,
    chsh: evaluation.chsh,
    abs_chsh: evaluation.abs_chsh,
    qber: evaluation.qber,
    security_status: evaluation.security_status,
    key_status: key.key_status,
    key_subset_size: evaluation.key_subset_size,
    bell_subset_size: evaluation.bell_subset_size || evaluation.check_subset_size,
    discarded_subset_size: evaluation.discarded_subset_size,
    raw_key_length: key.raw_key_length,
    sifted_key_length: key.sifted_key_length,
    final_key_length: key.final_key_length,
    final_key: key.final_key,
    hash_function: key.hash_function,
    privacy_amplification: key.privacy_amplification,
    total_quantum_loss_db: link.total_quantum_loss_db,
    transmittance: link.transmittance,
    link_status: link.link_status,
    lost_pair_count: link.lost_pair_count,
    source_alice_distance_km: link.source_alice_distance_km,
    source_bob_distance_km: link.source_bob_distance_km,
    attenuation_db_per_km: link.attenuation_db_per_km,
  };
}

function renderLatestResult(result) {
  const item = extractSimulation(result);
  dom.latestSessionChip.textContent = shortSession(item.session_id);
  dom.metricAbsChsh.textContent = formatNumber(item.abs_chsh, 4);
  dom.metricQber.textContent = formatQber(item.qber);
  dom.metricSecurity.textContent = safe(item.security_status);
  dom.metricKey.textContent = safe(item.key_status);

  const rows = [
    ["session_id", shortSession(item.session_id)],
    ["basis_model", item.basis_model],
    ["chsh", formatNumber(item.chsh, 4)],
    ["abs_chsh", formatNumber(item.abs_chsh, 4)],
    ["qber", formatQber(item.qber)],
    ["security_status", badgeText(item.security_status)],
    ["key_status", badgeText(item.key_status)],
    ["key_subset_size", item.key_subset_size],
    ["bell_subset_size", item.bell_subset_size],
    ["discarded_subset_size", item.discarded_subset_size],
    ["total_quantum_loss_db", formatNumber(item.total_quantum_loss_db, 2)],
    ["transmittance", formatNumber(item.transmittance, 4)],
    ["link_status", badgeText(item.link_status)],
    ["lost_pair_count", item.lost_pair_count],
    ["source_alice_distance_km", formatNumber(item.source_alice_distance_km, 1)],
    ["source_bob_distance_km", formatNumber(item.source_bob_distance_km, 1)],
    ["attenuation_db_per_km", formatNumber(item.attenuation_db_per_km, 4)],
    ["raw_key_length", item.raw_key_length],
    ["sifted_key_length", item.sifted_key_length],
    ["final_key_length", item.final_key_length],
    ["final_key", maskKey(item.final_key)],
    ["hash_function", item.hash_function],
    ["privacy_amplification", item.privacy_amplification],
  ];
  renderKeyValueGrid(dom.latestResultGrid, rows, "result-item");
}

function renderEmptyResult() {
  dom.latestSessionChip.textContent = "no session yet";
  dom.metricAbsChsh.textContent = "N/A";
  dom.metricQber.textContent = "N/A";
  dom.metricSecurity.textContent = "N/A";
  dom.metricKey.textContent = "N/A";
  renderKeyValueGrid(
    dom.latestResultGrid,
    [
      ["session_id", "N/A"],
      ["basis_model", BASIS_MODEL],
      ["chsh", "N/A"],
      ["abs_chsh", "N/A"],
      ["qber", "N/A"],
      ["security_status", "N/A"],
      ["key_status", "N/A"],
      ["total_quantum_loss_db", "N/A"],
      ["transmittance", "N/A"],
      ["link_status", "N/A"],
      ["lost_pair_count", "N/A"],
      ["final_key", "N/A"],
    ],
    "result-item",
  );
}

function renderSummary(summary) {
  renderKeyValueGrid(
    dom.summaryGrid,
    [
      ["total_sessions", summary?.total_sessions],
      ["generated_keys", summary?.generated_keys],
      ["discarded_degraded", summary?.discarded_degraded],
      ["discarded_insecure", summary?.discarded_insecure],
      ["insufficient_key_material", summary?.insufficient_key_material],
      ["average_qber", formatQber(summary?.average_qber)],
      ["average_abs_chsh", formatNumber(summary?.average_abs_chsh, 4)],
      ["generated_key_rate", formatRate(summary?.generated_key_rate)],
    ],
    "summary-item",
  );
}

function renderEmptySummary() {
  renderSummary({});
}

function renderKmsTable(records) {
  dom.kmsTableBody.innerHTML = "";
  if (!records.length) {
    const row = document.createElement("tr");
    row.innerHTML = `<td class="table-empty" colspan="11">No key records yet. Run a simulation to populate the repository.</td>`;
    dom.kmsTableBody.appendChild(row);
    return;
  }

  for (const record of records) {
    const row = document.createElement("tr");
    row.className = "kms-row";
    row.dataset.sessionId = record.session_id || "";
    row.innerHTML = `
      <td title="${escapeHtml(record.session_id || "")}">${escapeHtml(shortSession(record.session_id))}</td>
      <td>${escapeHtml(formatDate(record.created_at))}</td>
      <td>${escapeHtml(formatNumber(record.abs_chsh, 4))}</td>
      <td>${escapeHtml(formatQber(record.qber))}</td>
      <td>${badgeHtml(record.security_status)}</td>
      <td>${badgeHtml(record.key_status)}</td>
      <td>${escapeHtml(safe(record.final_key_length))}</td>
      <td>${escapeHtml(formatNumber(record.total_quantum_loss_db, 2))}</td>
      <td>${badgeHtml(record.link_status)}</td>
      <td>${escapeHtml(formatNumber(record.noise_level, 2))}</td>
      <td>${escapeHtml(formatNumber(record.eve_attack_probability, 2))}</td>
    `;
    row.addEventListener("click", () => showKeyDetail(record.session_id));
    dom.kmsTableBody.appendChild(row);
  }
}

function renderKeyDetail(record) {
  const rows = [
    ["session_id", shortSession(record.session_id)],
    ["created_at", formatDate(record.created_at)],
    ["basis_model", record.basis_model],
    ["security_status", record.security_status],
    ["key_status", record.key_status],
    ["abs_chsh", formatNumber(record.abs_chsh, 4)],
    ["chsh", formatNumber(record.chsh, 4)],
    ["qber", formatQber(record.qber)],
    ["raw_key_length", record.raw_key_length],
    ["sifted_key_length", record.sifted_key_length],
    ["final_key_length", record.final_key_length],
    ["final_key", maskKey(record.final_key)],
    ["key_reason", record.key_reason],
    ["source_alice_distance_km", formatNumber(record.source_alice_distance_km, 1)],
    ["source_bob_distance_km", formatNumber(record.source_bob_distance_km, 1)],
    ["total_quantum_loss_db", formatNumber(record.total_quantum_loss_db, 2)],
    ["transmittance", formatNumber(record.transmittance, 4)],
    ["link_status", record.link_status],
    ["noise_enabled", record.noise_enabled],
    ["noise_level", formatNumber(record.noise_level, 2)],
    ["eve_enabled", record.eve_enabled],
    ["eve_attack_probability", formatNumber(record.eve_attack_probability, 2)],
    ["privacy_amplification", record.privacy_amplification],
    ["hash_function", record.hash_function],
  ];
  renderKeyValueGrid(dom.keyDetailGrid, rows, "result-item");
}

function renderCharts(records, summary) {
  const ordered = [...records].reverse();
  const labels = ordered.map((record) => shortSession(record.session_id));
  const chshValues = ordered.map((record) => numericOrNull(record.abs_chsh));
  const qberValues = ordered.map((record) => numericOrNull(record.qber));
  const lossValues = ordered.map((record) => numericOrNull(record.total_quantum_loss_db));
  const generated = Number(summary?.generated_keys || 0);
  const degraded = Number(summary?.discarded_degraded || 0);
  const discarded = Number(summary?.discarded_insecure || 0);

  drawLineChart("chsh-chart", {
    labels,
    values: chshValues,
    color: "#bd00ff",
    label: "abs_chsh",
    min: 0,
    max: Math.max(3, ...chshValues.filter((value) => value !== null)),
    referenceLines: [
      { value: 2.0, color: "#ff3d3d", label: "2.0" },
      { value: 2.4, color: "#ffb300", label: "2.4" },
    ],
  });

  drawLineChart("qber-chart", {
    labels,
    values: qberValues,
    color: "#ff3d3d",
    label: "qber",
    min: 0,
    max: Math.max(0.3, ...qberValues.filter((value) => value !== null)),
    referenceLines: [
      { value: 0.08, color: "#ffb300", label: "0.08" },
      { value: 0.15, color: "#ff3d3d", label: "0.15" },
    ],
  });

  drawLineChart("loss-chart", {
    labels,
    values: lossValues,
    color: "#ffb300",
    label: "total_quantum_loss_db",
    min: 0,
    max: Math.max(8, ...lossValues.filter((value) => value !== null)),
    referenceLines: [
      { value: LOSS_DEGRADED_THRESHOLD_DB, color: "#ffb300", label: "5 dB" },
      { value: LOSS_CRITICAL_THRESHOLD_DB, color: "#ff3d3d", label: "7 dB" },
    ],
  });

  drawBarChart("key-count-chart", {
    labels: ["generated", "degraded", "discarded"],
    values: [generated, degraded, discarded],
    colors: ["#39ff14", "#ffb300", "#ff3d3d"],
  });
}

function drawLineChart(canvasId, options) {
  const canvas = document.getElementById(canvasId);
  const { ctx, width, height, scale } = prepareCanvas(canvas);
  clearCanvas(ctx, width, height);

  const padding = { left: 44, right: 16, top: 18, bottom: 34 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const min = Number.isFinite(options.min) ? options.min : 0;
  const max = options.max > min ? options.max : min + 1;
  const values = options.values || [];
  const validValues = values.filter((value) => value !== null);

  drawGrid(ctx, padding, plotWidth, plotHeight, min, max, scale);
  drawReferenceLines(ctx, options.referenceLines || [], padding, plotWidth, plotHeight, min, max);

  if (validValues.length === 0) {
    drawNoData(ctx, width, height);
    return;
  }

  ctx.save();
  ctx.strokeStyle = options.color;
  ctx.lineWidth = 2;
  ctx.shadowBlur = 10;
  ctx.shadowColor = options.color;
  ctx.beginPath();

  values.forEach((value, index) => {
    if (value === null) return;
    const x = padding.left + (values.length === 1 ? plotWidth / 2 : (plotWidth * index) / (values.length - 1));
    const y = padding.top + plotHeight - ((value - min) / (max - min)) * plotHeight;
    if (index === 0 || values[index - 1] === null) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.shadowBlur = 0;

  values.forEach((value, index) => {
    if (value === null) return;
    const x = padding.left + (values.length === 1 ? plotWidth / 2 : (plotWidth * index) / (values.length - 1));
    const y = padding.top + plotHeight - ((value - min) / (max - min)) * plotHeight;
    ctx.fillStyle = options.color;
    ctx.beginPath();
    ctx.arc(x, y, 3.2, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.restore();

  drawXAxisLabels(ctx, options.labels || [], padding, plotWidth, height);
}

function drawBarChart(canvasId, options) {
  const canvas = document.getElementById(canvasId);
  const { ctx, width, height, scale } = prepareCanvas(canvas);
  clearCanvas(ctx, width, height);

  const padding = { left: 36, right: 16, top: 18, bottom: 40 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const max = Math.max(1, ...options.values);

  drawGrid(ctx, padding, plotWidth, plotHeight, 0, max, scale);
  const gap = 16;
  const barWidth = Math.max(18, (plotWidth - gap * (options.values.length + 1)) / options.values.length);

  options.values.forEach((value, index) => {
    const x = padding.left + gap + index * (barWidth + gap);
    const barHeight = (value / max) * plotHeight;
    const y = padding.top + plotHeight - barHeight;
    ctx.fillStyle = options.colors[index];
    ctx.shadowBlur = 10;
    ctx.shadowColor = options.colors[index];
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.shadowBlur = 0;
    ctx.fillStyle = "#f0f6fc";
    ctx.font = "11px ui-monospace, SFMono-Regular, Menlo, monospace";
    ctx.textAlign = "center";
    ctx.fillText(String(value), x + barWidth / 2, y - 5);
    ctx.fillStyle = "#8b949e";
    ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, monospace";
    ctx.fillText(options.labels[index], x + barWidth / 2, height - 16);
  });
}

function prepareCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  const width = Math.max(260, Math.floor(rect.width || 300));
  const height = Math.max(170, Math.floor(rect.height || 190));
  canvas.width = Math.floor(width * scale);
  canvas.height = Math.floor(height * scale);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  return { ctx, width, height, scale };
}

function clearCanvas(ctx, width, height) {
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#0d1117";
  ctx.fillRect(0, 0, width, height);
}

function drawGrid(ctx, padding, plotWidth, plotHeight, min, max) {
  ctx.save();
  ctx.strokeStyle = "rgba(48, 54, 61, 0.72)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#8b949e";
  ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + (plotHeight * i) / 4;
    const value = max - ((max - min) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(padding.left + plotWidth, y);
    ctx.stroke();
    ctx.fillText(value.toFixed(max <= 1 ? 2 : 1), padding.left - 7, y);
  }
  ctx.strokeStyle = "#30363d";
  ctx.beginPath();
  ctx.moveTo(padding.left, padding.top);
  ctx.lineTo(padding.left, padding.top + plotHeight);
  ctx.lineTo(padding.left + plotWidth, padding.top + plotHeight);
  ctx.stroke();
  ctx.restore();
}

function drawReferenceLines(ctx, lines, padding, plotWidth, plotHeight, min, max) {
  ctx.save();
  ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.textAlign = "right";
  for (const line of lines) {
    if (line.value < min || line.value > max) continue;
    const y = padding.top + plotHeight - ((line.value - min) / (max - min)) * plotHeight;
    ctx.strokeStyle = line.color;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(padding.left + plotWidth, y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = line.color;
    ctx.fillText(line.label, padding.left + plotWidth - 4, y - 7);
  }
  ctx.restore();
}

function drawXAxisLabels(ctx, labels, padding, plotWidth, height) {
  if (!labels.length) return;
  ctx.save();
  ctx.fillStyle = "#8b949e";
  ctx.font = "9px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.textAlign = "center";
  const step = Math.max(1, Math.ceil(labels.length / 5));
  labels.forEach((label, index) => {
    if (index % step !== 0 && index !== labels.length - 1) return;
    const x = padding.left + (labels.length === 1 ? plotWidth / 2 : (plotWidth * index) / (labels.length - 1));
    ctx.fillText(label, x, height - 13);
  });
  ctx.restore();
}

function drawNoData(ctx, width, height) {
  ctx.save();
  ctx.fillStyle = "#8b949e";
  ctx.font = "12px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.textAlign = "center";
  ctx.fillText("No data", width / 2, height / 2);
  ctx.restore();
}

function renderKeyValueGrid(container, rows, itemClass) {
  container.innerHTML = "";
  for (const [label, value] of rows) {
    const item = document.createElement("div");
    item.className = itemClass;
    item.innerHTML = `<span>${escapeHtml(label)}</span><strong title="${escapeHtml(safe(value))}">${escapeHtml(safe(value))}</strong>`;
    container.appendChild(item);
  }
}

function setStatus(status) {
  const normalized = normalizeStatus(status);
  dom.status.className = `status-pill status-${normalized}`;
  dom.status.textContent = normalized;
  dom.protocolState.textContent = normalized;
  dom.protocolMap.classList.toggle("is-running", normalized === "running");
}

function applyProtocolHighlights({ security_status, enable_noise, enable_eve }) {
  const normalized = normalizeStatus(security_status);
  dom.protocolMap.classList.remove("status-secure-map", "status-degraded-map", "status-insecure-map");
  if (normalized === "secure") dom.protocolMap.classList.add("status-secure-map");
  if (normalized === "degraded") dom.protocolMap.classList.add("status-degraded-map");
  if (normalized === "insecure" || normalized === "error") dom.protocolMap.classList.add("status-insecure-map");

  dom.noiseNode.classList.toggle("active-noise", Boolean(enable_noise));
  dom.eveNode.classList.toggle("active-eve", Boolean(enable_eve));
}

function setBusy(isBusy) {
  dom.runButton.disabled = isBusy;
  dom.refreshButton.disabled = isBusy;
  dom.runButton.textContent = isBusy ? "Running..." : "Run Simulation";
}

function renderApiError() {
  renderKeyValueGrid(
    dom.summaryGrid,
    [
      ["API Gateway", "not reachable"],
      ["suggestion", `Check that API Gateway is running on ${API_GATEWAY_URL}`],
    ],
    "summary-item",
  );
}

function logEvent(message, level = "info") {
  const line = document.createElement("div");
  line.className = `log-entry ${level === "error" ? "log-error" : level === "ok" ? "log-ok" : level === "warn" ? "log-warn" : ""}`;
  const timestamp = new Date().toLocaleTimeString();
  line.innerHTML = `<strong>${escapeHtml(timestamp)}</strong> ${escapeHtml(message)}`;
  dom.logList.appendChild(line);
  while (dom.logList.children.length > 80) {
    dom.logList.removeChild(dom.logList.firstChild);
  }
}

function normalizeStatus(status) {
  const value = String(status || "idle").toLowerCase();
  if (["secure", "degraded", "insecure", "running", "error"].includes(value)) return value;
  return "idle";
}

function badgeText(value) {
  return safe(value);
}

function badgeHtml(value) {
  const text = safe(value);
  const lower = text.toLowerCase();
  const cls = lower.includes("generated") || lower.includes("secure") || lower.includes("nominal")
    ? "mini-secure"
    : lower.includes("degraded")
      ? "mini-degraded"
      : lower.includes("discarded") || lower.includes("insecure") || lower.includes("critical")
        ? "mini-insecure"
        : "";
  return `<span class="mini-badge ${cls}">${escapeHtml(text)}</span>`;
}

function shortSession(value) {
  if (!value) return "N/A";
  const text = String(value);
  if (text.length <= 13) return text;
  return `${text.slice(0, 8)}...${text.slice(-4)}`;
}

function maskKey(value) {
  if (!value) return "N/A";
  const text = String(value);
  if (text.length <= 20) return text;
  return `${text.slice(0, 12)}...${text.slice(-8)}`;
}

function safe(value) {
  if (value === undefined || value === null || value === "") return "N/A";
  return String(value);
}

function numericOrNull(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatNumber(value, digits = 4) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "N/A";
  return number.toFixed(digits);
}

function formatQber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "N/A";
  return number.toFixed(4);
}

function formatRate(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "N/A";
  return number.toFixed(4);
}

function formatDate(value) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString();
}

function getNested(object, path, fallback) {
  let current = object;
  for (const key of path) {
    if (!current || typeof current !== "object" || !(key in current)) return fallback;
    current = current[key];
  }
  return current;
}

function errorMessage(error) {
  return error?.message || String(error);
}

function debounce(fn, delayMs) {
  let timer = null;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), delayMs);
  };
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
