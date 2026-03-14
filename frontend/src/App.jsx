import { useState, useEffect, useRef } from "react";
import axios from "axios";
import jsPDF from "jspdf";
import {
  Search, BarChart3, Target, PenTool, ShieldCheck,
  Zap, ArrowRight, Clock, Building2, Users,
  ChevronDown, CheckCircle2, Loader2, Sparkles,
  FileText, Globe, TrendingUp, AlertCircle, Play,
  LayoutDashboard, Settings, Bell, ChevronRight,
  Layers, Award, Rocket, Download, History,
  X, CheckCheck, Info, AlertTriangle, Lightbulb,
  BarChart, Star, BookOpen, Cpu, Menu, RefreshCw
} from "lucide-react";
import "./App.css";

/* ─────────────────────────────────────────
   DATA
───────────────────────────────────────── */
const AGENTS = [
  { key:"researcher", Icon:Search,      label:"Research",  role:"Market Intelligence",     desc:"Deep market research, competitor analysis, trend identification and data gathering.", color:"#06b6d4" },
  { key:"analyst",    Icon:BarChart3,   label:"Analysis",  role:"Strategic Intelligence",  desc:"SWOT analysis, competitive landscape mapping and opportunity identification.",         color:"#818cf8" },
  { key:"strategist", Icon:Target,      label:"Strategy",  role:"Campaign Architecture",   desc:"Full marketing strategy with channels, messaging, budget allocation and roadmap.",     color:"#f59e0b" },
  { key:"writer",     Icon:PenTool,     label:"Report",    role:"Executive Documentation", desc:"Polished board-ready report combining all intelligence into one clear document.",       color:"#10b981" },
  { key:"critic",     Icon:ShieldCheck, label:"Review",    role:"Quality Assurance",       desc:"Critical review, quality scoring and actionable improvement recommendations.",         color:"#f43f5e" },
];

const EXAMPLES = [
  { topic:"Nike social media strategy for Gen Z",        industry:"Sportswear",  audience:"Ages 16–25" },
  { topic:"Launch a SaaS product for remote teams",      industry:"Technology",  audience:"Startup founders" },
  { topic:"Electric vehicle marketing in Africa",        industry:"Automotive",  audience:"Urban professionals" },
  { topic:"Food delivery app expansion strategy",        industry:"Food Tech",   audience:"Busy urban dwellers" },
  { topic:"Fintech app targeting university students",   industry:"Finance",     audience:"Students 18–24" },
  { topic:"Luxury hotel brand awareness campaign",       industry:"Hospitality", audience:"High-net-worth travelers" },
];

const HOW_IT_WORKS = [
  { Icon:FileText,  title:"Enter your topic",  desc:"Describe your product, company or strategy goal in plain language." },
  { Icon:Layers,    title:"Pipeline runs",      desc:"Five intelligent stages process your request, each building on the last." },
  { Icon:Award,     title:"Get your report",    desc:"Receive a structured, professional strategy report ready to present." },
];

