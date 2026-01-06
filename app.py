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
    }
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
      font-size:18px;
      font-weight:800;
    }
    canvas{width:100% !important; height:280px !important;}
    .hint{margin-top:10px;color:var(--muted);font-size:13px}
    .split{height:14px}
  </style>
</head>

<body>
  <div class="wrap">
    <h1>Monitoreo ESP32 en la nube</h1>
    <p class="sub">
      Registros S2: <span id="countS2">0</span> ·
      Registros WROOM: <span id="countW">0</span>
    </p>

    <div class="topbar">
      <button class="btn active" data-tab="tTemp">Temperatura (°C)</button>
      <button class="btn" data-tab="tSens">Sensores de paneles (S2)</button>
      <button class="btn" data-tab="tRad">Radiómetro (S2)</button>

      <button class="btn" data-tab="tW1">WROOM Panel 1</button>
      <button class="btn" data-tab="tW2">WROOM Panel 2</button>
      <button class="btn" data-tab="tW3">WROOM Panel 3</button>

      <button class="btn csv" id="btnCSV">📥 Descargar CSV (S2)</button>
    </div>

    <div class="cards">

      <!-- TAB TEMPERATURA (S2) -->
      <div id="tTemp" class="tab active">
        <div class="card">
          <h2>Temperatura (°C) - S2</h2>
          <canvas id="chTemp"></canvas>
          <div class="hint">Tip: pasa el dedo/ratón sobre la línea para ver el valor.</div>
        </div>
      </div>

      <!-- TAB SENSORES S2 -->
      <div id="tSens" class="tab">
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
        <div class="split"></div>
        <div class="card">
          <h2>Potencia (W) - S2</h2>
          <canvas id="chPot"></canvas>
        </div>
      </div>

      <!-- TAB RADIÓMETRO (S2) -->
      <div id="tRad" class="tab">
        <div class="card">
          <h2>Radiómetro - S2</h2>
          <canvas id="chRad"></canvas>
        </div>
      </div>

      <!-- TAB WROOM PANEL 1 -->
      <div id="tW1" class="tab">
        <div class="card">
          <h2>WROOM Panel 1</h2>
          <div class="grid3">
            <div class="card"><h2>Voltaje 1 (V)</h2><canvas id="chWV1"></canvas></div>
            <div class="card"><h2>Corriente 1 (A)</h2><canvas id="chWC1"></canvas></div>
            <div class="card"><h2>Potencia 1 (W)</h2><canvas id="chWP1"></canvas></div>
          </div>
          <div class="hint">Datos desde /api/data?device=wroom</div>
        </div>
      </div>

      <!-- TAB WROOM PANEL 2 -->
      <div id="tW2" class="tab">
        <div class="card">
          <h2>WROOM Panel 2</h2>
          <div class="grid3">
            <div class="card"><h2>Voltaje 2 (V)</h2><canvas id="chWV2"></canvas></div>
            <div class="card"><h2>Corriente 2 (A)</h2><canvas id="chWC2"></canvas></div>
            <div class="card"><h2>Potencia 2 (W)</h2><canvas id="chWP2"></canvas></div>
          </div>
          <div class="hint">Datos desde /api/data?device=wroom</div>
        </div>
      </div>

      <!-- TAB WROOM PANEL 3 -->
      <div id="tW3" class="tab">
        <div class="card">
          <h2>WROOM Panel 3</h2>
          <div class="grid3">
            <div class="card"><h2>Voltaje 3 (V)</h2><canvas id="chWV3"></canvas></div>
            <div class="card"><h2>Corriente 3 (A)</h2><canvas id="chWC3"></canvas></div>
            <div class="card"><h2>Potencia 3 (W)</h2><canvas id="chWP3"></canvas></div>
          </div>
          <div class="hint">Datos desde /api/data?device=wroom</div>
        </div>
      </div>

    </div>
  </div>

