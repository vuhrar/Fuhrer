import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const ROLES = [
  { key: 'محامي', label: 'المحامي', description: 'نظرية القضية والدفوع وخطة المواجهة' },
  { key: 'مستشار قانوني', label: 'المستشار القانوني', description: 'العناصر والأدلة والنواقص والتناقضات' },
  { key: 'مستشار عمالي', label: 'المستشار العمالي', description: 'الأجور والحضور والإنهاء والتسوية' },
];

const DEFAULT_CONCEPTS = {
  overtime: ['ساعات إضافية', 'بعد الدوام', 'خارج ساعات العمل'],
  unpaid_wages: ['راتب متأخر', 'عدم سداد الراتب', 'لم يتم تحويل الراتب'],
  deductions: ['خصم من الراتب', 'استقطاع', 'حسم'],
};

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('fuhrer_token') || '');
  const [matterId, setMatterId] = useState('');
  const [matterTitle, setMatterTitle] = useState('نزاع عمالي جديد');
  const [role, setRole] = useState('مستشار عمالي');
  const [text, setText] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [savedRights, setSavedRights] = useState([]);
  const [statements, setStatements] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [apiBase, setApiBase] = useState(import.meta.env.VITE_API_BASE || '/api');

  const headers = useMemo(() => ({ 'Content-Type': 'application/json', 'X-App-Token': token }), [token]);

  async function request(path, options = {}) {
    const response = await fetch(`${apiBase}${path}`, { ...options, headers: { ...headers, ...(options.headers || {}) } });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || `فشل الطلب (${response.status})`);
    return body;
  }

  useEffect(() => {
    if (token) localStorage.setItem('fuhrer_token', token);
  }, [token]);

  async function createMatter() {
    setBusy(true); setMessage('');
    try {
      const result = await request('/matters', { method: 'POST', body: JSON.stringify({ title: matterTitle, matter_type: 'نزاع عمالي' }) });
      setMatterId(result.matter.id);
      setMessage(`تم إنشاء القضية: ${result.matter.id}`);
    } catch (error) { setMessage(error.message); } finally { setBusy(false); }
  }

  async function analyze() {
    if (!matterId) return setMessage('أنشئ قضية أو أدخل معرف قضية أولًا.');
    if (!text.trim()) return setMessage('أدخل النص أو الصق مقتطفًا قانونيًا للتحليل.');
    setBusy(true); setMessage('جارٍ تحليل النص وحفظ الجمل والحقوق...');
    try {
      const result = await request(`/matters/${encodeURIComponent(matterId)}/rights/analyze`, {
        method: 'POST',
        body: JSON.stringify({ text, right_concepts: DEFAULT_CONCEPTS, semantic_matches: [], table_entities: [], claim_keys: [], right_catalog: {}, filename: 'إدخال يدوي', page: 1 }),
      });
      setAnalysis(result.analysis);
      setStatements(result.persisted.statements || []);
      setSavedRights(result.persisted.findings || []);
      setMessage('اكتمل التحليل وحُفظت النتائج في Repository.');
    } catch (error) { setMessage(error.message); } finally { setBusy(false); }
  }

  async function loadSaved() {
    if (!matterId) return setMessage('أدخل معرف القضية أولًا.');
    setBusy(true);
    try {
      const [rights, savedStatements] = await Promise.all([
        request(`/matters/${encodeURIComponent(matterId)}/repository-rights`),
        request(`/matters/${encodeURIComponent(matterId)}/legal-statements`),
      ]);
      setSavedRights(rights.rights || []);
      setStatements(savedStatements.statements || []);
      setMessage('تم تحميل السجل المحفوظ.');
    } catch (error) { setMessage(error.message); } finally { setBusy(false); }
  }

  async function review(right, decision) {
    try {
      await request(`/matters/${encodeURIComponent(matterId)}/right-review`, { method: 'POST', body: JSON.stringify({ discovered_right_id: right.id, decision, note: `قرار من دور ${role}` }) });
      setMessage(`تم تسجيل القرار: ${decision}`);
    } catch (error) { setMessage(error.message); }
  }

  return <main className="shell">
    <header className="topbar">
      <div><span className="eyebrow">FÜHRER / LEGAL INTELLIGENCE</span><h1>مراجعة الحقوق العمالية</h1><p>تحليل قابل للتتبع من النص إلى الحق والدليل والنقص.</p></div>
      <div className="status"><span className="dot" /> مستخدم واحد · خاص</div>
    </header>

    <section className="panel setup">
      <div className="section-title"><div><span className="kicker">01</span><h2>إعداد مساحة العمل</h2></div><button className="ghost" onClick={loadSaved} disabled={busy}>تحميل السجل</button></div>
      <div className="grid two">
        <label>رمز الوصول<input type="password" value={token} onChange={e => setToken(e.target.value)} placeholder="X-App-Token" /></label>
        <label>عنوان القضية<input value={matterTitle} onChange={e => setMatterTitle(e.target.value)} /></label>
        <label>معرف القضية<input value={matterId} onChange={e => setMatterId(e.target.value)} placeholder="يُنشأ تلقائيًا أو ألصقه هنا" /></label>
        <label>عنوان API<input value={apiBase} onChange={e => setApiBase(e.target.value)} /></label>
      </div>
      <div className="actions"><button className="primary" onClick={createMatter} disabled={busy}>إنشاء قضية</button><span className="muted">قاعدة البيانات تُحدد في الخادم عبر DATABASE_URL.</span></div>
    </section>

    <section className="panel">
      <div className="section-title"><div><span className="kicker">02</span><h2>الدور القانوني</h2></div><span className="muted">الأدوار المعتمدة فقط</span></div>
      <div className="roles">{ROLES.map(item => <button key={item.key} className={`role ${role === item.key ? 'selected' : ''}`} onClick={() => setRole(item.key)}><strong>{item.label}</strong><span>{item.description}</span></button>)}</div>
    </section>

    <section className="panel analysis-panel">
      <div className="section-title"><div><span className="kicker">03</span><h2>فحص النص القانوني</h2></div><span className="badge">نفي · إثبات · متحدث · سياق</span></div>
      <label>النص أو المقتطف القانوني<textarea value={text} onChange={e => setText(e.target.value)} placeholder="ألصق خطاب الإنهاء أو البريد أو محضر التسوية هنا..." /></label>
      <div className="actions"><button className="primary" onClick={analyze} disabled={busy}>{busy ? 'جارٍ التحليل...' : 'حلّل واحفظ'}</button><span className="muted">الدور الحالي: {role}</span></div>
    </section>

    {message && <div className="notice">{message}</div>}

    <section className="results-grid">
      <div className="panel"><div className="section-title"><div><span className="kicker">04</span><h2>الحقوق المحتملة</h2></div><span className="count">{savedRights.length}</span></div>
        {savedRights.length === 0 ? <Empty text="لم تُحفظ نتائج بعد." /> : <div className="rights">{savedRights.map(right => <RightCard key={right.id || right.right_key} right={right} onReview={review} />)}</div>}
      </div>
      <div className="panel"><div className="section-title"><div><span className="kicker">05</span><h2>الجمل المحللة</h2></div><span className="count">{statements.length}</span></div>
        {statements.length === 0 ? <Empty text="ستظهر هنا عبارات النفي والإثبات والمتحدث." /> : <div className="statements">{statements.map(item => <article className={`statement ${item.status?.includes('negated') ? 'negative' : ''}`} key={item.id}><div><b>{item.speaker || 'غير محدد'}</b><span className="status-chip">{item.status}</span></div><p>{item.text}</p><small>{item.negation_cue ? `أداة النفي: ${item.negation_cue} · ` : ''}الثقة: {Math.round((item.confidence || 0) * 100)}%</small></article>)}</div>}
      </div>
    </section>

    <footer>هذه واجهة تحليل واستخراج قابلة للمراجعة وليست رأيًا قانونيًا نهائيًا.</footer>
  </main>;
}

function RightCard({ right, onReview }) {
  const status = right.status || 'يحتاج تحقق';
  return <article className="right-card"><div className="right-head"><div><h3>{right.label || right.right_key}</h3><span className={`status-chip ${status.includes('نزاع') ? 'warning' : ''}`}>{status}</span></div><strong className="score">{right.final_confidence ? `${Math.round(right.final_confidence * 100)}%` : '—'}</strong></div><p>{right.reason || 'نتيجة مستخرجة من النص أو الكيان المنظم.'}</p><div className="meta"><span>مراجعة بشرية مطلوبة</span><span>{right.trigger_count || 0} محفز</span></div><div className="card-actions"><button onClick={() => onReview(right, 'مؤكد مبدئيًا')}>تأكيد</button><button onClick={() => onReview(right, 'يحتاج مستندًا إضافيًا')}>اطلب دليلًا</button><button onClick={() => onReview(right, 'غير منطبق')}>غير منطبق</button></div></article>;
}

function Empty({ text }) { return <div className="empty">{text}</div>; }

createRoot(document.getElementById('root')).render(<App />);
