<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Monitoreo ESP32 en la nube</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    :root{
      --bg:#0e0f10;
      --card:#1a1c1f;
      --cyan:#11c5d9;
      --txt:#e9eef2;
      --muted:#aab6be;
      --btn:#22262a;
      --btnActive:#0fb9cc;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
      background: radial-gradient(1200px 500px at 50% -100px, rgba(17,197,217,.25), transparent 60%), var(--bg);
      color:var(--txt);
      text-align:center;
    }
    .wrap{max-width:1200px;margin:0 auto;padding:24px 14px 40px}
    h1{
      margin:10px 0 6px;
      font-weight:800;
      letter-spacing:.5px;
      color:var(--cyan);
      text-shadow:0 0 24px rgba(17,197,217,.25);
    }
    .sub{color:var(--muted);margin:0 0 18px}
    .topbar{
      display:flex;
      flex-wrap:wrap;
      justify-content:center;
      gap:10px;
      margin:14px 0 18px;
    }
    .btn{
      border:none;
      padding:10px 16px;
      border-radius:12px;
      background:var(--btn);
      color:var(--txt);
      cursor:pointer;
      font-weight:700;
      transition:transform .08s ease, background .15s ease;
    }
    .btn:active{transform:scale(.98)}
    .btn.active{background:var(--btnActive); color:#001014}
    .btn.csv{
      background:linear-gradient(135deg, rgba(17,197,217,.95), rgba(17,197,217,.75));
      color:#001014;
    }
    .cards{
      margin-top:10px;
      background:linear-gradient(180deg, rgba(255,255,255,.03), transparent);
      border:1px solid rgba(255,255,255,.06);
      border-radius:22px;
      padding:18px;
      box-shadow:0 14px 40px rgba(0,0,0,.45);
    }
    .tab{display:none}
    .tab.active{display:block}
    .grid2{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:14px;
    }
    .grid3{
      display:grid;
      grid-template-columns:1fr 1fr 1fr;
      gap:14px;
    }
    @media (max-width:1000px){
      .grid3{grid-template-columns:1fr}
    }
    @media (max-width:900px){
      .grid2{grid-template-columns:1fr}
    }
    .card{
      background: radial-gradient(900px 320px at 50% 0px, rgba(255,255,255,.06), transparent 65%), var(--card);
      border:1px solid rgba(255,255,255,.06);
      border-radius:22px;
      padding:16px 14px 10px;
    }
    .card h2{
      margin:8px 0 8px;
      font-size:20px;
      font-weight:800;
    }
    canvas{width:100% !important; height:320px !important;}
    .hint{
      margin-top:10px;
      color:var(--muted);
      font-size:13px;
    }
  </style>
</head>

<body>
  <div class="wrap">
    <h1>Monitoreo ESP32 en la nube</h1>
    <p class="sub">Registros (ventana): <span id="count">0</span></p>

    <div class="topbar">
      <button class="btn active" data-tab="tTemp">Temperatura (°C)</button>
      <button class="btn" data-tab="tPanel">Sensores de Paneles</button>
      <button class="btn" data-tab="tRad">Radiómetro</button>

      <button class="btn" data-tab="tW1">WROOM - Canal 1</button>
      <button class="btn" data-tab="tW2">WROOM - Canal 2</button>
      <button class="btn" data-tab="tW3">WROOM - Canal 3</button>

      <button class="btn csv" id="btnCSV">📥 Descargar CSV (TODO)</button>
    </div>

    <div class="cards">
      <!-- TAB TEMPERATURA (S2) -->
      <div id="tTemp" class="tab active">
        <div class="card">
          <h2>Temperatura (°C) - ESP32 S2</h2>
          <canvas id="chTemp"></canvas>
          <div class="hint">Tip: pasa el dedo/ratón sobre la línea para ver el valor.</div>
        </div>
      </div>

      <!-- TAB SENSORES DE PANELES (S2) -->
      <div id="tPanel" class="tab">
        <div class="grid2">
          <div class="card">
            <h2>Voltaje (V) - S2</h2>
            <canvas id="chVolt"></canvas>
          </div>
          <div class="card">
            <h2>Corriente (A) - S2</h2>
            <canvas id="chCorr"></canvas>
          </div>
        </div>
        <div style="height:14px"></div>
        <div class="card">
          <h2>Potencia (W) - S2</h2>
          <canvas id="chPot"></canvas>
        </div>
      </div>

      <!-- TAB RADIÓMETRO (S2) -->
      <div id="tRad" class="tab">
        <div class="card">
          <h2>Radiómetro - ESP32 S2</h2>
          <canvas id="chRad"></canvas>
        </div>
      </div>

      <!-- WROOM CANAL 1 -->
      <div id="tW1" class="tab">
        <div class="grid3">
          <div class="card">
            <h2>Voltaje1 (V) - WROOM</h2>
            <canvas id="chWv1"></canvas>
          </div>
          <div class="card">
            <h2>Corriente1 (A) - WROOM</h2>
            <canvas id="chWc1"></canvas>
          </div>
          <div class="card">
            <h2>Potencia1 (W) - WROOM</h2>
            <canvas id="chWp1"></canvas>
          </div>
        </div>
      </div>

      <!-- WROOM CANAL 2 -->
      <div id="tW2" class="tab">
        <div class="grid3">
          <div class="card">
            <h2>Voltaje2 (V) - WROOM</h2>
            <canvas id="chWv2"></canvas>
          </div>
          <div class="card">
            <h2>Corriente2 (A) - WROOM</h2>
            <canvas id="chWc2"></canvas>
          </div>
          <div class="card">
            <h2>Potencia2 (W) - WROOM</h2>
            <canvas id="chWp2"></canvas>
          </div>
        </div>
      </div>

      <!-- WROOM CANAL 3 -->
      <div id="tW3" class="tab">
        <div class="grid3">
          <div class="card">
            <h2>Voltaje3 (V) - WROOM</h2>
            <canvas id="chWv3"></canvas>
          </div>
          <div class="card">
            <h2>Corriente3 (A) - WROOM</h2>
            <canvas id="chWc3"></canvas>
          </div>
          <div class="card">
            <h2>Potencia3 (W) - WROOM</h2>
            <canvas id="chWp3"></canvas>
          </div>
        </div>
      </div>

    </div>
  </div>

<script>
  // ================= CONFIG =================
  const API_BASE = "/api/data";
  const MAX_POINTS = 120;   // ventana visible (para que “se vaya recorriendo”)
  const REFRESH_MS = 2500;

  // ================= TABS =================
  const tabBtns = document.querySelectorAll(".btn[data-tab]");
  const tabs = document.querySelectorAll(".tab");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      tabs.forEach(t => t.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");
    });
  });

  // ================= CHART FACTORY =================
  function makeLineChart(canvasId, label, suggestedMax){
    const ctx = document.getElementById(canvasId).getContext("2d");
    return new Chart(ctx, {
      type: "line",
      data: {
        labels: [],
        datasets: [{
          label,
          data: [],
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.25,
          fill: false,
          spanGaps: true
        }]
      },
      options: {
        responsive: true,
        animation: { duration: 250 },
        parsing: false,
        interaction: { mode: "nearest", intersect: false },
        plugins: {
          legend: { display: true },
          tooltip: { enabled: true, mode: "nearest", intersect: false },
          decimation: { enabled: true, algorithm: "min-max" }
        },
        scales: {
          x: {
            ticks: { maxRotation: 0, autoSkip: true },
            grid: { display: false }
          },
          y: {
            beginAtZero: true,
            suggestedMax: suggestedMax,
            grid: { color: "rgba(255,255,255,.06)" }
          }
        }
      }
    });
  }

  // S2
  const chTemp = makeLineChart("chTemp", "Temperatura (°C)", 120);
  const chVolt = makeLineChart("chVolt", "Voltaje (V)", 30);
  const chCorr = makeLineChart("chCorr", "Corriente (A)", 10);
  const chPot  = makeLineChart("chPot",  "Potencia (W)", 200);
  const chRad  = makeLineChart("chRad",  "Radiómetro", 4096);

  // WROOM (3 canales)
  const chWv1 = makeLineChart("chWv1", "Voltaje1 (V)", 30);
  const chWc1 = makeLineChart("chWc1", "Corriente1 (A)", 10);
  const chWp1 = makeLineChart("chWp1", "Potencia1 (W)", 200);

  const chWv2 = makeLineChart("chWv2", "Voltaje2 (V)", 30);
  const chWc2 = makeLineChart("chWc2", "Corriente2 (A)", 10);
  const chWp2 = makeLineChart("chWp2", "Potencia2 (W)", 200);

  const chWv3 = makeLineChart("chWv3", "Voltaje3 (V)", 30);
  const chWc3 = makeLineChart("chWc3", "Corriente3 (A)", 10);
  const chWp3 = makeLineChart("chWp3", "Potencia3 (W)", 200);

  // ================= HELPERS =================
  function pad2(n){ return String(n).padStart(2,"0"); }

  // convierte a número seguro (soporta "15,25")
  function clampNumber(x){
    if (x === null || x === undefined) return null;
    if (typeof x === "string") x = x.replace(",", ".");
    const n = Number(x);
    return Number.isFinite(n) ? n : null;
  }

  // etiqueta HH:MM:SS (sin microsegundos)
  function labelFromRow(row){
    const h = (row.hora || "00:00:00").split(".")[0];
    return h;
  }

  // Orden correcto: SIEMPRE por id asc (viejo→nuevo)
  function sortChronoAsc(arr){
    arr.sort((a,b) => Number(a.id) - Number(b.id));
  }

  function setChart(chart, labels, data){
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update();
  }

  async function fetchDevice(device){
    const url = `${API_BASE}?device=${encodeURIComponent(device)}&limit=300`;
    const res = await fetch(url, { cache:"no-store" });
    if(!res.ok) throw new Error("API error " + res.status);
    const arr = await res.json();

    // tu API viene DESC (nuevo→viejo). La ordenamos a ASC (viejo→nuevo)
    sortChronoAsc(arr);

    // ventana visible
    const view = arr.slice(-MAX_POINTS);

    return { all: arr, view };
  }

  function buildSeries(view){
    const labels = view.map(labelFromRow);
    return { labels };
  }

  // ================= REFRESH =================
  async function refresh(){
    try{
      // S2
      const s2 = await fetchDevice("s2");
      const s2labels = s2.view.map(labelFromRow);

      const temp = s2.view.map(d => clampNumber(d.temperatura));
      const volt = s2.view.map(d => clampNumber(d.voltaje));
      const corr = s2.view.map(d => clampNumber(d.corriente));
      const pot  = s2.view.map(d => clampNumber(d.potencia));
      const rad  = s2.view.map(d => clampNumber(d.radiometro));

      setChart(chTemp, s2labels, temp);
      setChart(chVolt, s2labels, volt);
      setChart(chCorr, s2labels, corr);
      setChart(chPot,  s2labels, pot);
      setChart(chRad,  s2labels, rad);

      // WROOM
      const wr = await fetchDevice("wroom");
      const wrlabels = wr.view.map(labelFromRow);

      setChart(chWv1, wrlabels, wr.view.map(d=>clampNumber(d.voltaje1)));
      setChart(chWc1, wrlabels, wr.view.map(d=>clampNumber(d.corriente1)));
      setChart(chWp1, wrlabels, wr.view.map(d=>clampNumber(d.potencia1)));

      setChart(chWv2, wrlabels, wr.view.map(d=>clampNumber(d.voltaje2)));
      setChart(chWc2, wrlabels, wr.view.map(d=>clampNumber(d.corriente2)));
      setChart(chWp2, wrlabels, wr.view.map(d=>clampNumber(d.potencia2)));

      setChart(chWv3, wrlabels, wr.view.map(d=>clampNumber(d.voltaje3)));
      setChart(chWc3, wrlabels, wr.view.map(d=>clampNumber(d.corriente3)));
      setChart(chWp3, wrlabels, wr.view.map(d=>clampNumber(d.potencia3)));

      // contador: muestra el tamaño de la ventana (más real para lo que ves)
      document.getElementById("count").textContent = MAX_POINTS;

    }catch(e){
      console.log("refresh error:", e);
    }
  }

  // ================= CSV (TODO junto) =================
  function toCSV(rows){
    // SIN device, sin microsegundos
    const header = [
      "id","fecha","hora",
      "voltaje","corriente","potencia","radiometro","temperatura",
      "voltaje1","voltaje2","voltaje3",
      "corriente1","corriente2","corriente3",
      "potencia1","potencia2","potencia3"
    ];
    const lines = [header.join(",")];

    for(const r of rows){
      lines.push([
        r.id ?? "",
        r.fecha ?? "",
        (r.hora ?? "").split(".")[0],
        r.voltaje ?? "",
        r.corriente ?? "",
        r.potencia ?? "",
        r.radiometro ?? "",
        r.temperatura ?? "",
        r.voltaje1 ?? "",
        r.voltaje2 ?? "",
        r.voltaje3 ?? "",
        r.corriente1 ?? "",
        r.corriente2 ?? "",
        r.corriente3 ?? "",
        r.potencia1 ?? "",
        r.potencia2 ?? "",
        r.potencia3 ?? ""
      ].join(","));
    }
    return lines.join("\n");
  }

  async function fetchAllForCSV(device){
    const res = await fetch(`${API_BASE}?device=${encodeURIComponent(device)}&limit=5000`, {cache:"no-store"});
    if(!res.ok) throw new Error("API error " + res.status);
    const arr = await res.json();
    // ordenar ASC por id
    sortChronoAsc(arr);
    return arr;
  }

  document.getElementById("btnCSV").addEventListener("click", async () => {
    try{
      const [s2, wroom] = await Promise.all([fetchAllForCSV("s2"), fetchAllForCSV("wroom")]);

      // combinar en un solo CSV (todo revuelto NO: orden por id global)
      const all = [...s2, ...wroom];
      sortChronoAsc(all);

      const csv = toCSV(all);
      const blob = new Blob([csv], {type:"text/csv;charset=utf-8"});
      const url = URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      const now = new Date();
      a.download = `esp32_todo_${now.getFullYear()}-${pad2(now.getMonth()+1)}-${pad2(now.getDate())}_${pad2(now.getHours())}${pad2(now.getMinutes())}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }catch(e){
      console.log("CSV error:", e);
      alert("No pude generar el CSV. Revisa consola (F12).");
    }
  });

  // ================= START =================
  refresh();
  setInterval(refresh, REFRESH_MS);
</script>
</body>
</html>

