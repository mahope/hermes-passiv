/**
 * bugbottle-demo.js — drives the live demo form on /bugbottle-demo
 * using the real bugbottle library from jsDelivr (same build users install).
 */
import {
  initConsoleBuffer,
  getConsoleBuffer,
  resetConsoleBuffer,
  collectContext,
  captureScreenshot,
} from "https://cdn.jsdelivr.net/gh/mahope/bugbottle@v0.2.4/dist/index.js";

initConsoleBuffer();

const $ = (id) => document.getElementById(id);
const form = $("reportForm");
if (form) {
  const status = $("status");
  const setMsg = (text, cls) => { status.textContent = text; status.className = "bb-status " + cls; };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = $("sendBtn");
    btn.disabled = true;
    setMsg("Capturing and sending…", "");

    try {
      const type = $("type").value;
      const message = $("message").value.trim();
      if (!message) throw new Error("Write a message first.");

      let screenshotDataUrl;
      if ($("shot").checked) {
        // capture the page as it looked BEFORE the form interaction noise
        screenshotDataUrl = await captureScreenshot();
      }

      const res = await fetch("/api/bugbottle-demo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type,
          message,
          screenshotDataUrl,
          console: getConsoleBuffer(),
          context: collectContext(),
        }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok || !body?.ok) throw new Error(body?.error || `HTTP ${res.status}`);

      setMsg(`Sent ✓ — report ${body.id} received with ${screenshotDataUrl ? "screenshot, " : ""}${getConsoleBuffer().length} console entries and context attached.`, "bb-ok");
      form.reset();
      $("shot").checked = true;
      resetConsoleBuffer();
      loadReports();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : String(err), "bb-err");
    } finally {
      btn.disabled = false;
    }
  });
}

async function loadReports() {
  const list = $("reports");
  if (!list) return;
  try {
    const res = await fetch("/api/bugbottle-demo");
    const body = await res.json();
    const reports = body.reports || [];
    if (!reports.length) {
      list.innerHTML = '<li style="border:none;color:var(--color-text-muted)">No reports yet today — be the first to send one.</li>';
      return;
    }
    list.innerHTML = "";
    for (const r of reports) {
      const li = document.createElement("li");
      const when = r.at ? new Date(r.at).toLocaleTimeString() : "";
      const shot = r.screenshot ? ` · 📷 ${Math.round(r.screenshot.bytes / 1024)} kB PNG` : "";
      li.innerHTML =
        `<span class="bb-badge bb-${r.type}">${r.type}</span> ` +
        `<span style="white-space:pre-wrap"></span>` +
        `<div class="bb-meta">${when} · ${r.consoleCount} console entries · ${r.context?.viewport || "?"} viewport${shot} · id ${r.id}</div>`;
      li.querySelector("span:nth-child(2)").textContent = r.message;
      list.appendChild(li);
    }
  } catch {
    list.innerHTML = '<li style="border:none;color:var(--color-text-muted)">Could not load reports right now.</li>';
  }
}
loadReports();
setInterval(loadReports, 30000);
