const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

let promptData = {};
let promptStarted = false;

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(window.__toast);
  window.__toast = setTimeout(() => t.classList.remove("show"), 2800);
}

function setView(view) {
  $$(".view").forEach(v => v.classList.toggle("active", v.id === `view-${view}`));
  $$(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  const titles = {
    home: "Many AI minds. One intelligent workflow.",
    arena: "AI Arena — challenge the answers.",
    delegator: "AI Delegator — approve the work.",
    prompt: "Prompt Lab — refine your intent."
  };
  $("#pageTitle").textContent = titles[view] || titles.home;
  window.scrollTo({top:0, behavior:"smooth"});
}
$$("[data-view]").forEach(b => b.addEventListener("click", () => setView(b.dataset.view)));

async function api(path, body) {
  const r = await fetch(path, {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(body)
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || "Request failed");
  return data;
}

$("#healthBtn").addEventListener("click", async () => {
  try {
    const r = await fetch("/api/health");
    const d = await r.json();
    const configured = Object.values(d.configured).filter(Boolean).length;
    const total = Object.keys(d.configured).length;
    toast(`${configured}/${total} AI slots configured`);
  } catch(e) { toast("Backend is not reachable"); }
});

$("#arenaRun").addEventListener("click", async () => {
  const q = $("#arenaQuestion").value.trim();
  if (!q) return toast("Enter a question first.");
  const box = $("#arenaResults");
  box.innerHTML = `<div class="empty-state"><div class="empty-icon">◌</div><h3>Models are thinking...</h3><p>Independent responses are being collected and compared.</p></div>`;
  try {
    const d = await api("/api/arena", {question:q, context:$("#arenaContext").value.trim()});
    const cards = d.responses.map(r => `
      <article class="agent-card">
        <div class="agent-head"><span class="agent-name">${esc(r.agent)}</span><span class="${r.status==="success"?"ok":""}">${r.status}</span></div>
        <p>${esc(r.answer)}</p>
      </article>`).join("");
    const s = d.synthesis || {};
    const conflicts = (s.conflicts || []).map(c => `<div class="conflict"><b>${esc(c.topic || "Conflict")}</b><p>${esc((c.positions||[]).join(" vs "))}</p><small>${esc(c.why||"")}</small></div>`).join("");
    box.innerHTML = `
      <div class="agent-grid">${cards}</div>
      <div class="synthesis">
        <h4>⚡ Synthesis & conflict map</h4>
        <p><b>Consensus:</b> ${esc(s.consensus||"—")}</p>
        <p><b>Agreement:</b> ${esc((s.agreement_points||[]).join(" • ")||"None recorded")}</p>
        ${conflicts ? `<h4 style="margin-top:12px">Conflicts</h4>${conflicts}` : ""}
        <p><b>Uncertainty:</b> ${esc((s.uncertainties||[]).join(" • ")||"None recorded")}</p>
        <p><b>Next step:</b> ${esc(s.recommended_next_step||"—")}</p>
      </div>`;
  } catch(e) {
    box.innerHTML = `<div class="empty-state"><div class="empty-icon">!</div><h3>Arena could not run</h3><p>${esc(e.message)}</p></div>`;
  }
});

$("#delegatePlan").addEventListener("click", async () => {
  const requirement = $("#delegateRequirement").value.trim();
  if (!requirement) return toast("Describe your goal first.");
  const box = $("#delegateResults");
  box.innerHTML = `<div class="empty-state"><div class="empty-icon">◌</div><h3>Mapping the work...</h3><p>MindMesh is identifying specialist tasks.</p></div>`;
  try {
    const d = await api("/api/delegator/plan", {requirement});
    const tasks = d.tasks || [];
    box.innerHTML = `
      <div class="tag">PROPOSED TEAM</div>
      <h3 style="margin:8px 0 4px">${esc(d.summary||"Specialist task plan")}</h3>
      <p class="muted" style="margin-bottom:14px">Select the tasks you permit MindMesh to execute.</p>
      <div class="task-list">${tasks.map((t,i)=>`
        <label class="task">
          <input type="checkbox" class="task-check" data-index="${i}" checked>
          <div><div class="specialty">${esc(t.specialty||"specialist")}</div><h4>${esc(t.title||"Task")}</h4><p>${esc(t.reason||"")}<br><b>Deliverable:</b> ${esc(t.deliverable||"")}</p></div>
        </label>`).join("")}</div>
      <button class="primary full" style="margin-top:14px" id="runApproved">Run Approved Agents →</button>
      <div id="delegatorRunResults"></div>`;
    $("#runApproved").addEventListener("click", async () => {
      const approved = [...$$(".task-check")].filter(x=>x.checked).map(x=>tasks[Number(x.dataset.index)]);
      if (!approved.length) return toast("Approve at least one task.");
      $("#runApproved").disabled = true;
      $("#runApproved").textContent = "Running approved agents...";
      try {
        const out = await api("/api/delegator/run", {requirement, tasks:approved});
        $("#delegatorRunResults").innerHTML = `<div class="run-results">${(out.results||[]).map(r=>`
          <div class="result-item"><h4>${esc(r.title||r.specialty)} · ${r.status}</h4><p>${esc(r.result||"")}</p></div>`).join("")}</div>`;
        toast("Approved agents completed.");
      } catch(e) { toast(e.message); }
      finally { $("#runApproved").disabled=false; $("#runApproved").textContent="Run Approved Agents →"; }
    });
  } catch(e) {
    box.innerHTML = `<div class="empty-state"><div class="empty-icon">!</div><h3>Planner could not run</h3><p>${esc(e.message)}</p></div>`;
  }
});

function addBubble(role, label, text) {
  const m = $("#promptMessages");
  const empty = m.querySelector(".empty-state");
  if (empty) empty.remove();
  const d = document.createElement("div");
  d.className = `bubble ${role}`;
  d.innerHTML = `<div class="label">${esc(label)}</div>${esc(text).replace(/\n/g,"<br>")}`;
  m.appendChild(d);
  m.scrollTop = m.scrollHeight;
}

function renderContext(data) {
  promptData = data || {};
  const ctx = promptData.known_context || {};
  const entries = Object.entries(ctx);
  $("#contextCount").textContent = `${entries.length} fact${entries.length===1?"":"s"}`;
  $("#contextList").innerHTML = entries.length
    ? entries.map(([k,v]) => `<div class="context-item"><b>${esc(k)}</b><span>${esc(String(v))}</span></div>`).join("")
    : `<div class="muted">Your collected requirements will appear here.</div>`;
  $("#completePrompt").disabled = entries.length < 1;
}

async function startPrompt() {
  const input = $("#promptInput");
  const text = input.value.trim();
  if (!text) return toast("Start with a simple request.");
  input.value = "";
  addBubble("user","YOU",text);
  $("#promptSend").disabled = true;
  try {
    const d = await api("/api/prompt/start",{request:text});
    promptStarted = true;
    promptData = {
      known_context: {...(d.known_context||{}), original_request:text},
      understanding:d.understanding,
      next_question:d.next_question,
      question_reason:d.question_reason,
      complete_enough:d.complete_enough
    };
    renderContext(promptData);
    addBubble("ai","MINDMESH",`${d.understanding||"I understand the starting request."}\n\n${d.next_question||"What else should I know?"}`);
  } catch(e) { toast(e.message); }
  finally { $("#promptSend").disabled=false; }
}

async function answerPrompt() {
  const input = $("#promptInput");
  const answer = input.value.trim();
  if (!answer) return toast("Answer the current question.");
  input.value = "";
  addBubble("user","YOU",answer);
  $("#promptSend").disabled = true;
  try {
    const d = await api("/api/prompt/answer",{data:promptData,answer});
    promptData = {...d, known_context:d.known_context||{}};
    renderContext(promptData);
    addBubble("ai","MINDMESH",`${d.understanding||"Context updated."}\n\n${d.next_question||"You can complete the prompt when ready."}`);
  } catch(e) { toast(e.message); }
  finally { $("#promptSend").disabled=false; }
}

$("#promptSend").addEventListener("click", () => promptStarted ? answerPrompt() : startPrompt());
$("#promptInput").addEventListener("keydown", e => {
  if (e.key==="Enter" && !e.shiftKey) { e.preventDefault(); $("#promptSend").click(); }
});

$("#completePrompt").addEventListener("click", async () => {
  if (!Object.keys(promptData.known_context||{}).length) return toast("Add some context first.");
  $("#completePrompt").disabled = true;
  $("#completePrompt").textContent = "Architecting...";
  try {
    const d = await api("/api/prompt/complete",{data:promptData});
    $("#finalPrompt").classList.remove("hidden");
    $("#finalTitle").textContent = d.title || "Your optimized prompt";
    $("#finalPromptText").textContent = d.prompt || "";
    $("#finalPrompt").scrollIntoView({behavior:"smooth",block:"center"});
    toast("Final prompt generated.");
  } catch(e) { toast(e.message); }
  finally { $("#completePrompt").disabled=false; $("#completePrompt").textContent="Complete Prompt ✦"; }
});

$("#copyPrompt").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText($("#finalPromptText").textContent); toast("Prompt copied."); }
  catch(e) { toast("Copy failed — select the prompt manually."); }
});

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
