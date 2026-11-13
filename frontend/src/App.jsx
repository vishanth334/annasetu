import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import api, { errorMessage } from "./api/client";
import MapView from "./components/MapView";

const green = "#1B7F3B";
const demoAccounts = [
  ["Kitchen admin", "kitchen@annasetu.demo"],
  ["NGO", "ngo@annasetu.demo"],
  ["Super admin", "admin@annasetu.demo"],
];

function App() {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("annasetu_user")); } catch { return null; }
  });
  const [toast, setToast] = useState("");
  const [notifications, setNotifications] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();

  function signIn(data) {
    localStorage.setItem("annasetu_token", data.access_token);
    localStorage.setItem("annasetu_user", JSON.stringify(data.user));
    setUser(data.user);
    navigate(data.user.role === "NGO" ? "/ngo" : "/dashboard");
  }
  function signOut() {
    localStorage.removeItem("annasetu_token");
    localStorage.removeItem("annasetu_user");
    setUser(null);
    navigate("/");
  }
  useEffect(() => {
    if (!user) return;
    api.get("/surplus/notifications")
      .then((res) => setNotifications(res.data))
      .catch((error) => flash(errorMessage(error)));
  }, [user, location.pathname]);
  function flash(message) {
    setToast(message);
    window.setTimeout(() => setToast(""), 3800);
  }
  async function markNotificationRead(id) {
    try {
      await api.post(`/surplus/notifications/${id}/read`);
      setNotifications((current) => current.map((item) => item.id === id ? { ...item, is_read: true } : item));
    } catch (error) { flash(errorMessage(error)); }
  }

  return (
    <div className="min-h-screen">
      <Navbar user={user} notifications={notifications} onSignOut={signOut} onRead={markNotificationRead} />
      {toast && <div className="toast">{toast}</div>}
      <Routes>
        <Route path="/" element={<Landing user={user} />} />
        <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <AuthPage mode="login" onSuccess={signIn} flash={flash} />} />
        <Route path="/register" element={user ? <Navigate to="/dashboard" /> : <AuthPage mode="register" onSuccess={signIn} flash={flash} />} />
        <Route path="/dashboard" element={!user ? <Navigate to="/login" /> : user.role === "NGO" ? <Navigate to="/ngo" /> : user.role === "SUPER_ADMIN" ? <SuperAdminDashboard flash={flash} /> : <KitchenDashboard user={user} flash={flash} />} />
        <Route path="/inventory" element={user?.role === "KITCHEN_ADMIN" ? <InventoryPage flash={flash} /> : <Navigate to="/login" />} />
        <Route path="/ngo" element={user?.role === "NGO" ? <NgoDashboard flash={flash} /> : <Navigate to="/login" />} />
        <Route path="/routes" element={user?.role === "NGO" ? <RoutePlanner flash={flash} /> : <Navigate to="/login" />} />
        <Route path="/analytics" element={user ? <AnalyticsPage flash={flash} /> : <Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
      <footer className="footer">AnnaSetu · Turning surplus into shared nourishment</footer>
    </div>
  );
}

function Navbar({ user, notifications, onSignOut, onRead }) {
  const [open, setOpen] = useState(false);
  const unread = notifications.filter((item) => !item.is_read).length;
  return (
    <header className="navbar">
      <Link to="/" className="brand"><span className="brand-icon">A</span> anna<span>setu</span></Link>
      <nav className="nav-links">
        {user ? <>
          {user.role === "KITCHEN_ADMIN" && <><Link to="/dashboard">Dashboard</Link><Link to="/inventory">Inventory</Link></>}
          {user.role === "SUPER_ADMIN" && <Link to="/dashboard">Overview</Link>}
          {user.role === "NGO" && <><Link to="/ngo">Surplus</Link><Link to="/routes">Route planner</Link></>}
          {user.role !== "NGO" && <Link to="/analytics">Impact & ESG</Link>}
          {user.role === "NGO" && <Link to="/analytics">Impact</Link>}
          <div className="relative">
            <button className="icon-btn" aria-label="Notifications" onClick={() => setOpen(!open)}>🔔{unread > 0 && <span className="notification-count">{unread}</span>}</button>
            {open && <div className="notification-menu">
              <strong>Notifications</strong>
              {notifications.length ? notifications.slice(0, 5).map((n) => <button type="button" key={n.id} className={`notification-item ${n.is_read ? "read" : ""}`} onClick={() => onRead(n.id)}>{n.message}</button>) : <p className="muted">You’re all caught up.</p>}
            </div>}
          </div>
          <span className="user-name">{user.name}</span><button className="button button-outline small" onClick={onSignOut}>Sign out</button>
        </> : <><Link to="/#how">How it works</Link><Link to="/login" className="button button-outline small">Log in</Link><Link to="/register" className="button button-primary small">Get started</Link></>}
      </nav>
    </header>
  );
}