<script>
  // ========= CONFIG =========
  const API_S2 = "/api/data?device=s2";
  const API_W  = "/api/data?device=wroom";
  const MAX_POINTS = 120;
  const REFRESH_MS = 3000;

  // ========= TABS =========
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

  // ========= CHART FACTORY =========
  function makeLineChart(canvasId, label, suggestedMax){
    const ctx = document.getElementById(canvasId).getContext("2d");
    return new Chart(ctx, {
      type: "line",
      data: { labels: [], datasets: [{ label, data: [], borderWidth: 2, pointRadius: 0, tension: 0.25, fill: false }] },
      options: {
        responsive: true,
        animation: { duration: 200 },
        interaction: { mode: "nearest", intersect: false },
        plugins: {
          legend: { display: true },
          tooltip: { enabled: true, mode: "nearest", intersect: false },
          decimation: { enabled: true, algorithm: "min-max" }
        },
        scales: {
          x: { ticks: { autoSkip: true, maxRotation: 0 }, grid: { display: false } },
          y: { beginAtZero: true, suggestedMax, grid: { color: "rgba(255,255,255,.06)" } }
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

  // WROOM Panel 1..3
  const chWV1 = makeLineChart("chWV1", "Voltaje 1 (V)", 30);
  const chWC1 = makeLineChart("chWC1", "Corriente 1 (A)", 10);
  const chWP1 = makeLineChart("chWP1", "Potencia 1 (W)", 200);

  const chWV2 = makeLineChart("chWV2", "Voltaje 2 (V)", 30);
  const chWC2 = makeLineChart("chWC2", "Corriente 2 (A)", 10);
  const chWP2 = makeLineChart("chWP2", "Potencia 2 (W)", 200);

  const chWV3 = makeLineChart("chWV3", "Voltaje 3 (V)", 30);
  const chWC3 = makeLineChart("chWC3", "Corriente 3 (A)", 10);
  const chWP3 = makeLineChart("chWP3", "Potencia 3 (W)", 200);

  // ========= HELPERS =========
  function parseDateTime(row){
    const h = (row.hora || "00:00:00").split(".")[0];
    return new Date(`${row.fecha}T${h}`);
  }
  function labelFromRow(row){
    return (row.hora || "00:00:00").split(".")[0];
  }
  function nval(x){
    const n = Number(x);
    return Number.isFinite(n) ? n : null;
  }
  function normalize(arr){
    const ordered = [...arr].sort((a,b) => parseDateTime(a) - parseDateTime(b));
    const view = ordered.slice(-MAX_POINTS);
    return { total: arr.length, labels: view.map(labelFromRow), view };
  }
  function setChart(chart, labels, data){
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update();
  }

  // ========= REFRESH =========
  async function refresh(){
    try{
      const [s2Res, wRes] = await Promise.all([
        fetch(API_S2, {cache:"no-store"}).then(r => r.json()),
        fetch(API_W,  {cache:"no-store"}).then(r => r.json()),
      ]);

      const s2 = normalize(s2Res);
      const w  = normalize(wRes);

      document.getElementById("countS2").textContent = s2.total;
      document.getElementById("countW").textContent  = w.total;

      // S2
      setChart(chTemp, s2.labels, s2.view.map(d => nval(d.temperatura)));
      setChart(chVolt, s2.labels, s2.view.map(d => nval(d.voltaje)));
      setChart(chCorr, s2.labels, s2.view.map(d => nval(d.corriente)));
      setChart(chPot,  s2.labels, s2.view.map(d => nval(d.potencia)));
      setChart(chRad,  s2.labels, s2.view.map(d => nval(d.radiometro)));

      // WROOM (usa keys voltaje1..3, corriente1..3, potencia1..3)
      setChart(chWV1, w.labels, w.view.map(d => nval(d.voltaje1)));
      setChart(chWC1, w.labels, w.view.map(d => nval(d.corriente1)));
      setChart(chWP1, w.labels, w.view.map(d => nval(d.potencia1)));

      setChart(chWV2, w.labels, w.view.map(d => nval(d.voltaje2)));
      setChart(chWC2, w.labels, w.view.map(d => nval(d.corriente2)));
      setChart(chWP2, w.labels, w.view.map(d => nval(d.potencia2)));

      setChart(chWV3, w.labels, w.view.map(d => nval(d.voltaje3)));
      setChart(chWC3, w.labels, w.view.map(d => nval(d.corriente3)));
      setChart(chWP3, w.labels, w.view.map(d => nval(d.potencia3)));

    }catch(e){
      console.log("refresh error:", e);
    }
  }

  // ========= CSV (solo S2) =========
  function toCSV(rows){
    const header = ["fecha","hora","voltaje","corriente","potencia","radiometro","temperatura"];
    const lines = [header.join(",")];
    const ordered = [...rows].sort((a,b) => parseDateTime(a) - parseDateTime(b));
    for(const r of ordered){
      lines.push([
        r.fecha ?? "",
        (r.hora ?? "").split(".")[0],
        r.voltaje ?? "",
        r.corriente ?? "",
        r.potencia ?? "",
        r.radiometro ?? "",
        r.temperatura ?? ""
      ].join(","));
    }
    return lines.join("\n");
  }

  document.getElementById("btnCSV").addEventListener("click", async () => {
    const rows = await fetch(API_S2, {cache:"no-store"}).then(r => r.json());
    const csv = toCSV(rows);
    const blob = new Blob([csv], {type:"text/csv;charset=utf-8"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `esp32_s2.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  refresh();
  setInterval(refresh, REFRESH_MS);
</script>
</body>
</html>