/* ─────────────────────────────────────────
   HELPERS
───────────────────────────────────────── */
function parseReport(text) {
  if (!text) return [];
  const sections = [];
  let current = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const isHeading =
      /^#{1,3}\s/.test(line) ||
      /^\*\*[^*]+\*\*\s*$/.test(line) ||
      /^[A-Z][A-Z\s&:,]{5,}$/.test(line) ||
      /^\d+\.\s+[A-Z]/.test(line);
    if (isHeading) {
      if (current) sections.push(current);
      current = {
        heading: line.replace(/^#+\s*/,"").replace(/\*\*/g,"").replace(/^\d+\.\s*/,""),
        bullets: [],
      };
    } else if (current) {
      const clean = line.replace(/^[-*•]\s*/,"").replace(/\*\*/g,"").replace(/\*/g,"").replace(/^#+\s*/,"");
      if (clean) current.bullets.push(clean);
    } else {
      current = { heading:"", bullets:[line.replace(/\*\*/g,"").replace(/\*/g,"")] };
    }
  }
  if (current) sections.push(current);
  return sections.filter(s => s.bullets.length > 0);
}

function ReportView({ text }) {
  const sections = parseReport(text);
  if (!sections.length) return <p className="empty-report">No output generated.</p>;
  return (
    <div className="report-view">
      {sections.map((s,i) => (
        <div key={i} className="report-section">
          {s.heading && <div className="report-heading">{s.heading}</div>}
          <ul className="report-bullets">
            {s.bullets.map((b,j) => <li key={j} className="report-bullet">{b}</li>)}
          </ul>
        </div>
      ))}
    </div>
  );
}

/* ─────────────────────────────────────────
   TOAST SYSTEM
───────────────────────────────────────── */
function ToastContainer({ toasts, remove }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span className="toast-icon">
            {t.type==="success" && <CheckCheck size={15}/>}
            {t.type==="error"   && <AlertTriangle size={15}/>}
            {t.type==="info"    && <Info size={15}/>}
            {t.type==="loading" && <Loader2 size={15} className="spin"/>}
          </span>
          <span className="toast-msg">{t.msg}</span>
          <button className="toast-close" onClick={()=>remove(t.id)}><X size={13}/></button>
        </div>
      ))}
    </div>
  );
}

function useToast() {
  const [toasts, setToasts] = useState([]);
  const add = (msg, type="info", duration=3500) => {
    const id = Date.now();
    setToasts(p => [...p, { id, msg, type }]);
    if (type !== "loading") setTimeout(() => remove(id), duration);
    return id;
  };
  const remove = (id) => setToasts(p => p.filter(t => t.id !== id));
  const update = (id, msg, type="success") => {
    setToasts(p => p.map(t => t.id===id ? {...t, msg, type} : t));
    setTimeout(() => remove(id), 3000);
  };
  return { toasts, add, remove, update };
}