function Landing({ user }) {
  return <main>
    <section className="hero">
      <div className="hero-copy">
        <div className="eyebrow"><span className="pulse-dot" /> LESS WASTE. MORE NOURISHMENT.</div>
        <h1>Good food deserves<br /><span>a second chance.</span></h1>
        <p>AnnaSetu helps institutional kitchens predict demand, protect food quality, and get safe surplus to nearby communities.</p>
        <div className="hero-actions"><Link className="button button-primary" to={user ? "/dashboard" : "/register"}>{user ? "Open dashboard" : "Join the food loop"} <span>→</span></Link><a className="text-link" href="#how">Explore the platform ↓</a></div>
        <div className="hero-proof"><div className="avatar-stack"><i>🍲</i><i>🤝</i><i>🌱</i></div><span>Built for kitchens and community partners</span></div>
      </div>
      <div className="hero-art">
        <div className="orbit orbit-one"></div><div className="orbit orbit-two"></div>
        <div className="food-plate"><span>🥗</span></div>
        <div className="floating-card card-top"><span className="mini-icon">↗</span><div><b>Food saved</b><small>Every meal matters</small></div></div>
        <div className="floating-card card-bottom"><span className="mini-icon leaf">♧</span><div><b>Local impact</b><small>From kitchen to community</small></div></div>
      </div>
    </section>
    <section className="problem-section"><div className="section-kicker">THE CHALLENGE</div><h2>Every day, good food gets left behind.</h2><p>Uncertain meal demand and disconnected donation networks create avoidable waste. AnnaSetu connects the dots so fresh food reaches people who need it.</p><div className="problem-stats"><div><strong>1/3</strong><span>of food produced is wasted globally</span></div><div><strong>8–10%</strong><span>of global emissions come from food loss</span></div><div><strong>1 platform</strong><span>to make surplus count</span></div></div></section>
    <section className="modules-section" id="how"><div className="section-kicker">HOW ANNASETU HELPS</div><h2>One connected food loop.</h2><div className="module-grid">
      {[["01", "Predict", "Plan the right portions with data-backed meal demand forecasts.", "◷"], ["02", "Detect", "Monitor shelf life and flag food that needs attention.", "⌕"], ["03", "Redistribute", "Match surplus with nearby NGOs and organise pickups.", "↗"], ["04", "Report", "Track food saved, meals shared, and emissions avoided.", "▤"]].map((x) => <article className="module-card" key={x[1]}><span className="module-icon">{x[3]}</span><span className="module-number">{x[0]}</span><h3>{x[1]}</h3><p>{x[2]}</p></article>)}
    </div></section>
    <section className="cta-band"><div><h2>Make surplus a starting point.</h2><p>Bring your kitchen or community organisation into the loop.</p></div><Link to="/register" className="button button-white">Create a free account →</Link></section>
  </main>;
}

