import { useState, useEffect, createContext, useContext } from "react";

// ─── Auth Context ──────────────────────────────────────────────────────────────
const AuthContext = createContext(null);
const useAuth = () => useContext(AuthContext);

const API = "http://localhost:5000/api";
const apiFetch = async (path, opts = {}) => {
  const token = localStorage.getItem("pm_token");
  const res = await fetch(`${API}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...opts,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
};

// ─── Styles ────────────────────────────────────────────────────────────────────
const S = {
  app: { fontFamily: "'DM Sans', sans-serif", minHeight: "100vh", background: "#f4f6fb", color: "#1a1d2e" },
  nav: { background: "#1a1d2e", color: "#fff", padding: "0 2rem", display: "flex", alignItems: "center", height: 60, position: "sticky", top: 0, zIndex: 100, boxShadow: "0 2px 12px rgba(0,0,0,0.15)" },
  navBrand: { fontWeight: 700, fontSize: 18, color: "#fff", display: "flex", alignItems: "center", gap: 10 },
  navLinks: { display: "flex", gap: 4, marginLeft: 32, flex: 1 },
  navLink: (active) => ({ padding: "6px 14px", borderRadius: 8, cursor: "pointer", fontSize: 14, fontWeight: 500, background: active ? "rgba(255,255,255,0.12)" : "transparent", color: active ? "#fff" : "rgba(255,255,255,0.65)", border: "none", transition: "all 0.15s" }),
  badge: (color) => ({ background: color + "22", color, padding: "3px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600 }),
  card: { background: "#fff", borderRadius: 16, padding: "1.5rem", boxShadow: "0 2px 8px rgba(0,0,0,0.06)", marginBottom: 16 },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 24 },
  statCard: (color) => ({ background: color + "10", border: `1.5px solid ${color}33`, borderRadius: 12, padding: "1rem 1.25rem", borderLeft: `4px solid ${color}` }),
  btn: (variant = "primary") => ({
    padding: "9px 20px", borderRadius: 10, border: "none", cursor: "pointer", fontWeight: 600, fontSize: 14,
    background: variant === "primary" ? "#3d5af1" : variant === "success" ? "#0a8754" : variant === "danger" ? "#e53e3e" : "#f4f6fb",
    color: variant === "outline" ? "#3d5af1" : "#fff",
    border: variant === "outline" ? "1.5px solid #3d5af1" : "none",
    transition: "all 0.15s",
  }),
  input: {
    width: "100%",
    padding: "10px 14px",
    borderRadius: 10,
    border: "1.5px solid #1a1d2e",
    background: "#13191f",
    boxShadow: "0 2px 8px rgba(10, 7, 7, 0.08)",
    fontSize: 14,
    boxSizing: "border-box",
    outline: "none",
    fontFamily: "inherit"
  },
  label: { display: "block", marginBottom: 6, fontSize: 13, fontWeight: 600, color: "#4a5568" },
  formGroup: { marginBottom: 16 },
  scoreBar: (score, color) => ({ height: 8, borderRadius: 4, background: "#e2e8f0", overflow: "hidden", position: "relative", "::after": { content: '""', position: "absolute", left: 0, top: 0, height: "100%", width: `${score * 100}%`, background: color } }),
  tag: { display: "inline-flex", alignItems: "center", background: "#eef2ff", color: "#3d5af1", borderRadius: 6, padding: "3px 10px", fontSize: 12, fontWeight: 500, margin: "2px" },
  avatar: (size = 40) => ({ width: size, height: size, borderRadius: "50%", background: "linear-gradient(135deg, #3d5af1, #6c63ff)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 700, fontSize: size * 0.35, flexShrink: 0 }),
  page: { maxWidth: 1100, margin: "0 auto", padding: "2rem 1.5rem" },
  sectionTitle: { fontSize: 22, fontWeight: 700, marginBottom: 4, color: "#1a1d2e" },
  sectionSub: { color: "#090a0c", fontSize: 14, marginBottom: 24 },
  divider: { border: "none", borderTop: "1.5px solid #e2e8f0", margin: "1.5rem 0" },
  progressBar: (pct, color = "#3d5af1") => ({ height: 8, borderRadius: 4, overflow: "hidden", background: "#e2e8f0", position: "relative" }),
  alert: (type) => ({
    background: type === "success" ? "#f0fff4" : type === "error" ? "#fff5f5" : "#fffaf0",
    border: `1px solid ${type === "success" ? "#9ae6b4" : type === "error" ? "#feb2b2" : "#fbd38d"}`,
    borderRadius: 10, padding: "12px 16px", marginBottom: 16, fontSize: 14,
    color: type === "success" ? "#276749" : type === "error" ? "#c53030" : "#c05621"
  }),
};

// ─── Shared Components ─────────────────────────────────────────────────────────
const ScoreCircle = ({ score, size = 64 }) => {
  const pct = Math.round(score * 100);
  const color = pct >= 75 ? "#0a8754" : pct >= 50 ? "#d97706" : "#e53e3e";
  return (
    <div style={{ width: size, height: size, borderRadius: "50%", background: `conic-gradient(${color} ${pct * 3.6}deg, #e2e8f0 0deg)`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
      <div style={{ width: size - 10, height: size - 10, borderRadius: "50%", background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        <span style={{ fontSize: size * 0.22, fontWeight: 700, color, lineHeight: 1 }}>{pct}%</span>
      </div>
    </div>
  );
};

const ScoreBar = ({ label, value, color }) => (
  <div style={{ marginBottom: 10 }}>
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
      <span style={{ color: "#718096" }}>{label}</span>
      <span style={{ fontWeight: 600, color }}>{Math.round(value * 100)}%</span>
    </div>
    <div style={{ height: 6, borderRadius: 3, background: "#e2e8f0", overflow: "hidden" }}>
      <div style={{ height: "100%", width: `${value * 100}%`, background: color, borderRadius: 3, transition: "width 0.6s ease" }} />
    </div>
  </div>
);

const SkillTag = ({ skill }) => <span style={S.tag}>{skill}</span>;

const Spinner = () => (
  <div style={{ display: "flex", justifyContent: "center", padding: "3rem", color: "#3d5af1" }}>
    <div style={{ width: 36, height: 36, border: "3px solid #e2e8f0", borderTopColor: "#3d5af1", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
    <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
  </div>
);

const NotifDot = ({ count }) => count > 0 ? (
  <span style={{ background: "#e53e3e", color: "#fff", borderRadius: "50%", width: 18, height: 18, fontSize: 10, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center" }}>{count > 9 ? "9+" : count}</span>
) : null;

// ─── Login / Register Page ─────────────────────────────────────────────────────
const AuthPage = ({ onLogin, onCompanyReg }) => {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", full_name: "", student_id: "", university: "", degree_program: "", year_of_study: 3, gpa: "", skills: "", preferred_domains: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async () => {
    setLoading(true); setError("");
    try {
      const payload = mode === "login"
        ? { email: form.email, password: form.password }
        : { ...form, skills: JSON.stringify(form.skills.split(",").map(s => s.trim()).filter(Boolean)), preferred_domains: JSON.stringify(form.preferred_domains.split(",").map(s => s.trim()).filter(Boolean)) };
      const data = await apiFetch(`/auth/${mode}`, { method: "POST", body: JSON.stringify(payload) });
      localStorage.setItem("pm_token", data.token);
      onLogin(data.user || { id: null, role: "student" });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0f172a 0%, #1e293b 45%, #1c2a4a 100%)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
      position: "relative",
      overflow: "hidden"
    }}>
      <style>{`
        @keyframes gradientMove {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        @keyframes floatUp {
          0% { transform: translateY(0px); opacity: 0.6; }
          50% { transform: translateY(-18px); opacity: 1; }
          100% { transform: translateY(0px); opacity: 0.6; }
        }
        @keyframes popIn {
          from { transform: scale(0.92); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
      `}</style>

      <div style={{
        background: "rgba(255,255,255,0.94)",
        backdropFilter: "blur(12px)",
        borderRadius: 24,
        padding: "2.5rem",
        width: "100%",
        maxWidth: 460,
        boxShadow: "0 25px 70px rgba(0,0,0,0.35)",
        animation: "popIn 0.45s ease",
        border: "1px solid rgba(255,255,255,0.35)"
      }}>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{ fontSize: 42, marginBottom: 8, animation: "floatUp 2.8s ease-in-out infinite" }}>🎓</div>
          <h1 style={{ fontSize: 24, fontWeight: 900, color: "#1a1d2e", margin: 0 }}>PM Internship Scheme</h1>
          <p style={{ color: "#4a5568", fontSize: 13, marginTop: 6 }}>AI-Powered Smart Allocation Engine ✨</p>
        </div>

        <div style={{ display: "flex", background: "#eef2ff", borderRadius: 14, padding: 5, marginBottom: 24 }}>
          {["login", "register"].map(m => (
            <button key={m} onClick={() => setMode(m)} style={{
              flex: 1,
              padding: "10px 0",
              border: "none",
              borderRadius: 10,
              cursor: "pointer",
              fontWeight: 700,
              fontSize: 14,
              background: mode === m ? "linear-gradient(135deg, #3d5af1, #6c63ff)" : "transparent",
              color: mode === m ? "#fff" : "#1d232a",
              border: mode === m ? "none" : "1px solid #1a1d2e",
              boxShadow: mode === m ? "0 8px 18px rgba(13, 16, 31, 0.3)" : "none",
              transition: "all 0.25s"
            }}>
              {m === "login" ? "🔐 Sign In" : "📝 Register"}
            </button>
          ))}
        </div>

        {error && <div style={S.alert("error")}>{error}</div>}

        {mode === "login" ? (
          <>
            <div style={S.formGroup}><label style={S.label}>Email</label><input style={S.input} type="email" placeholder="student@university.edu.my" value={form.email} onChange={set("email")} /></div>
            <div style={S.formGroup}><label style={S.label}>Password</label><input style={S.input} type="password" placeholder="••••••••" value={form.password} onChange={set("password")} /></div>
            <p style={{ fontSize: 12, color: "#718096", marginBottom: 16 }}>Demo — Admin: admin@pm-internship.gov.my | Student: ahmad.zaki@student.um.edu.my</p>
          </>
        ) : (
          <div style={{ maxHeight: 340, overflowY: "auto", paddingRight: 4 }}>
            {[["Email", "email", "email"], ["Password", "password", "password"], ["Full Name", "full_name", "text"], ["Student ID", "student_id", "text"], ["University", "university", "text"], ["Degree Program", "degree_program", "text"]].map(([lbl, key, type]) => (
              <div key={key} style={S.formGroup}><label style={S.label}>{lbl}</label><input style={S.input} type={type} value={form[key]} onChange={set(key)} /></div>
            ))}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div style={S.formGroup}><label style={S.label}>Year of Study</label><select style={S.input} value={form.year_of_study} onChange={set("year_of_study")}>{[1, 2, 3, 4, 5].map(y => <option key={y} value={y}>Year {y}</option>)}</select></div>
              <div style={S.formGroup}><label style={S.label}>GPA (out of 4.0)</label><input style={S.input} type="number" step="0.01" min="0" max="4.0" value={form.gpa} onChange={set("gpa")} /></div>
            </div>
            <div style={S.formGroup}><label style={S.label}>Skills (comma-separated)</label><input style={S.input} placeholder="Python, SQL, Machine Learning" value={form.skills} onChange={set("skills")} /></div>
            <div style={S.formGroup}><label style={S.label}>Preferred Domains (comma-separated)</label><input style={S.input} placeholder="Technology, Finance" value={form.preferred_domains} onChange={set("preferred_domains")} /></div>
          </div>
        )}

        <button onClick={handleSubmit} disabled={loading} style={{
          ...S.btn("primary"),
          width: "100%",
          padding: "13px",
          fontSize: 15,
          marginTop: 8,
          background: "linear-gradient(135deg, #3d5af1, #6c63ff)",
          boxShadow: "0 10px 20px rgba(61,90,241,0.3)"
        }}>
          {loading ? "⏳ Please wait..." : mode === "login" ? "🚀 Sign In" : "✨ Create Account"}
        </button>

        <div style={{ textAlign: "center", marginTop: 16, paddingTop: 16, borderTop: "1px solid #e2e8f0" }}>
          <p style={{ fontSize: 13, color: "#718096", margin: "0 0 8px" }}>Are you a company wanting to offer internships?</p>
          <button onClick={onCompanyReg} style={{ ...S.btn("outline"), width: "100%", padding: 10 }}>🏢 Register Your Company</button>
        </div>
      </div>
    </div>
  );
};

// ─── Student Dashboard ─────────────────────────────────────────────────────────
const StudentDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/students/dashboard").then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (!data) return <p>Failed to load dashboard.</p>;
  const { profile, recommendations, allocation, stats } = data;
  const statusColor = { pending: "#d97706", recommended: "#3d5af1", allocated: "#0a8754", rejected: "#e53e3e" };

  return (
    <div style={S.page}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <div style={S.avatar(56)}>{profile.full_name?.[0] || "S"}</div>
        <div>
          <h1 style={{ ...S.sectionTitle, marginBottom: 2 }}>Welcome, {profile.full_name.split(" ")[0]}!</h1>
          <p style={{ color: "#718096", fontSize: 14, margin: 0 }}>{profile.university} · {profile.degree_program} · Year {profile.year_of_study}</p>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <span style={S.badge(statusColor[profile.allocation_status] || "#718096")}>
            {profile.allocation_status?.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div style={S.grid}>
        {[
          { label: "GPA", value: Number(profile.gpa || 0).toFixed(2), color: "#3d5af1", icon: "📊" },
          { label: "Recommendations", value: stats.rec_count, color: "#0a8754", icon: "🤖" },
          { label: "Status", value: profile.allocation_status, color: statusColor[profile.allocation_status], icon: "📋" },
          { label: "Profile", value: stats.profile_complete ? "Complete" : "Incomplete", color: stats.profile_complete ? "#0a8754" : "#d97706", icon: "👤" },
        ].map(s => (
          <div key={s.label} style={S.statCard(s.color)}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>{s.icon}</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 13, color: "#718096" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Allocation Banner */}
      {allocation && (
        <div style={{ ...S.card, background: "linear-gradient(135deg, #0a8754, #0d9e65)", color: "#fff", padding: "1.5rem 2rem" }}>
          <div style={{ fontSize: 28, marginBottom: 8 }}>🎉</div>
          <h3 style={{ margin: "0 0 4px", fontSize: 20 }}>Internship Confirmed!</h3>
          <p style={{ margin: "0 0 12px", opacity: 0.9 }}>{allocation.title} at {allocation.company_name}</p>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", fontSize: 13, opacity: 0.9 }}>
            <span>📍 {allocation.location}</span>
            <span>💰 RM{allocation.stipend}/month</span>
            <span>📅 Starts {allocation.start_date}</span>
            <span>✉️ {allocation.contact_email}</span>
          </div>
        </div>
      )}

      {/* AI Recommendations */}
      {recommendations.length > 0 && (
        <div>
          <h2 style={S.sectionTitle}>🤖 AI Recommendations</h2>
          <p style={S.sectionSub}>Top matches selected by the AI engine based on your skills, GPA, and preferences</p>
          {recommendations.map(rec => (
            <RecommendationCard key={rec.id} rec={rec} onRespond={() => apiFetch("/students/dashboard").then(setData)} />
          ))}
        </div>
      )}

      {/* Skills */}
      <div style={S.card}>
        <h3 style={{ marginTop: 0 }}>Your Skills</h3>
        <div>{(() => { try { return JSON.parse(profile.skills || "[]").map(s => <SkillTag key={s} skill={s} />); } catch { return null; } })()}</div>
        <hr style={S.divider} />
        <h3>Preferred Domains</h3>
        <div>{(() => { try { return JSON.parse(profile.preferred_domains || "[]").map(d => <span key={d} style={{ ...S.tag, background: "#f0fff4", color: "#0a8754" }}>{d}</span>); } catch { return null; } })()}</div>
      </div>
    </div>
  );
};

const RecommendationCard = ({ rec, onRespond }) => {
  const [responding, setResponding] = useState(false);
  const respond = async (choice) => {
    setResponding(true);
    try {
      await apiFetch(`/recommendations/${rec.id}/respond`, { method: "POST", body: JSON.stringify({ choice }) });
      onRespond();
    } catch (e) { console.error(e); }
    setResponding(false);
  };
  const reqSkills = (() => { try { return JSON.parse(rec.required_skills || "[]"); } catch { return []; } })();
  const rankColors = ["#3d5af1", "#0a8754", "#d97706"];

  return (
    <div style={{ ...S.card, borderLeft: `4px solid ${rankColors[rec.recommendation_rank - 1] || "#718096"}` }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
        <ScoreCircle score={rec.match_score || 0} size={70} />
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <span style={{ ...S.badge(rankColors[rec.recommendation_rank - 1]), fontSize: 11 }}>#{rec.recommendation_rank} Match</span>
            <span style={S.badge("#718096")}>{rec.domain}</span>
          </div>
          <h3 style={{ margin: "0 0 2px", fontSize: 17, fontWeight: 700 }}>{rec.title}</h3>
          <p style={{ margin: "0 0 8px", color: "#718096", fontSize: 14 }}>{rec.company_name} · {rec.location}</p>
          <div style={{ display: "flex", gap: 16, fontSize: 13, color: "#4a5568", marginBottom: 12 }}>
            <span>💰 RM{rec.stipend}/month</span>
            <span>📅 {rec.duration_weeks} weeks</span>
          </div>
          <div style={{ marginBottom: 12 }}>
            <ScoreBar label="Skill Match" value={rec.skill_similarity || rec.match_score * 0.7} color="#3d5af1" />
            <ScoreBar label="GPA Score" value={rec.gpa_score || rec.match_score * 0.5} color="#0a8754" />
            <ScoreBar label="Preference" value={rec.preference_score || rec.match_score * 0.8} color="#d97706" />
          </div>
          <div style={{ marginBottom: 12 }}>{reqSkills.slice(0, 5).map(s => <SkillTag key={s} skill={s} />)}</div>

          {rec.student_choice === "pending" && (
            <div style={{ display: "flex", gap: 8 }}>
              <button disabled={responding} onClick={() => respond("accepted")} style={S.btn("success")}>✓ Accept</button>
              <button disabled={responding} onClick={() => respond("declined")} style={S.btn("outline")}>✗ Decline</button>
            </div>
          )}
          {rec.student_choice !== "pending" && (
            <span style={S.badge(rec.student_choice === "accepted" ? "#0a8754" : "#718096")}>
              {rec.student_choice === "accepted" ? "✓ Accepted" : "✗ Declined"}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── Internship Explorer ───────────────────────────────────────────────────────
const InternshipExplorer = () => {
  const [internships, setInternships] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [domain, setDomain] = useState("");
  const [selected, setSelected] = useState(null);
  const DOMAINS = ["Technology", "Finance", "Engineering", "Energy", "Telecommunications", "Marketing", "Investment", "Aviation"];

  useEffect(() => {
    const q = new URLSearchParams({ search, ...(domain ? { domain } : {}) });
    apiFetch(`/internships/?${q}`).then(d => setInternships(d.internships || [])).finally(() => setLoading(false));
  }, [search, domain]);

  return (
    <div style={S.page}>
      <h1 style={S.sectionTitle}>Internship Listings</h1>
      <p style={S.sectionSub}>{internships.length} opportunities from top Malaysian companies</p>

      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <input style={{ ...S.input, maxWidth: 280 }} placeholder="🔍 Search positions..." value={search} onChange={e => setSearch(e.target.value)} />
        <select style={{ ...S.input, maxWidth: 180 }} value={domain} onChange={e => setDomain(e.target.value)}>
          <option value="">All Domains</option>
          {DOMAINS.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>

      {loading ? <Spinner /> : (
        <div style={{ display: "grid", gridTemplateColumns: selected ? "1fr 420px" : "1fr", gap: 20 }}>
          <div>
            {internships.map(i => (
              <div key={i.id} onClick={() => setSelected(i)} style={{ ...S.card, cursor: "pointer", borderLeft: selected?.id === i.id ? "4px solid #3d5af1" : "4px solid transparent", transition: "all 0.15s" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <h3 style={{ margin: "0 0 4px", fontSize: 16 }}>{i.title}</h3>
                    <p style={{ margin: "0 0 8px", color: "#718096", fontSize: 14 }}>{i.company_name} · {i.location}</p>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <span style={S.badge("#3d5af1")}>{i.domain}</span>
                      <span style={S.badge("#0a8754")}>RM{i.stipend}/mo</span>
                      <span style={S.badge(i.available_slots > 0 ? "#d97706" : "#e53e3e")}>{i.available_slots} slots</span>
                    </div>
                  </div>
                  <div style={{ textTransform: "none", fontSize: 12, color: "#718096" }}>
                    <div>Min GPA: {i.min_gpa}</div>
                    <div>{i.duration_weeks}w</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {selected && (
            <div style={{ ...S.card, position: "sticky", top: 80, alignSelf: "flex-start", height: "fit-content" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 18 }}>{selected.title}</h3>
                <button onClick={() => setSelected(null)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 18, color: "#718096" }}>✕</button>
              </div>
              <p style={{ color: "#3d5af1", fontWeight: 600, marginTop: 0 }}>{selected.company_name}</p>
              <div style={{ fontSize: 14, color: "#4a5568", lineHeight: 1.8 }}>
                <div>📍 {selected.location}</div>
                <div>💰 RM{selected.stipend}/month</div>
                <div>📅 {selected.duration_weeks} weeks</div>
                <div>🎓 Min GPA: {selected.min_gpa}</div>
                <div>👥 {selected.available_slots}/{selected.total_slots} slots available</div>
                {selected.start_date && <div>🗓 Start: {selected.start_date}</div>}
              </div>
              <hr style={S.divider} />
              <div>
                <strong style={{ fontSize: 13 }}>Required Skills</strong>
                <div style={{ marginTop: 6 }}>{(() => { try { return JSON.parse(selected.required_skills || "[]").map(s => <SkillTag key={s} skill={s} />); } catch { return null; } })()}</div>
              </div>
              {selected.description && <><hr style={S.divider} /><p style={{ fontSize: 14, color: "#4a5568", lineHeight: 1.7 }}>{selected.description}</p></>}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Profile Editor ────────────────────────────────────────────────────────────
const ProfileEditor = () => {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    apiFetch("/students/profile").then(p => { setProfile(p); setForm({ ...p, skills: (() => { try { return JSON.parse(p.skills || "[]").join(", "); } catch { return ""; } })(), preferred_domains: (() => { try { return JSON.parse(p.preferred_domains || "[]").join(", "); } catch { return ""; } })() }); });
  }, []);

  const save = async () => {
    setSaving(true); setMsg(null);
    try {
      await apiFetch("/students/profile", { method: "PUT", body: JSON.stringify({ ...form, skills: JSON.stringify(form.skills.split(",").map(s => s.trim()).filter(Boolean)), preferred_domains: JSON.stringify(form.preferred_domains.split(",").map(s => s.trim()).filter(Boolean)) }) });
      setMsg({ type: "success", text: "Profile updated! AI will re-rank your matches shortly." });
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    setSaving(false);
  };

  if (!profile) return <Spinner />;
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  return (
    <div style={S.page}>
      <h1 style={S.sectionTitle}>Edit Profile</h1>
      <p style={S.sectionSub}>Keep your profile updated for better AI match recommendations</p>

      {msg && <div style={S.alert(msg.type)}>{msg.text}</div>}

      <div style={{ ...S.card, maxWidth: 640 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {[["Full Name", "full_name", "text"], ["University", "university", "text"], ["Degree Program", "degree_program", "text"], ["Phone", "phone", "text"], ["State", "state", "text"]].map(([lbl, key, type]) => (
            <div key={key} style={S.formGroup}><label style={S.label}>{lbl}</label><input style={S.input} type={type} value={form[key] || ""} onChange={set(key)} /></div>
          ))}
          <div style={S.formGroup}>
            <label style={S.label}>Year of Study</label>
            <select style={S.input} value={form.year_of_study || 3} onChange={set("year_of_study")}>
              {[1, 2, 3, 4, 5].map(y => <option key={y} value={y}>Year {y}</option>)}
            </select>
          </div>
          <div style={S.formGroup}><label style={S.label}>GPA (0 – 4.0)</label><input style={S.input} type="number" step="0.01" min="0" max="4.0" value={form.gpa || ""} onChange={set("gpa")} /></div>
        </div>

        <div style={S.formGroup}><label style={S.label}>Skills (comma-separated)</label><input style={S.input} placeholder="Python, SQL, Machine Learning, React..." value={form.skills || ""} onChange={set("skills")} /><p style={{ fontSize: 12, color: "#718096", marginTop: 4 }}>These are used by the AI engine for skill-vector cosine similarity matching.</p></div>
        <div style={S.formGroup}><label style={S.label}>Preferred Domains (comma-separated)</label><input style={S.input} placeholder="Technology, Finance, Engineering..." value={form.preferred_domains || ""} onChange={set("preferred_domains")} /></div>

        <button onClick={save} disabled={saving} style={S.btn("primary")}>{saving ? "Saving..." : "Save Profile"}</button>
      </div>
    </div>
  );
};

// ─── APPROVELS Dashboard ──────────────────────────────────────────────
const CompanyApprovals = () => {
  const [companies, setCompanies] = useState([]);
  const [msg, setMsg] = useState(null);

  const load = () => {
    apiFetch("/admin/companies/pending")
      .then(d => setCompanies(d.companies || []))
      .catch(e => setMsg({ type: "error", text: e.message }));
  };

  useEffect(() => {
    load();
  }, []);

  const approve = async (id) => {
    try {
      const res = await apiFetch(`/admin/companies/${id}/approve`, { method: "POST" });
      setMsg({
        type: "success",
        text: `Approved! Email: ${res.login_email} | Password: ${res.temp_password}`
      });
      load();
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  };

  return (
    <div style={S.page}>
      <h1 style={S.sectionTitle}>🏢 Company Approvals</h1>
      <p style={S.sectionSub}>Approve company registration requests</p>

      {msg && <div style={S.alert(msg.type)}>{msg.text}</div>}

      {companies.length === 0 ? (
        <div style={S.card}>No pending company requests.</div>
      ) : (
        companies.map(c => (
          <div key={c.id} style={S.card}>
            <h3 style={{ marginTop: 0 }}>{c.name}</h3>
            <p>{c.sector} · {c.location}</p>
            <p>{c.contact_email}</p>
            <button onClick={() => approve(c.id)} style={S.btn("success")}>
              ✅ Approve Company
            </button>
          </div>
        ))
      )}
    </div>
  );
};

// ─── Admin Dashboard ───────────────────────────────────────────────────────────
const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(null);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    apiFetch("/admin/dashboard").then(setStats).finally(() => setLoading(false));
  }, []);

  const runEngine = async (action) => {
    setRunning(action); setMsg(null);
    try {
      const res = await apiFetch(`/${action === "match" ? "matching/run" : "allocations/run"}`, { method: "POST" });
      setMsg({ type: "success", text: action === "match" ? `✓ Matching complete! ${res.stats?.students_recommended} students received recommendations.` : `✓ Allocation complete! ${res.allocated_count} students placed.` });
      apiFetch("/admin/dashboard").then(setStats);
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    setRunning(null);
  };

  if (loading) return <Spinner />;
  if (!stats) return <p>Failed to load admin data.</p>;

  return (
    <div style={S.page}>
      <h1 style={S.sectionTitle}>Admin Dashboard</h1>
      <p style={S.sectionSub}>PM Internship AI Allocation Engine — System Overview</p>

      {msg && <div style={S.alert(msg.type)}>{msg.text}</div>}

      {/* Engine Controls */}
      <div style={{ ...S.card, background: "linear-gradient(135deg, #1a1d2e, #2d3561)", color: "#fff", marginBottom: 24 }}>
        <h3 style={{ margin: "0 0 8px", color: "#fff" }}>⚡ AI Engine Controls</h3>
        <p style={{ opacity: 0.75, fontSize: 14, margin: "0 0 16px" }}>Step 1: Run matching engine to compute scores. Step 2: Run allocation algorithm to place students.</p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <button disabled={running === "match"} onClick={() => runEngine("match")} style={{ ...S.btn("primary"), background: running === "match" ? "#555" : "#3d5af1" }}>
            {running === "match" ? "⏳ Running Matching..." : "🤖 Run AI Matching Engine"}
          </button>
          <button disabled={running === "alloc"} onClick={() => runEngine("alloc")} style={{ ...S.btn("success"), background: running === "alloc" ? "#555" : "#0a8754" }}>
            {running === "alloc" ? "⏳ Running Allocation..." : "🎯 Run Greedy Allocation"}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div style={S.grid}>
        {[
          { label: "Total Students", value: stats.total_students, color: "#3d5af1", icon: "👥" },
          { label: "Active Internships", value: stats.total_internships, color: "#0a8754", icon: "💼" },
          { label: "Allocated", value: stats.total_allocations, color: "#d97706", icon: "✅" },
          { label: "Fill Rate", value: `${stats.fill_rate}%`, color: "#e53e3e", icon: "📈" },
          { label: "Avg Match Score", value: `${(stats.avg_match_score * 100).toFixed(1)}%`, color: "#6c63ff", icon: "🎯" },
          { label: "Available Slots", value: stats.total_slots - stats.filled_slots, color: "#718096", icon: "📋" },
        ].map(s => (
          <div key={s.label} style={S.statCard(s.color)}>
            <div style={{ fontSize: 24 }}>{s.icon}</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 13, color: "#718096" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Status breakdown */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <div style={S.card}>
          <h3 style={{ marginTop: 0 }}>Student Status Breakdown</h3>
          {Object.entries(stats.by_status || {}).map(([status, count]) => {
            const colors = { pending: "#d97706", recommended: "#3d5af1", allocated: "#0a8754", rejected: "#e53e3e" };
            const pct = Math.round((count / stats.total_students) * 100);
            return (
              <div key={status} style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: 13 }}>
                  <span style={{ textTransform: "capitalize", fontWeight: 500 }}>{status}</span>
                  <span style={{ color: colors[status] || "#718096" }}>{count} ({pct}%)</span>
                </div>
                <div style={{ height: 8, borderRadius: 4, background: "#e2e8f0" }}>
                  <div style={{ height: "100%", width: `${pct}%`, background: colors[status] || "#718096", borderRadius: 4, transition: "width 0.5s" }} />
                </div>
              </div>
            );
          })}
        </div>
        <div style={S.card}>
          <h3 style={{ marginTop: 0 }}>Domain Distribution</h3>
          {(stats.domain_distribution || []).map(d => (
            <div key={d.domain} style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                <span>{d.domain}</span>
                <span style={{ color: "#718096" }}>{d.internships} postings · {d.slots} slots</span>
              </div>
              <div style={{ height: 6, borderRadius: 3, background: "#e2e8f0" }}>
                <div style={{ height: "100%", width: `${Math.min((d.slots / stats.total_slots) * 100, 100)}%`, background: "#3d5af1", borderRadius: 3 }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Allocations */}
      {stats.top_allocations?.length > 0 && (
        <div style={S.card}>
          <h3 style={{ marginTop: 0 }}>Top Allocations by Match Score</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e2e8f0" }}>
                {["Student", "Internship", "Company", "Match Score"].map(h => <th key={h} style={{ textAlign: "left", padding: "8px 12px", color: "#718096", fontWeight: 600, fontSize: 12 }}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {stats.top_allocations.map((a, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #f4f6fb" }}>
                  <td style={{ padding: "10px 12px", fontWeight: 500 }}>{a.full_name}</td>
                  <td style={{ padding: "10px 12px", color: "#718096" }}>{a.title}</td>
                  <td style={{ padding: "10px 12px", color: "#718096" }}>{a.company}</td>
                  <td style={{ padding: "10px 12px" }}><span style={S.badge(a.allocation_score >= 0.75 ? "#0a8754" : "#d97706")}>{(a.allocation_score * 100).toFixed(1)}%</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Audit Log */}
      {stats.recent_activity?.length > 0 && (
        <div style={S.card}>
          <h3 style={{ marginTop: 0 }}>Recent Activity Log</h3>
          {stats.recent_activity.map((a, i) => (
            <div key={i} style={{ display: "flex", gap: 12, padding: "10px 0", borderBottom: i < stats.recent_activity.length - 1 ? "1px solid #f4f6fb" : "none" }}>
              <span style={{ fontSize: 12, color: "#718096", minWidth: 140 }}>{new Date(a.created_at).toLocaleString()}</span>
              <span style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", color: "#3d5af1", minWidth: 120 }}>{a.action?.replace("_", " ")}</span>
              <span style={{ fontSize: 12, color: "#4a5568" }}>{a.details}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Allocations Table (Admin View) ───────────────────────────────────────────
const AllocationsTable = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/allocations/")
      .then(d => setData(d.allocations || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  return (
    <div style={S.page}>
      <h1 style={S.sectionTitle}>Final Allocations List</h1>
      <p style={S.sectionSub}>Official student-to-company placements records</p>
      <div style={S.card}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #e2e8f0" }}>
              {["Student", "University", "Assigned Role", "Company", "Stipend", "Status"].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "12px", color: "#718096", fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr><td colSpan="6" style={{ padding: "20px", textAlign: "center", color: "#718096" }}>No allocations generated yet.</td></tr>
            ) : (
              data.map(row => (
                <tr key={row.id} style={{ borderBottom: "1px solid #f4f6fb" }}>
                  <td style={{ padding: "12px", fontWeight: 500 }}>{row.student_name || row.full_name || "—"}</td>
                  <td style={{ padding: "12px", color: "#4a5568" }}>{row.university}</td>
                  <td style={{ padding: "12px", fontWeight: 500 }}>{row.internship_title || row.title || "—"}</td>
                  <td style={{ padding: "12px", color: "#3d5af1", fontWeight: 600 }}>{row.company_name || row.company || "—"}</td>
                  <td style={{ padding: "12px" }}>RM {row.stipend}</td>
                  <td style={{ padding: "12px" }}><span style={S.badge("#0a8754")}>CONFIRMED</span></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── Company Portal Template ──────────────────────────────────────────────────
const CompanyPortal = () => {
  return (
    <div style={S.page}>
      <h1 style={S.sectionTitle}>Company Portal</h1>
      <p style={S.sectionSub}>Manage postings and view AI recommended candidates</p>
      <div style={S.card}>
        <h3>Welcome Partner Component</h3>
        <p style={{ color: "#4a5568" }}>This module allows verified corporate entities to submit requests for industrial trainee placement cohorts.</p>
      </div>
    </div>
  );
};

const CompanyRegister = ({ onBack }) => {
  const [form, setForm] = useState({
    name: "",
    sector: "",
    location: "",
    contact_email: "",
    website: "",
    description: ""
  });
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async () => {
    setLoading(true);
    setMsg(null);
    try {
      const res = await apiFetch("/companies/register", {
        method: "POST",
        body: JSON.stringify(form)
      });
      setMsg({ type: "success", text: res.message || "Company registration submitted!" });
      setTimeout(() => onBack(), 1500);
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
    setLoading(false);
  };

  return (
    <div style={S.page}>
      <div style={{ ...S.card, maxWidth: 620, margin: "2rem auto" }}>
        <h1 style={S.sectionTitle}>🏢 Company Registration</h1>
        <p style={S.sectionSub}>Submit your company details for admin approval.</p>

        {msg && <div style={S.alert(msg.type)}>{msg.text}</div>}

        <div style={S.formGroup}>
          <label style={S.label}>Company Name</label>
          <input style={S.input} value={form.name} onChange={set("name")} />
        </div>

        <div style={S.formGroup}>
          <label style={S.label}>Sector</label>
          <input style={S.input} placeholder="Technology, Finance, Marketing..." value={form.sector} onChange={set("sector")} />
        </div>

        <div style={S.formGroup}>
          <label style={S.label}>Location</label>
          <input style={S.input} value={form.location} onChange={set("location")} />
        </div>

        <div style={S.formGroup}>
          <label style={S.label}>Contact Email</label>
          <input style={S.input} type="email" value={form.contact_email} onChange={set("contact_email")} />
        </div>

        <div style={S.formGroup}>
          <label style={S.label}>Website</label>
          <input style={S.input} value={form.website} onChange={set("website")} />
        </div>

        <div style={S.formGroup}>
          <label style={S.label}>Description</label>
          <textarea style={{ ...S.input, minHeight: 90 }} value={form.description} onChange={set("description")} />
        </div>

        <button onClick={submit} disabled={loading} style={{ ...S.btn("primary"), width: "100%" }}>
          {loading ? "Submitting..." : "Submit for Approval"}
        </button>
      </div>
    </div>
  );
};

// ─── Notifications Screen ─────────────────────────────────────────────────────
const NotificationsScreen = ({ onClear }) => {
  const [notifs, setNotifs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/notifications/")
      .then(d => setNotifs(d.notifications || []))
      .catch(() => setNotifs([{ id: 1, text: "System notification channel loaded.", created_at: new Date() }]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={S.page}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={S.sectionTitle}>Alert Center</h1>
        <button onClick={onClear} style={S.btn("outline")}>Mark All Read</button>
      </div>
      <p style={S.sectionSub}>System logs and active updates</p>
      {loading ? <Spinner /> : (
        notifs.map(n => (
          <div key={n.id} style={S.card}>
            <div style={{ fontSize: 12, color: "#718096", marginBottom: 4 }}>{new Date(n.created_at).toLocaleString()}</div>
            <div style={{ fontSize: 20, marginBottom: 6 }}>
              🔔✨🎉
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>
              {n.title || "Notification"}
            </div>
            <div style={{ fontSize: 14 }}>
              {n.message || n.text || "No message"}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

// ─── Main App Router ──────────────────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState("dashboard");
  const [unread, setUnread] = useState(0);

  const fetchUnread = () => {
    apiFetch("/notifications/")
      .then(d => setUnread(d.unread_count || 0))
      .catch(() => setUnread(0));
  };

  useEffect(() => {
    const token = localStorage.getItem("pm_token");
    if (token) {
      apiFetch("/auth/me")
        .then(res => {
          setUser(res.user);
          setPage(res.user.role === "admin" ? "admin" : res.user.role === "company" ? "company" : "dashboard");
          fetchUnread();
        })
        .catch(() => localStorage.removeItem("pm_token"));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("pm_token");
    setUser(null);
    setPage("dashboard");
  };

  if (!user) {
    if (page === "companyRegister") {
      return <CompanyRegister onBack={() => setPage("dashboard")} />;
    }

    return (
      <AuthPage
        onLogin={(u) => {
          setUser(u);
          setPage(u.role === "admin" ? "admin" : u.role === "company" ? "company" : "dashboard");
          fetchUnread();
        }}
        onCompanyReg={() => setPage("companyRegister")}
      />
    );
  }

  const isAdmin = user.role === "admin";
  const isCompany = user.role === "company";

  const navItems = isAdmin
    ? [
      { id: "admin", label: "Dashboard" },
      { id: "approvals", label: "Approvals" },
      { id: "allocations", label: "Placements" },
      { id: "explorer", label: "Jobs" }
    ] : isCompany
      ? [{ id: "company", label: "Company Portal" }, { id: "explorer", label: "Browse Listings" }]
      : [{ id: "dashboard", label: "My Dashboard" }, { id: "explorer", label: "Find Internships" }, { id: "profile", label: "My Profile" }];

  const renderPage = () => {
    if (page === "notifications") return <NotificationsScreen onClear={() => setUnread(0)} />;

    if (page === "companyRegister") return <CompanyRegister />;

    if (isAdmin) {
      switch (page) {
        case "admin": return <AdminDashboard />;
        case "allocations": return <AllocationsTable />;
        case "explorer": return <InternshipExplorer />;
        default: return <AdminDashboard />;
        case "approvals": return <CompanyApprovals />;
      }
    } else if (isCompany) {
      switch (page) {
        case "company": return <CompanyPortal />;
        case "explorer": return <InternshipExplorer />;
        default: return <CompanyPortal />;
      }
    } else {
      switch (page) {
        case "dashboard": return <StudentDashboard />;
        case "explorer": return <InternshipExplorer />;
        case "profile": return <ProfileEditor />;
        default: return <StudentDashboard />;
      }
    }
  };

  return (
    <AuthContext.Provider value={{ user, handleLogout }}>
      <div style={S.app}>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap" />

        <nav style={S.nav}>
          <div style={S.navBrand}>
            <span style={{ fontSize: 22 }}>🎓</span>
            <span>PM Internship</span>
            {isAdmin && <span style={{ ...S.badge("#d97706"), fontSize: 10, marginLeft: 4 }}>ADMIN</span>}
            {isCompany && <span style={{ ...S.badge("#0a8754"), fontSize: 10, marginLeft: 4 }}>COMPANY</span>}
          </div>
          <div style={S.navLinks}>
            {navItems.map(n => (
              <button key={n.id} onClick={() => setPage(n.id)} style={S.navLink(page === n.id)}>{n.label}</button>
            ))}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button onClick={() => { setPage("notifications"); setUnread(0); }} style={{ ...S.navLink(page === "notifications"), display: "flex", alignItems: "center", gap: 6, background: "none" }}>
              🔔 <NotifDot count={unread} />
            </button>
            <span style={{ fontSize: 14, color: "rgb(255, 255, 255)" }}>{user.full_name || user.email}</span>
            <button onClick={handleLogout} style={{
              padding: "8px 16px",
              borderRadius: 10,
              border: "1.5px solid #f87171",
              background: "rgba(136, 181, 197, 0.08)",
              color: "#fff",
              cursor: "pointer",
              fontWeight: 600,
              transition: "all 0.3s ease",
              boxShadow: "0 4px 12px rgba(241, 85, 85, 0.25)"
            }}>Logout</button>
          </div>
        </nav>
        {renderPage()}
      </div>
    </AuthContext.Provider>
  );
}