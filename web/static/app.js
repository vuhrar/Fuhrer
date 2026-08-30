(() => {
  const $ = (id) => document.getElementById(id);
  const tokenKey = "fuhrer_app_token";
  let token = localStorage.getItem(tokenKey) || "";
  const headers = () => ({"Content-Type":"application/json","X-App-Token":token});

  function show(id, html) { const el = $(id); el.hidden = false; el.innerHTML = html; }
  function loading(id) { show(id, '<div class="loading">جارٍ التنفيذ…</div>'); }
  function esc(value) { return String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[c])); }
  async function api(url, options = {}) {
    const response = await fetch(url, {...options, headers: {...headers(), ...(options.headers || {})}});
    let body = {};
    try { body = await response.json(); } catch (_) {}
    if (!response.ok) throw new Error(body.detail || body.error || `HTTP ${response.status}`);
    return body;
  }
  function taskPrompt(text, task) {
    const instructions = {
      contract_review: "راجع النص كمسودة مراجعة قانونية. استخرج: ملخصًا تنفيذيًا، الأطراف والنطاق والمدة، التزامات كل طرف، المقابل والدفع، السرية والملكية الفكرية، المسؤولية والضمانات، الإنهاء، القانون والاختصاص، المخاطر، البنود الناقصة، ونقاط تفاوض عملية. لا تفترض وقائع غير موجودة واذكر المواد التي تحتاج تحققًا.",
      case_analysis: "حلل الوقائع قانونيًا تحليلًا أوليًا: التكييف المحتمل، الوقائع المؤثرة، الأدلة المطلوبة، نقاط القوة والضعف، المخاطر الإجرائية، والخيارات العملية. ميّز بوضوح بين النص الموجود والاستنتاج.",
      summary: "لخّص النص في عناوين واضحة مع إبراز الالتزامات والمواعيد والمبالغ والمخاطر والعبارات التي تحتاج مراجعة."
    };
    return `${instructions[task]}\n\nالنص:\n${text}`;
  }
  async function login() {
    const error = $("loginError"); error.hidden = true;
    const value = $("tokenInput").value.trim();
    if (!value) { error.textContent = "أدخل رمز الوصول."; error.hidden = false; return; }
    token = value;
    try { await api("/api/auth/verify", {method:"POST"}); localStorage.setItem(tokenKey, token); $("loginView").hidden = true; $("appView").hidden = false; }
    catch (e) { token = ""; error.textContent = e.message; error.hidden = false; }
  }
  function logout() { token = ""; localStorage.removeItem(tokenKey); $("appView").hidden = true; $("loginView").hidden = false; $("tokenInput").value = ""; }
  function activatePanel(panelId) { document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.panel === panelId)); document.querySelectorAll(".panel").forEach(p => { p.hidden = p.id !== panelId; p.classList.toggle("active", p.id === panelId); }); }

  async function analyze() {
    const text = $("analysisText").value.trim(); if (!text) return show("analysisResult", "اكتب النص أولًا.");
    loading("analysisResult");
    try { const body = await api("/api/analyze", {method:"POST", body:JSON.stringify({prompt:taskPrompt(text,$("analysisTask").value), system:"أنت مساعد قانوني سعودي حذر. لا تقدم نتيجة نهائية، واذكر حدود المعلومات والمصادر المطلوبة.")}); show("analysisResult", `<h3>نتيجة التحليل</h3><div>${esc(body.response).replace(/\n/g,"<br>")}</div>`); }
    catch (e) { show("analysisResult", `<p class="error">${esc(e.message)}</p>`); }
  }
  async function search() {
    const query = $("searchQuery").value.trim(); if (!query) return show("searchResult", "أدخل عبارة البحث أولًا."); loading("searchResult");
    try { const body = await api("/api/law-search", {method:"POST", body:JSON.stringify({query,max_results:10})}); const results = body.results || []; show("searchResult", results.length ? results.map(r => `<article class="result-item"><strong>${esc(r.title || "مادة قانونية")}</strong><br><span>${esc(r.article ? "المادة " + r.article : "")}</span><p>${esc(r.text || "").slice(0,1800)}</p></article>`).join("") : "لم يتم العثور على نتائج."); }
    catch (e) { show("searchResult", `<p class="error">${esc(e.message)}</p>`); }
  }
  async function calculate() {
    loading("calcResult");
    const payload = {basic_salary:+$("basicSalary").value,total_salary:+$("totalSalary").value,years_of_service:+$("yearsService").value,delay_months:+$("delayMonths").value,is_arbitrary:$("isArbitrary").checked,resignation:$("resignation").checked,is_saudi:true};
    try { const body = await api("/api/calculate/eosb", {method:"POST", body:JSON.stringify(payload)}); const r=body.result; show("calcResult", `<h3>النتيجة التقديرية: ${esc((r.totals.grand_total||0).toLocaleString("ar-SA"))} ريال</h3><p>تُعرض كتقدير مبني على المدخلات، وليست استحقاقًا نهائيًا.</p>${Object.values(r.details||{}).map(d=>`<div class="result-item"><strong>${esc(d.description)}</strong><br>${esc((d.amount||0).toLocaleString("ar-SA"))} ريال<br><small>${esc(d.formula)}</small></div>`).join("")}`); }
    catch (e) { show("calcResult", `<p class="error">${esc(e.message)}</p>`); }
  }
  async function upload() {
    const files = $("fileInput").files; if (!files.length) return show("fileResult", "اختر ملفًا واحدًا على الأقل."); const form = new FormData(); [...files].slice(0,5).forEach(f=>form.append("files",f)); loading("fileResult");
    try { const body = await api("/api/upload", {method:"POST", headers:{"X-App-Token":token}, body:form}); show("fileResult", `<p>تمت معالجة ${body.summary.success} من ${body.summary.total} ملفات.</p>${(body.results||[]).map(r=>`<article class="result-item"><strong>${esc(r.filename)}</strong><br>${r.success?`<textarea rows="8" readonly>${esc(r.text)}</textarea>`:`<span class="error">${esc(r.error)}</span>`}</article>`).join("")}`); }
    catch (e) { show("fileResult", `<p class="error">${esc(e.message)}</p>`); }
  }

  $("loginButton").addEventListener("click", login); $("tokenInput").addEventListener("keydown", e=>{if(e.key==="Enter")login()}); $("logoutButton").addEventListener("click", logout); $("analyzeButton").addEventListener("click", analyze); $("searchButton").addEventListener("click", search); $("calcButton").addEventListener("click", calculate); $("uploadButton").addEventListener("click", upload); document.querySelectorAll(".tab").forEach(t=>t.addEventListener("click",()=>activatePanel(t.dataset.panel)));
  if (token) api("/api/auth/verify", {method:"POST"}).then(()=>{$("loginView").hidden=true;$("appView").hidden=false}).catch(()=>{token="";localStorage.removeItem(tokenKey)});
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
})();