function AuthPage({ mode, onSuccess, flash }) {
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "KITCHEN_ADMIN", organization_name: "", latitude: "12.9716", longitude: "77.5946" });
  const [busy, setBusy] = useState(false);
  const isRegister = mode === "register";
  async function submit(event) {
    event.preventDefault(); setBusy(true);
    try {
      const { data } = await api.post(`/auth/${mode}`, isRegister ? { ...form, latitude: Number(form.latitude), longitude: Number(form.longitude) } : { email: form.email, password: form.password });
      onSuccess(data);
    } catch (error) { flash(errorMessage(error)); } finally { setBusy(false); }
  }
  return <main className="auth-wrap"><div className="auth-card">
    <div className="section-kicker">{isRegister ? "JOIN ANNASETU" : "WELCOME BACK"}</div><h1>{isRegister ? "Start making an impact." : "Good to see you again."}</h1><p className="muted">{isRegister ? "Create your kitchen or NGO workspace." : "Sign in to your AnnaSetu workspace."}</p>
    <form onSubmit={submit} className="form-grid">
      {isRegister && <><label>Your name<input required minLength="2" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
      <label>I am a<select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option value="KITCHEN_ADMIN">Kitchen admin</option><option value="NGO">NGO partner</option></select></label>
      <label className="full">Organization name<input value={form.organization_name} onChange={(e) => setForm({ ...form, organization_name: e.target.value })} placeholder="Your kitchen or NGO" /></label>
      <label>Latitude<input type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} /></label><label>Longitude<input type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} /></label></>}
      <label className="full">Email<input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
      <label className="full">Password<input type="password" minLength="8" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
      <button className="button button-primary full" disabled={busy}>{busy ? "Please wait…" : isRegister ? "Create account →" : "Sign in →"}</button>
    </form>
    {!isRegister && <div className="demo-box"><b>Demo sign-ins</b>{demoAccounts.map(([label, email]) => <div key={email}><span>{label}</span><button type="button" onClick={() => setForm({ ...form, email, password: "demo1234" })}>{email}</button></div>)}<small>All demo accounts use password <code>demo1234</code>.</small></div>}
    <p className="auth-switch">{isRegister ? "Already registered?" : "New to AnnaSetu?"} <Link to={isRegister ? "/login" : "/register"}>{isRegister ? "Sign in" : "Create an account"}</Link></p>
  </div></main>;
}

function PageHeader({ eyebrow, title, description, action }) {
  return <div className="page-header"><div><div className="section-kicker">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}