/* ─────────────────────────────────────────
   PDF EXPORT
───────────────────────────────────────── */
function exportPDF(result) {
  const doc = new jsPDF({ unit:"pt", format:"a4" });
  const W = doc.internal.pageSize.getWidth();
  const margin = 48;
  let y = margin;

  const addText = (text, size, bold, color=[30,30,60]) => {
    doc.setFontSize(size);
    doc.setFont("helvetica", bold ? "bold" : "normal");
    doc.setTextColor(...color);
    const lines = doc.splitTextToSize(text, W - margin*2);
    lines.forEach(line => {
      if (y > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
      doc.text(line, margin, y);
      y += size * 1.45;
    });
  };

  const addDivider = () => {
    if (y > doc.internal.pageSize.getHeight() - margin) { doc.addPage(); y = margin; }
    doc.setDrawColor(220,220,240);
    doc.line(margin, y, W-margin, y);
    y += 14;
  };

  // Cover
  doc.setFillColor(15,15,35);
  doc.rect(0, 0, W, 180, "F");
  doc.setFontSize(28); doc.setFont("helvetica","bold"); doc.setTextColor(255,255,255);
  doc.text("Strategy Intelligence Report", margin, 70);
  doc.setFontSize(13); doc.setFont("helvetica","normal"); doc.setTextColor(160,160,210);
  doc.text(result.topic, margin, 96);
  doc.setFontSize(10); doc.setTextColor(100,100,150);
  doc.text(`Industry: ${result.industry}  |  Audience: ${result.audience}  |  Generated in ${result.time_taken}`, margin, 118);
  y = 210;

  // Stage outputs
  AGENTS.forEach(agent => {
    const text = result.agents?.[agent.key];
    if (!text) return;
    addText(agent.label + " — " + agent.role, 13, true, [40,40,100]);
    y += 4;
    addDivider();
    parseReport(text).forEach(sec => {
      if (sec.heading) addText(sec.heading, 11, true, [60,60,110]);
      sec.bullets.forEach(b => addText("• " + b, 10, false, [70,70,100]));
      y += 6;
    });
    y += 10;
  });

  // Final report
  doc.addPage(); y = margin;
  addText("Executive Strategy Report", 16, true, [30,30,80]);
  y += 6; addDivider();
  parseReport(result.final_report).forEach(sec => {
    if (sec.heading) addText(sec.heading, 12, true, [50,50,110]);
    sec.bullets.forEach(b => addText("• " + b, 10, false, [70,70,100]));
    y += 8;
  });

  doc.save(`strategy-report-${result.topic.slice(0,30).replace(/\s+/g,"-").toLowerCase()}.pdf`);
}

/* ─────────────────────────────────────────
   MAIN APP
───────────────────────────────────────── */
export default function App() {
  const [topic,    setTopic]    = useState("");
  const [industry, setIndustry] = useState("");
  const [audience, setAudience] = useState("");
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [active,   setActive]   = useState("");
  const [step,     setStep]     = useState(0);
  const [error,    setError]    = useState("");
  const [expanded, setExpanded] = useState(null);
  const [page,     setPage]     = useState("home");
  const [history,  setHistory]  = useState(() => {
    try { return JSON.parse(localStorage.getItem("strategy_history")||"[]"); } catch { return []; }
  });
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { toasts, add: addToast, remove: removeToast, update: updateToast } = useToast();

  const saveToHistory = (r) => {
    const entry = { id: Date.now(), topic: r.topic, industry: r.industry, audience: r.audience, time_taken: r.time_taken, date: new Date().toLocaleDateString(), result: r };
    const updated = [entry, ...history].slice(0, 10);
    setHistory(updated);
    localStorage.setItem("strategy_history", JSON.stringify(updated));
  };

  const runAgents = async () => {
    if (!topic.trim()) { addToast("Please enter a topic first.", "error"); return; }
    setLoading(true); setResult(null); setError(""); setStep(0); setExpanded(null);
    setPage("workspace");
    const tid = addToast("Pipeline starting...", "loading");

    for (let i = 0; i < AGENTS.length; i++) {
      setActive(AGENTS[i].label); setStep(i+1);
      updateToast(tid, `Running: ${AGENTS[i].label} stage (${i+1}/${AGENTS.length})`, "loading");
      await new Promise(r => setTimeout(r, 900));
    }

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/run-agent/", {
        topic, industry: industry||"General", audience: audience||"General public",
      });
      setResult(res.data);
      saveToHistory(res.data);
      updateToast(tid, `Report ready in ${res.data.time_taken}!`, "success");
    } catch (err) {
      const msg = err.response?.data?.error || "Something went wrong.";
      setError(msg);
      updateToast(tid, "Pipeline failed. Check your API key.", "error");
    }
    setActive(""); setLoading(false);
  };

  const handleExample = (ex) => {
    setTopic(ex.topic); setIndustry(ex.industry); setAudience(ex.audience);
    setPage("workspace");
    addToast("Example loaded — click Generate to run!", "info");
  };

  const handleExport = () => {
    if (!result) return;
    addToast("Generating PDF...", "loading");
    setTimeout(() => {
      try { exportPDF(result); addToast("PDF downloaded!", "success"); }
      catch { addToast("PDF export failed.", "error"); }
    }, 300);
  };

  const loadHistory = (entry) => {
    setResult(entry.result); setTopic(entry.topic);
    setIndustry(entry.industry); setAudience(entry.audience);
    setPage("workspace");
    addToast("Report loaded from history.", "info");
  };

  const progress = loading ? Math.round((step/AGENTS.length)*100) : result ? 100 : 0;

  return (
    <div className={`root ${sidebarOpen?"sidebar-open":"sidebar-closed"}`}>
      <ToastContainer toasts={toasts} remove={removeToast}/>

      {/* ── SIDEBAR ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-mark"><Rocket size={16}/></div>
          <span className="logo-text">StrategyAI</span>
          <button className="sidebar-toggle" onClick={()=>setSidebarOpen(false)}><X size={15}/></button>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-label">Workspace</div>
          <button className={`nav-item ${page==="home"?"active":""}`} onClick={()=>setPage("home")}>
            <LayoutDashboard size={15}/><span>Dashboard</span>
          </button>
          <button className={`nav-item ${page==="workspace"?"active":""}`} onClick={()=>setPage("workspace")}>
            <Layers size={15}/><span>Strategy Builder</span>
            {result && <span className="nav-dot"/>}
          </button>
          <button className={`nav-item ${page==="history"?"active":""}`} onClick={()=>setPage("history")}>
            <History size={15}/><span>History</span>
            {history.length>0 && <span className="nav-count">{history.length}</span>}
          </button>

          <div className="nav-label" style={{marginTop:20}}>Pipeline</div>
          {AGENTS.map((agent,i) => {
            const isActive = active===agent.label && loading;
            const isPast   = result || (loading && i < step-1);
            return (
              <div key={agent.key} className={`pipeline-step ${isActive?"running":""} ${isPast?"done":""}`}>
                <div className="pipeline-dot" style={{background:agent.color}}/>
                <span>{agent.label}</span>
                {isActive && <Loader2 size={11} className="spin"/>}
                {isPast   && <CheckCircle2 size={11} style={{color:agent.color}}/>}
              </div>
            );
          })}
        </nav>

        <div className="sidebar-foot">
          <button className="nav-item"><Settings size={15}/><span>Settings</span></button>
          <div className="sidebar-user">
            <div className="user-avatar">U</div>
            <div><span className="user-name">User</span><span className="user-plan">Pro Plan</span></div>
          </div>
        </div>
      </aside>

      {/* ── MAIN ── */}
      <div className="main-wrapper">
        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-left">
            {!sidebarOpen && (
              <button className="icon-btn" onClick={()=>setSidebarOpen(true)}><Menu size={16}/></button>
            )}
            <div className="breadcrumb">
              <span>Platform</span><ChevronRight size={13}/>
              <span className="bc-active">
                {page==="home"?"Dashboard":page==="history"?"History":"Strategy Builder"}
              </span>
            </div>
          </div>
          <div className="topbar-right">
            <button className="icon-btn"><Bell size={16}/></button>
            {loading && <div className="status-chip running"><Loader2 size={12} className="spin"/>Stage {step}/{AGENTS.length}</div>}
            {result && !loading && <div className="status-chip done"><CheckCircle2 size={12}/>Done in {result.time_taken}</div>}
            {result && !loading && (
              <button className="btn-export" onClick={handleExport}>
                <Download size={14}/> Export PDF
              </button>
            )}
          </div>
        </header>

        <main className="main">

          {/* ══ HOME ══ */}
          {page==="home" && (
            <div className="page-home">
              <div className="home-hero">
                <div className="hero-eyebrow"><Sparkles size={13}/> Intelligent Strategy Platform</div>
                <h1 className="hero-h1">Turn any idea into a<br/><span className="gradient-text">complete strategy</span></h1>
                <p className="hero-p">Our intelligent pipeline researches your market, analyzes competitors, designs your strategy, writes the report, and reviews quality — all in minutes.</p>
                <div className="hero-actions">
                  <button className="btn-primary" onClick={()=>setPage("workspace")}><Play size={15}/> Start Building</button>
                  <button className="btn-ghost">See how it works <ArrowRight size={14}/></button>
                </div>
              </div>

              {/* Stats */}
              <div className="stats-strip">
                {[["5","Pipeline Stages"],["Fast","Processing"],["SWOT","Analysis"],["800+","Word Reports"],["PDF","Export"]].map(([v,l])=>(
                  <div key={l} className="stat-item"><div className="stat-val">{v}</div><div className="stat-lbl">{l}</div></div>
                ))}
              </div>

              {/* How it works */}
              <div className="hiw-section">
                <div className="section-label">How it works</div>
                <div className="hiw-grid">
                  {HOW_IT_WORKS.map((h,i)=>(
                    <div key={i} className="hiw-card">
                      <div className="hiw-num">0{i+1}</div>
                      <div className="hiw-icon"><h.Icon size={20}/></div>
                      <div className="hiw-title">{h.title}</div>
                      <div className="hiw-desc">{h.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Pipeline stages */}
              <div className="stages-section">
                <div className="section-label">Pipeline stages</div>
                <div className="stages-grid">
                  {AGENTS.map((a,i)=>(
                    <div key={a.key} className="stage-card" style={{"--c":a.color}}>
                      <div className="stage-top">
                        <div className="stage-icon"><a.Icon size={18}/></div>
                        <div className="stage-num">Stage {i+1}</div>
                      </div>
                      <div className="stage-label">{a.label}</div>
                      <div className="stage-role">{a.role}</div>
                      <div className="stage-desc">{a.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Example topics */}
              <div className="examples-section">
                <div className="section-label">Try an example</div>
                <div className="examples-grid">
                  {EXAMPLES.map((ex,i)=>(
                    <button key={i} className="example-card" onClick={()=>handleExample(ex)}>
                      <div className="ex-topic"><Lightbulb size={14}/>{ex.topic}</div>
                      <div className="ex-meta"><span>{ex.industry}</span><span>{ex.audience}</span></div>
                      <div className="ex-cta">Use this example <ChevronRight size={12}/></div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ══ WORKSPACE ══ */}
          {page==="workspace" && (
            <div className="page-workspace">
              {!result && (
                <div className="workspace-split">
                  <div className="ws-left">
                    <div className="ws-card">
                      <div className="ws-card-head"><Play size={15}/><span>Configure your strategy</span></div>

                      <div className="field-block">
                        <label className="field-label"><Zap size={12}/> Strategy topic <span className="req-dot"/></label>
                        <input className="field-input large" value={topic} onChange={e=>setTopic(e.target.value)} onKeyDown={e=>e.key==="Enter"&&runAgents()} placeholder="e.g. Launch a fintech app for Gen Z users in East Africa" disabled={loading}/>
                      </div>

                      <div className="field-row">
                        <div className="field-block">
                          <label className="field-label"><Building2 size={12}/> Industry</label>
                          <input className="field-input" value={industry} onChange={e=>setIndustry(e.target.value)} placeholder="e.g. Fintech" disabled={loading}/>
                        </div>
                        <div className="field-block">
                          <label className="field-label"><Users size={12}/> Target audience</label>
                          <input className="field-input" value={audience} onChange={e=>setAudience(e.target.value)} placeholder="e.g. Ages 18–30" disabled={loading}/>
                        </div>
                      </div>

                      {loading && (
                        <div className="progress-wrap">
                          <div className="progress-header">
                            <span className="progress-stage">Running: {active} stage</span>
                            <span className="progress-pct">{progress}%</span>
                          </div>
                          <div className="progress-track"><div className="progress-fill" style={{width:`${progress}%`}}/></div>
                        </div>
                      )}

                      {error && <div className="error-banner"><AlertCircle size={15}/><span>{error}</span></div>}

                      <button className="btn-run" onClick={runAgents} disabled={loading||!topic.trim()}>
                        {loading
                          ? <><Loader2 size={15} className="spin"/>Processing stage {step} of {AGENTS.length}...</>
                          : <><Rocket size={15}/>Generate Strategy Report</>}
                      </button>
                    </div>

                    {/* Quick examples inside workspace */}
                    <div className="ws-examples">
                      <div className="ws-ex-label"><Lightbulb size={13}/> Quick examples</div>
                      <div className="ws-ex-list">
                        {EXAMPLES.slice(0,3).map((ex,i)=>(
                          <button key={i} className="ws-ex-btn" onClick={()=>handleExample(ex)}>{ex.topic}</button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="ws-right">
                    <div className="pipeline-preview">
                      <div className="pp-label">Pipeline preview</div>
                      {AGENTS.map((a,i)=>{
                        const isActive=active===a.label&&loading;
                        const isPast=loading&&i<step-1;
                        return (
                          <div key={a.key} className={`pp-step ${isActive?"active":""} ${isPast?"past":""}`} style={{"--c":a.color}}>
                            <div className="pp-icon"><a.Icon size={15}/></div>
                            <div className="pp-info"><div className="pp-name">{a.label}</div><div className="pp-role">{a.role}</div></div>
                            <div className="pp-state">
                              {isActive && <Loader2 size={13} className="spin" style={{color:a.color}}/>}
                              {isPast   && <CheckCircle2 size={13} style={{color:a.color}}/>}
                              {!isActive&&!isPast && <div className="pp-idle"/>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {result && (
                <div className="results-wrap">
                  <div className="results-topbar">
                    <div className="results-title">
                      <CheckCircle2 size={18} className="success-icon"/>
                      <div>
                        <div className="rt-main">Strategy Report Ready</div>
                        <div className="rt-sub">{result.topic} · {result.industry} · {result.time_taken}</div>
                      </div>
                    </div>
                    <div className="results-actions">
                      <button className="btn-export-lg" onClick={handleExport}><Download size={14}/>Export PDF</button>
                      <button className="btn-new" onClick={()=>{setResult(null);setTopic("");setIndustry("");setAudience("");}}>
                        <RefreshCw size={13}/>New Strategy
                      </button>
                    </div>
                  </div>

                  <div className="stage-accordions">
                    <div className="sa-label">Stage outputs</div>
                    {AGENTS.map(agent=>(
                      <div key={agent.key} className={`accordion ${expanded===agent.key?"open":""}`} style={{"--c":agent.color}}>
                        <button className="accordion-head" onClick={()=>setExpanded(expanded===agent.key?null:agent.key)}>
                          <div className="acc-left">
                            <div className="acc-icon"><agent.Icon size={16}/></div>
                            <div><div className="acc-title">{agent.label}</div><div className="acc-sub">{agent.role}</div></div>
                          </div>
                          <div className="acc-right">
                            <span className="acc-badge">Complete</span>
                            <ChevronDown size={15} className={`chevron ${expanded===agent.key?"open":""}`}/>
                          </div>
                        </button>
                        {expanded===agent.key && (
                          <div className="accordion-body"><ReportView text={result.agents?.[agent.key]}/></div>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="final-card">
                    <div className="final-card-head">
                      <div className="final-title"><FileText size={18}/>Executive Strategy Report</div>
                      <div className="final-meta"><Clock size={12}/>{result.time_taken}<span className="sep"/><TrendingUp size={12}/>{result.audience}</div>
                    </div>
                    <div className="final-body"><ReportView text={result.final_report}/></div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ══ HISTORY ══ */}
          {page==="history" && (
            <div className="page-history">
              <div className="history-head">
                <div>
                  <h2 className="history-title">Report History</h2>
                  <p className="history-sub">Your last {history.length} generated strategy reports</p>
                </div>
                {history.length>0 && (
                  <button className="btn-ghost-sm" onClick={()=>{setHistory([]);localStorage.removeItem("strategy_history");addToast("History cleared","info");}}>
                    <X size={13}/> Clear all
                  </button>
                )}
              </div>

              {history.length===0 ? (
                <div className="empty-state">
                  <History size={40} className="empty-icon"/>
                  <div className="empty-title">No reports yet</div>
                  <div className="empty-sub">Generate your first strategy report to see it here.</div>
                  <button className="btn-primary" onClick={()=>setPage("workspace")}><Play size={14}/> Start Building</button>
                </div>
              ) : (
                <div className="history-grid">
                  {history.map(entry=>(
                    <div key={entry.id} className="history-card">
                      <div className="hc-top">
                        <div className="hc-topic">{entry.topic}</div>
                        <div className="hc-date">{entry.date}</div>
                      </div>
                      <div className="hc-meta">
                        <span><Building2 size={11}/>{entry.industry}</span>
                        <span><Users size={11}/>{entry.audience}</span>
                        <span><Clock size={11}/>{entry.time_taken}</span>
                      </div>
                      <div className="hc-actions">
                        <button className="hc-btn primary" onClick={()=>loadHistory(entry)}><FileText size={13}/>View Report</button>
                        <button className="hc-btn" onClick={()=>{exportPDF(entry.result);addToast("PDF downloaded!","success");}}><Download size={13}/>PDF</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