function Stat({ icon, label, value, note }) {
  return <article className="stat-card"><span className="stat-icon">{icon}</span><div><span>{label}</span><strong>{value}</strong><small>{note}</small></div></article>;
}
function KitchenDashboard({ user, flash }) {
  const [forecast, setForecast] = useState([]);
  const [stats, setStats] = useState({});
  const [inventory, setInventory] = useState([]);
  const [surplusForm, setSurplusForm] = useState({ item: "Prepared lunch", quantity_kg: "12", safe_until: "", latitude: user.latitude || 12.9716, longitude: user.longitude || 77.5946 });
  const [recordForm, setRecordForm] = useState({ date: new Date().toISOString().slice(0, 16), meals_prepared: "", meals_consumed: "", is_holiday: false, is_exam_day: false, weather_temp: "24" });
  async function load() {
    const [forecastResult, analyticsResult, inventoryResult] = await Promise.allSettled([
      api.post("/forecast"), api.get("/analytics"), api.get("/inventory"),
    ]);
    if (forecastResult.status === "fulfilled") setForecast(forecastResult.value.data.forecast);
    else if (forecastResult.reason.response?.status === 422) setForecast([]);
    else flash(errorMessage(forecastResult.reason));
    if (analyticsResult.status === "fulfilled") setStats(analyticsResult.value.data);
    else flash(errorMessage(analyticsResult.reason));
    if (inventoryResult.status === "fulfilled") setInventory(inventoryResult.value.data);
    else flash(errorMessage(inventoryResult.reason));
  }
  useEffect(() => { load(); }, []);
  async function postSurplus(e) {
    e.preventDefault();
    try {
      await api.post("/surplus", { ...surplusForm, quantity_kg: Number(surplusForm.quantity_kg), safe_until: new Date(surplusForm.safe_until).toISOString(), latitude: Number(surplusForm.latitude), longitude: Number(surplusForm.longitude) });
      flash("Surplus posted. Nearby NGO partners have been notified.");
      setSurplusForm({ ...surplusForm, safe_until: "" });
      load();
    } catch (error) { flash(errorMessage(error)); }
  }
  async function saveRecord(e) {
    e.preventDefault();
    try {
      await api.post("/forecast/records", { ...recordForm, date: new Date(recordForm.date).toISOString(), meals_prepared: Number(recordForm.meals_prepared), meals_consumed: Number(recordForm.meals_consumed), weather_temp: Number(recordForm.weather_temp) });
      flash("Daily meal record saved; refreshing forecast."); load();
    } catch (error) { flash(errorMessage(error)); }
  }
  return <main className="page-shell">
    <PageHeader eyebrow="KITCHEN WORKSPACE" title={`Good day, ${user.name.split(" ")[0]}.`} description="Here’s your food planning and community impact at a glance." action={<Link className="button button-primary" to="/inventory">＋ Manage inventory</Link>} />
    <div className="stat-grid"><Stat icon="♧" label="Food saved" value={`${stats.food_saved_kg || 0} kg`} note="Delivered surplus" /><Stat icon="♡" label="Meals donated" value={stats.meals_donated || 0} note="Estimated at 3 meals/kg" /><Stat icon="↗" label="CO₂ avoided" value={`${stats.co2_avoided_kg || 0} kg`} note="Based on configurable factor" /><Stat icon="◷" label="Items to use soon" value={inventory.filter((x) => x.status === "USE_SOON" || x.status === "EXPIRING").length} note="Check expiry alerts" /></div>
    <div className="content-grid">
      <section className="panel wide"><div className="panel-heading"><div><div className="section-kicker">NEXT 7 DAYS</div><h2>Meal demand forecast</h2></div><span className="model-pill">Random Forest</span></div>{forecast.length ? <div className="chart"><ResponsiveContainer><LineChart data={forecast}><CartesianGrid stroke="#e9f0e9" strokeDasharray="3 3" /><XAxis dataKey="date" tickFormatter={(x) => x.slice(5)} /><YAxis /><Tooltip /><Line type="monotone" dataKey="predicted_meals" name="Predicted demand" stroke={green} strokeWidth={3} /><Line type="monotone" dataKey="recommended_to_cook" name="Recommended to cook" stroke="#E8A23A" strokeDasharray="5 5" /></LineChart></ResponsiveContainer></div> : <EmptyState text="Add at least 7 daily records or seed demo data to generate your forecast." />}</section>
      <section className="panel"><div className="panel-heading"><div><div className="section-kicker">FOOD SAFETY</div><h2>Expiry watch</h2></div><Link className="text-link" to="/inventory">View all →</Link></div>{inventory.length ? inventory.slice(0, 5).map((item) => <div className="expiry-row" key={item.id}><div><b>{item.name}</b><small>{item.quantity_kg} kg · {item.category}</small></div><StatusBadge status={item.status} /></div>) : <EmptyState text="No inventory items yet. Add food to start monitoring shelf life." />}</section>
      <section className="panel full-panel"><div className="panel-heading"><div><div className="section-kicker">SHARE YOUR SURPLUS</div><h2>Post food for pickup</h2></div><span className="mini-icon">↗</span></div><form className="surplus-form" onSubmit={postSurplus}><label>Food item<input required value={surplusForm.item} onChange={(e) => setSurplusForm({ ...surplusForm, item: e.target.value })} /></label><label>Quantity (kg)<input type="number" min="0.1" step="0.1" required value={surplusForm.quantity_kg} onChange={(e) => setSurplusForm({ ...surplusForm, quantity_kg: e.target.value })} /></label><label>Safe until<input type="datetime-local" required value={surplusForm.safe_until} onChange={(e) => setSurplusForm({ ...surplusForm, safe_until: e.target.value })} /></label><button className="button button-primary">Notify nearby NGOs →</button></form></section>
      <section className="panel full-panel"><div className="panel-heading"><div><div className="section-kicker">DAILY OPERATIONS</div><h2>Log meal production</h2></div></div><form className="surplus-form record-form" onSubmit={saveRecord}><label>Date<input type="datetime-local" required value={recordForm.date} onChange={(e) => setRecordForm({ ...recordForm, date: e.target.value })} /></label><label>Meals prepared<input type="number" min="0" required value={recordForm.meals_prepared} onChange={(e) => setRecordForm({ ...recordForm, meals_prepared: e.target.value })} /></label><label>Meals consumed<input type="number" min="0" required value={recordForm.meals_consumed} onChange={(e) => setRecordForm({ ...recordForm, meals_consumed: e.target.value })} /></label><label>Temperature (°C)<input type="number" step="0.1" value={recordForm.weather_temp} onChange={(e) => setRecordForm({ ...recordForm, weather_temp: e.target.value })} /></label><label className="check-field"><input type="checkbox" checked={recordForm.is_holiday} onChange={(e) => setRecordForm({ ...recordForm, is_holiday: e.target.checked })} /> Holiday</label><label className="check-field"><input type="checkbox" checked={recordForm.is_exam_day} onChange={(e) => setRecordForm({ ...recordForm, is_exam_day: e.target.checked })} /> Exam day</label><button className="button button-primary">Save daily record</button></form></section>
    </div>
  </main>;
}

function SuperAdminDashboard({ flash }) {
  const [overview, setOverview] = useState(null);
  useEffect(() => { api.get("/admin/overview").then((res) => setOverview(res.data)).catch((error) => flash(errorMessage(error))); }, []);
  const impact = overview?.impact || {};
  return <main className="page-shell">
    <PageHeader eyebrow="PLATFORM ADMINISTRATION" title="AnnaSetu overview" description="Monitor registered food partners and impact across the platform." action={<Link className="button button-primary" to="/analytics">View ESG analytics →</Link>} />
    <div className="stat-grid"><Stat icon="♧" label="Food saved" value={`${impact.food_saved_kg || 0} kg`} note="Delivered platform-wide" /><Stat icon="♡" label="Meals donated" value={impact.meals_donated || 0} note="Estimated at 3 meals/kg" /><Stat icon="↗" label="CO₂ avoided" value={`${impact.co2_avoided_kg || 0} kg`} note="Estimated platform-wide" /><Stat icon="⌂" label="Partner organizations" value={(overview?.kitchens?.length || 0) + (overview?.ngos?.length || 0)} note={`${overview?.kitchens?.length || 0} kitchens · ${overview?.ngos?.length || 0} NGOs`} /></div>
    <div className="content-grid"><section className="panel"><div className="panel-heading"><div><div className="section-kicker">KITCHEN PARTNERS</div><h2>Registered kitchens</h2></div></div>{overview?.kitchens?.length ? overview.kitchens.map((item) => <div className="expiry-row" key={item.id}><div><b>{item.name}</b><small>{item.latitude.toFixed(3)}, {item.longitude.toFixed(3)}</small></div><StatusBadge status="FRESH" /></div>) : <EmptyState text="No kitchens registered yet." />}</section><section className="panel"><div className="panel-heading"><div><div className="section-kicker">COMMUNITY PARTNERS</div><h2>Registered NGOs</h2></div></div>{overview?.ngos?.length ? overview.ngos.map((item) => <div className="expiry-row" key={item.id}><div><b>{item.name}</b><small>{item.latitude.toFixed(3)}, {item.longitude.toFixed(3)}</small></div><span className="model-pill">Partner</span></div>) : <EmptyState text="No NGOs registered yet." />}</section></div>
  </main>;
}

function StatusBadge({ status }) {
  return <span className={`status-badge status-${(status || "").toLowerCase()}`}>{(status || "UNKNOWN").replace("_", " ")}</span>;
}
function EmptyState({ text }) { return <div className="empty-state"><span>✳</span><p>{text}</p></div>; }

function estimatedTravelMinutes(distanceKm) {
  return Math.max(1, Math.ceil(Number(distanceKm || 0) / 25 * 60));
}

function safeWindowRemaining(safeUntil) {
  const remainingMinutes = Math.max(0, Math.floor((new Date(safeUntil).getTime() - Date.now()) / 60000));
  if (!remainingMinutes) return "Safe window ended";
  const hours = Math.floor(remainingMinutes / 60);
  const minutes = remainingMinutes % 60;
  return hours ? `${hours}h ${minutes}m remaining` : `${minutes}m remaining`;
}

function InventoryPage({ flash }) {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ name: "", category: "Prepared food", quantity_kg: "", prepared_time: new Date().toISOString().slice(0, 16), shelf_life_hours: "12", storage_temp: "4" });
  const [quality, setQuality] = useState(null);
  async function load() { try { setItems((await api.get("/inventory")).data); } catch (error) { flash(errorMessage(error)); } }
  useEffect(() => { load(); }, []);
  async function submit(e) {
    e.preventDefault();
    try {
      await api.post("/inventory", { ...form, quantity_kg: Number(form.quantity_kg), shelf_life_hours: Number(form.shelf_life_hours), storage_temp: Number(form.storage_temp), prepared_time: new Date(form.prepared_time).toISOString() });
      flash("Inventory item saved."); setForm({ ...form, name: "", quantity_kg: "" }); load();
    } catch (error) { flash(errorMessage(error)); }
  }
  async function remove(id) { try { await api.delete(`/inventory/${id}`); load(); } catch (error) { flash(errorMessage(error)); } }
  async function checkImage(event) {
    const file = event.target.files?.[0]; if (!file) return;
    const data = new FormData(); data.append("image", file);
    try { setQuality((await api.post("/quality-check", data)).data); } catch (error) { flash(errorMessage(error)); }
  }
  return <main className="page-shell"><PageHeader eyebrow="KITCHEN WORKSPACE" title="Inventory & food safety" description="Keep an eye on shelf life and log what’s in your kitchen." />
    <div className="inventory-layout"><section className="panel"><div className="panel-heading"><div><div className="section-kicker">IN YOUR KITCHEN</div><h2>Inventory items</h2></div></div>
      {items.length ? <div className="table-scroll"><table><thead><tr><th>Food</th><th>Quantity</th><th>Prepared</th><th>Status</th><th></th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><b>{item.name}</b><small>{item.category}</small></td><td>{item.quantity_kg} kg</td><td>{new Date(item.prepared_time).toLocaleString()}</td><td><StatusBadge status={item.status} /></td><td><button className="delete-btn" onClick={() => remove(item.id)}>Remove</button></td></tr>)}</tbody></table></div> : <EmptyState text="Nothing in inventory yet. Add your first food item." />}</section>
      <aside className="side-stack"><section className="panel"><div className="section-kicker">ADD FOOD</div><h2>New inventory item</h2><form className="stack-form" onSubmit={submit}><label>Food name<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label><label>Category<input required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></label><div className="two-fields"><label>Quantity (kg)<input type="number" min="0.1" step="0.1" required value={form.quantity_kg} onChange={(e) => setForm({ ...form, quantity_kg: e.target.value })} /></label><label>Shelf life (hours)<input type="number" min="0.1" step="0.5" required value={form.shelf_life_hours} onChange={(e) => setForm({ ...form, shelf_life_hours: e.target.value })} /></label></div><label>Prepared at<input type="datetime-local" required value={form.prepared_time} onChange={(e) => setForm({ ...form, prepared_time: e.target.value })} /></label><label>Storage temperature (°C)<input type="number" step="0.1" value={form.storage_temp} onChange={(e) => setForm({ ...form, storage_temp: e.target.value })} /></label><button className="button button-primary">Save item</button></form></section>
      <section className="panel quality-panel"><div className="section-kicker">DEMO AI QUALITY CHECK</div><h2>Check a food photo</h2><p>Mock freshness estimate for demo only. A trained model is not connected.</p><label className="upload-button">＋ Upload an image<input type="file" accept="image/*" onChange={checkImage} /></label>{quality && <div className="quality-result"><StatusBadge status={quality.label} /><span>{Math.round(quality.confidence * 100)}% demo confidence</span></div>}</section></aside>
    </div>
  </main>;
}

function NgoDashboard({ flash }) {
  const [listings, setListings] = useState([]);
  const [, refreshSafeWindows] = useState(0);
  async function load() { try { setListings((await api.get("/surplus")).data); } catch (error) { flash(errorMessage(error)); } }
  useEffect(() => { load(); }, []);
  useEffect(() => {
    const timer = window.setInterval(() => refreshSafeWindows((current) => current + 1), 60_000);
    return () => window.clearInterval(timer);
  }, []);
  async function decide(id, action) { try { await api.post(`/surplus/${id}/${action}`); flash(action === "accept" ? "Pickup accepted and kitchen notified." : "Listing declined."); load(); } catch (error) { flash(errorMessage(error)); } }
  async function status(id, value) { try { await api.post(`/surplus/${id}/status?status=${value}`); flash(`Pickup marked ${value.toLowerCase().replace("_", " ")}.`); load(); } catch (error) { flash(errorMessage(error)); } }
  const points = listings.map((x) => ({ ...x, latitude: x.latitude, longitude: x.longitude }));
  return <main className="page-shell"><PageHeader eyebrow="COMMUNITY PARTNER" title="Good food is nearby." description="Find safe surplus from local kitchens and coordinate a pickup." action={<Link to="/routes" className="button button-primary">Plan pickup route →</Link>} />
    <div className="ngo-layout"><section className="panel map-panel"><div className="panel-heading"><div><div className="section-kicker">NEARBY ON THE MAP</div><h2>Available food</h2></div><span className="model-pill">{listings.length} listings</span></div><MapView points={points} /> <div className="map-legend"><span>● Your nearby listings · distances ranked by proximity</span></div></section>
      <section className="panel listing-panel"><div className="panel-heading"><div><div className="section-kicker">AVAILABLE & ASSIGNED</div><h2>Surplus listings</h2></div></div>{listings.length ? listings.map((item) => <article className="listing-card" key={item.id}><div className="listing-top"><div><h3>{item.item}</h3><p>{item.kitchen_name}</p></div><span className="distance-chip">{item.distance_km} km away</span></div><div className="listing-meta"><span>♧ {item.quantity_kg} kg</span><span>Safe until {new Date(item.safe_until).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span></div><div className="listing-travel"><span>◷ ~{estimatedTravelMinutes(item.distance_km)} min travel</span><span>{safeWindowRemaining(item.safe_until)}</span></div><div className="listing-actions"><a className="button button-outline small" href={`https://www.google.com/maps/dir/?api=1&destination=${item.latitude},${item.longitude}&travelmode=driving`} target="_blank" rel="noreferrer">Get directions ↗</a>{item.status === "POSTED" ? <><button className="button button-primary small" onClick={() => decide(item.id, "accept")}>Accept pickup</button><button className="button button-outline small" onClick={() => decide(item.id, "reject")}>Decline</button></> : <><StatusBadge status={item.status} />{item.status === "ACCEPTED" && <button className="button button-primary small" onClick={() => status(item.id, "PICKED_UP")}>Mark picked up</button>}{item.status === "PICKED_UP" && <button className="button button-primary small" onClick={() => status(item.id, "DELIVERED")}>Mark delivered</button>}</>}</div></article>) : <EmptyState text="No new surplus nearby. New listings will show up here." />}<p className="listing-estimate-note">Travel times are rough estimates at 25 km/h from straight-line distance; traffic and road routes may differ. Use directions for current road travel information.</p></section></div>
  </main>;
}

function RoutePlanner({ flash }) {
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  async function plan() { setLoading(true); try { setRoute((await api.post("/routes/plan", {})).data); } catch (error) { flash(errorMessage(error)); } finally { setLoading(false); } }
  useEffect(() => { plan(); }, []);
  const points = useMemo(() => route?.stops || [], [route]);
  return <main className="page-shell"><PageHeader eyebrow="PICKUP LOGISTICS" title="Your pickup route" description="A practical stop order, planned from your NGO location." action={<button className="button button-primary" onClick={plan} disabled={loading}>{loading ? "Planning…" : "↻ Recalculate route"}</button>} />
    <div className="route-stats"><Stat icon="⌖" label="Total distance" value={`${route?.total_distance_km || 0} km`} note="Straight-line route estimate" /><Stat icon="◷" label="Estimated time" value={`${route?.eta_minutes || 0} min`} note="Approx. travel + 10 min per stop" /><Stat icon="↗" label="Pickup stops" value={route?.stops?.length || 0} note="Accepted listings" /></div>
    <div className="route-layout"><section className="panel"><div className="panel-heading"><div><div className="section-kicker">OPTIMISED ORDER</div><h2>Pickup sequence</h2></div></div>{route?.stops?.length ? route.stops.map((stop, i) => <div className="route-stop" key={stop.listing_id}><span className="stop-index">{i + 1}</span><div><b>{stop.item}</b><small>{stop.quantity_kg} kg · Listing #{stop.listing_id}</small></div><span>⌖</span></div>) : <EmptyState text="Accept surplus listings to see them in your route." />}</section><section className="panel"><div className="panel-heading"><div><div className="section-kicker">PICKUP LOCATIONS</div><h2>Route map</h2></div></div><MapView points={points} height={440} /></section></div>
    <div className="note-banner">Route order uses {route?.method || "the nearest-neighbour haversine fallback"}. Distance and ETA are estimates, not turn-by-turn navigation.</div>
  </main>;
}

function AnalyticsPage({ flash }) {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/analytics").then((res) => setData(res.data)).catch((error) => flash(errorMessage(error))); }, []);
  const monthly = data?.monthly?.reduce((acc, row) => {
    const existing = acc.find((item) => item.month === row.month);
    if (existing) existing.food_saved_kg += row.food_saved_kg; else acc.push({ ...row });
    return acc;
  }, []) || [];
  async function download() {
    try {
      const result = await api.get("/analytics/report.pdf", { responseType: "blob" });
      const url = URL.createObjectURL(result.data); const link = document.createElement("a");
      link.href = url; link.download = "annasetu-esg-report.pdf"; link.click(); URL.revokeObjectURL(url);
    } catch (error) { flash(errorMessage(error)); }
  }
  return <main className="page-shell"><PageHeader eyebrow="MEASURE THE DIFFERENCE" title="Impact & ESG" description="A transparent view of delivered food, community meals and estimated emissions avoided." action={<button className="button button-primary" onClick={download}>↓ Download ESG report</button>} />
    <div className="stat-grid impact-stats"><Stat icon="♧" label="Food saved" value={`${data?.food_saved_kg || 0} kg`} note="Successfully delivered" /><Stat icon="♡" label="Meals donated" value={data?.meals_donated || 0} note="Estimated 3 meals per kg" /><Stat icon="↗" label="CO₂ avoided" value={`${data?.co2_avoided_kg || 0} kg`} note={`${data?.co2_factor_kg_per_kg || 2.5} kg CO₂e / kg factor`} /><Stat icon="↓" label="Waste reduction" value={`${data?.waste_reduction_percent || 0}%`} note="Change vs first recorded month" /><Stat icon="₹" label="Cost saved" value={`₹${data?.cost_saved || 0}`} note="Estimated food value" /></div>
    <div className="chart-grid"><section className="panel"><div className="section-kicker">FOOD RECOVERY & WASTE</div><h2>Impact over time</h2><div className="chart"><ResponsiveContainer><LineChart data={monthly}><CartesianGrid stroke="#e9f0e9" strokeDasharray="3 3" /><XAxis dataKey="month" /><YAxis yAxisId="left" /><YAxis yAxisId="right" orientation="right" unit="%" /><Tooltip /><Line yAxisId="left" type="monotone" dataKey="food_saved_kg" name="Food saved (kg)" stroke={green} strokeWidth={3} /><Line yAxisId="right" type="monotone" dataKey="waste_reduction_percent" name="Waste reduction (%)" stroke="#E8A23A" strokeWidth={2} /></LineChart></ResponsiveContainer></div></section>
      <section className="panel"><div className="section-kicker">COMMUNITY VALUE</div><h2>Impact at a glance</h2><div className="chart"><ResponsiveContainer><BarChart data={[{ name: "Food saved (kg)", value: data?.food_saved_kg || 0 }, { name: "Meals donated", value: data?.meals_donated || 0 }, { name: "CO₂ avoided (kg)", value: data?.co2_avoided_kg || 0 }]}><CartesianGrid stroke="#e9f0e9" strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="value" fill={green} radius={[8, 8, 0, 0]} /></BarChart></ResponsiveContainer></div></section>
      <section className="panel"><div className="section-kicker">ESG SNAPSHOT</div><h2>Where impact adds up</h2><div className="chart"><ResponsiveContainer><PieChart><Pie data={[{ name: "Food recovered", value: data?.food_saved_kg || 1 }, { name: "Community meals", value: data?.meals_donated || 1 }, { name: "CO₂ avoided", value: data?.co2_avoided_kg || 1 }]} dataKey="value" nameKey="name" outerRadius={90} label>{["#1B7F3B", "#75B77E", "#E8A23A"].map((color) => <Cell key={color} fill={color} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div></section>
    </div><p className="method-note">Donation metrics use delivered listings. The configurable emissions factor defaults to {data?.co2_factor_kg_per_kg || 2.5} kg CO₂e per kg food; meals are estimated at 3 per kg. Waste reduction compares monthly meal waste (prepared minus consumed) with the first recorded month.</p>
  </main>;
}

export default App;
