// amoblai · la web. Una sola página: landing, nuevo ambiente, avance, resultado, historial, ajustes.

const $app = document.getElementById("app");

// utilidades ------------------------------------------------------------------------------------

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const ICONS = {
  logo: '<path d="M10 20H4V4h16v16h-2"/><path d="M18 20v-8"/><path d="M18 12a8 8 0 0 0-8 8"/>',
  left: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  right: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  done: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  todo: '<circle cx="12" cy="12" r="9"/>',
  spin: '<path d="M21 12a9 9 0 1 1-6.219-8.56"/>',
  alert: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
  image: '<path d="M16 5h6"/><path d="M19 2v6"/><path d="M21 11.5V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7.5"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/><circle cx="9" cy="9" r="2"/>',
  download: '<path d="M12 15V3"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  retry: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  drag: '<path d="m9 7-5 5 5 5"/><path d="m15 7 5 5-5 5"/>',
  layers: '<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>',
};
const NAMES = { anthropic: "Anthropic", openai: "OpenAI", fal: "fal" };
const VIA = { web: "Desde la web", terminal: "Desde la terminal", "interfaz vieja": "Desde la interfaz vieja" };
const icon = (name, cls = "") =>
  `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;

const money = (n) => "US$ " + Number(n || 0).toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const clock = (s) => `${Math.floor((s || 0) / 60)}:${String(Math.floor((s || 0) % 60)).padStart(2, "0")}`;
const day = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  const date = d.toLocaleDateString("es-AR", { day: "numeric", month: "short" }).replace(".", "");
  const time = d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", hour12: false });
  return `${date} · ${time}`;
};
const AXES = [["width", "de ancho"], ["depth", "de profundidad"], ["height", "de alto"]];
const sizeText = (m) => (m ? AXES.filter(([k]) => m[k]).map(([k]) => m[k]).join(" × ") + " cm" : "");
const sizeTitle = (m) => (m ? AXES.filter(([k]) => m[k]).map(([k, w]) => `${m[k]} cm ${w}`).join(", ") : "");
const limitText = (h) => {
  const parts = AXES.filter(([k]) => h && h[k]).map(([k, w]) => `${h[k]} cm ${w}`);
  return parts.length ? "hasta " + parts.join(", ") : "";
};
const cota = (m) =>
  m
    ? `<span class="cota" title="${esc(sizeTitle(m))}"><span class="cota-line"></span><span class="cota-val">${esc(sizeText(m))}</span></span>`
    : `<span class="cota none"><span class="cota-line"></span><span class="cota-val muted">sin medidas en el catálogo</span></span>`;
const stores = (lista) => {
  const s = [...new Set((lista || []).map((p) => p.tienda))];
  return s.length === 2 ? "IKEA y Amazon" : s[0] || "";
};
const units = (lista) => (lista || []).reduce((n, p) => n + (p.cantidad || 1), 0);

async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "No pudimos conectar con el servidor");
  return data;
}

let toastTimer;
function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("on");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("on"), 3600);
}

let examplesCache;
const examples = async () => (examplesCache ??= await api("/static/ejemplos.json"));

// navegación ------------------------------------------------------------------------------------

function nav(kind, here = "") {
  const links =
    kind === "landing"
      ? `<a href="#como" class="hide-s">Cómo funciona</a><a href="#ejemplos" class="hide-s">Ejemplos</a><a href="/ambientes">Mis ambientes</a>`
      : `<a href="/nuevo" class="${here === "nuevo" ? "on" : ""}">Nuevo ambiente</a><a href="/ambientes" class="${here === "ambientes" ? "on" : ""}">Mis ambientes</a><a href="/ajustes" class="${here === "ajustes" ? "on" : ""}">Ajustes</a>`;
  const cta = kind === "landing" ? `<a class="btn btn-ink btn-sm" href="/nuevo">Amoblar mi ambiente</a>` : "";
  return `<header class="nav"><div class="wrap"><a class="logo" href="/">${icon("logo")}amoblai</a><nav class="nav-links">${links}</nav>${cta}</div></header>`;
}

const footer = () =>
  `<footer class="foot"><div class="wrap"><a class="logo" href="/">${icon("logo")}amoblai</a><span>Proyecto de la materia de LLM · ITBA · 2026</span></div></footer>`;

// antes y después ---------------------------------------------------------------------------------

function beforeAfter({ antes, despues, alineada }, start = 50) {
  if (!despues) return `<div class="ba"><img src="${esc(antes)}" alt="El ambiente vacío"></div>`;
  if (alineada)
    return `<div class="ba slide" data-ba style="--x:${start}%">
      <img src="${esc(antes)}" alt="El ambiente vacío, como era">
      <img class="after" src="${esc(despues)}" alt="El ambiente amoblado con los productos de la lista">
      <span class="handle"></span>
      <button class="knob" aria-label="Deslizar entre antes y después">${icon("drag")}</button>
      <span class="tag l">Antes</span><span class="tag r">Después</span>
    </div>`;
  return `<div class="ba fade" data-fade>
      <img src="${esc(antes)}" alt="El ambiente vacío, como era">
      <img class="after" src="${esc(despues)}" alt="El ambiente amoblado con los productos de la lista">
    </div>`;
}

function wireBeforeAfter(root) {
  root.querySelectorAll("[data-ba]").forEach((el) => {
    const set = (clientX) => {
      const r = el.getBoundingClientRect();
      const x = Math.min(100, Math.max(0, ((clientX - r.left) / r.width) * 100));
      el.style.setProperty("--x", x + "%");
    };
    el.addEventListener("pointerdown", (e) => {
      el.setPointerCapture(e.pointerId);
      set(e.clientX);
    });
    el.addEventListener("pointermove", (e) => el.hasPointerCapture(e.pointerId) && set(e.clientX));
    el.querySelector(".knob").addEventListener("keydown", (e) => {
      const x = parseFloat(el.style.getPropertyValue("--x")) || 50;
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        e.preventDefault();
        el.style.setProperty("--x", Math.min(100, Math.max(0, x + (e.key === "ArrowLeft" ? -5 : 5))) + "%");
      }
    });
  });
  root.querySelectorAll("[data-seg]").forEach((seg) => {
    const fade = root.querySelector("[data-fade]");
    seg.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b || !fade) return;
      seg.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
      fade.classList.toggle("show-before", b.dataset.v === "antes");
    });
  });
}

// la landing ----------------------------------------------------------------------------------------

async function landing() {
  const { ejemplos, candidatos } = await examples();
  const hero = ejemplos[0];
  const sofa = hero.lista.find((p) => p.medidas && p.medidas.height) || hero.lista[0];
  const total = 1502;

  $app.innerHTML = `${nav("landing")}
  <main>
    <section class="hero"><div class="wrap">
      <div class="enter">
        <h1>Amoblá tu ambiente a partir de una foto</h1>
        <p class="sub">Sacale una foto al ambiente vacío y contá cómo lo imaginás. amoblai elige muebles reales de IKEA y Amazon que van con el espacio, te dice por qué y te muestra cómo quedaría.</p>
        <div class="actions">
          <a class="btn btn-ink btn-lg" href="/nuevo">Amoblar mi ambiente ${icon("right")}</a>
          <a class="btn btn-ghost btn-lg" href="#ejemplos">Ver ejemplos</a>
        </div>
        <div class="facts mono"><span><b>${total.toLocaleString("es-AR")}</b> productos</span><span><b>43</b> tipos de muebles</span><span><b>2</b> minutos</span></div>
      </div>
      <div class="hero-visual enter d1">
        ${beforeAfter(hero, 54)}
        <a class="chip" href="/ejemplos/${esc(hero.id)}">
          <span class="ph"><img src="${esc(sofa.foto)}" alt=""></span>
          <span><span class="k">${esc(sofa.tipo)} · ${esc(sofa.tienda)}</span><span class="n">${esc(sofa.nombre)}</span>${cota(sofa.medidas)}</span>
        </a>
      </div>
    </div></section>

    <section class="section band" id="como"><div class="wrap">
      <div class="section-head">
        <h2>De la foto a la lista, en tres pasos</h2>
        <p class="lede">Lo que ves al final son productos que existen, con su foto y sus medidas, y una imagen para darte una idea de cómo quedan juntos.</p>
      </div>
      <div class="steps3">
        <article class="step3">
          <div class="vis"><img class="cover" src="${esc(hero.antes)}" alt="Un living vacío">
            <div class="bubble"><span class="who mono muted">Tu pedido</span>${esc(hero.pedido.split(/(?<=\.)\s/)[0])}</div></div>
          <span class="mono n">01</span><h3>Contás cómo lo imaginás</h3>
          <p>Una foto del ambiente vacío y unas líneas. Lee el espacio, la luz y lo que entra en cada pared.</p>
        </article>
        <article class="step3">
          <div class="vis"><div class="cands">
            ${candidatos.fotos.map((f, i) => `<div class="c ${i === candidatos.elegido ? "pick" : ""}"><img src="${esc(f)}" alt="">${i === candidatos.elegido ? `<span class="ok">${icon("check")}</span>` : ""}</div>`).join("")}
            <div class="c info"><span class="mono muted">5 candidatos</span><span style="font-size:13px;line-height:18px">para el ${esc(candidatos.pieza)}, por tipo, medidas y estilo</span></div>
          </div></div>
          <span class="mono n">02</span><h3>Busca entre ${total.toLocaleString("es-AR")} productos</h3>
          <p>Para cada mueble trae los cinco que mejor responden a la descripción, sin pasarse de las medidas del lugar.</p>
        </article>
        <article class="step3">
          <div class="vis"><img class="cover" src="${esc(hero.despues)}" alt="El living amoblado">
            <div class="mini-list">${hero.lista.slice(0, 3).map((p) => `<div class="r"><img src="${esc(p.foto)}" alt=""><span>${esc(p.tipo)}</span><span class="mono muted">${p.medidas ? esc(sizeText(p.medidas)) : ""}</span></div>`).join("")}</div></div>
          <span class="mono n">03</span><h3>Elige y te lo muestra</h3>
          <p>Arma la combinación, te explica por qué cada producto y dibuja tu ambiente con ellos.</p>
        </article>
      </div>
    </div></section>

    <section class="section" id="ejemplos"><div class="wrap">
      <div class="section-head">
        <h2>Ambientes reales, muebles reales</h2>
        <p class="lede">Cada ejemplo es una corrida completa: el pedido tal cual, la lista que armó y la imagen. Pasá el mouse para ver el antes.</p>
      </div>
      <div class="gallery">
        ${ejemplos.slice(0, 6).map((e, i) => `
          <a class="gcard ${i === 0 ? "big" : ""}" href="/ejemplos/${esc(e.id)}">
            <div class="im"><img src="${esc(e.despues)}" alt="Ambiente amoblado" loading="lazy"><img class="b" src="${esc(e.antes)}" alt="El mismo ambiente vacío" loading="lazy"><span class="tag">Antes</span></div>
            <div class="cap"><p class="q">“${esc(e.pedido)}”</p><span class="mono muted">${units(e.lista)} productos · ${esc(stores(e.lista))}</span></div>
          </a>`).join("")}
      </div>
    </div></section>

    <section class="section band"><div class="wrap">
      <div class="section-head"><h2>Antes de probar</h2></div>
      <div class="know">
        <div><span class="cota"><span class="cota-line"></span></span><h3>La lista es lo que vale</h3><p>Los productos existen y sus medidas salen del catálogo. La imagen es una visualización: puede no copiar cada mueble al detalle.</p></div>
        <div><span class="cota"><span class="cota-line"></span></span><h3>Living, comedor y escritorio</h3><p>El catálogo tiene ${total.toLocaleString("es-AR")} productos de IKEA y Amazon para esos ambientes. Para un dormitorio todavía no hay camas.</p></div>
        <div><span class="cota"><span class="cota-line"></span></span><h3>Unos dos minutos</h3><p>Leer el ambiente, buscar y elegir lleva alrededor de un minuto. Dibujar la imagen, otro más.</p></div>
      </div>
    </div></section>

    <section class="cta" style="padding-top:96px"><div class="wrap"><div class="box">
      <div><h2>Probalo con tu ambiente</h2><p>Una foto y dos líneas alcanzan. La lista te queda guardada en Mis ambientes.</p></div>
      <a class="btn btn-lg" href="/nuevo">Amoblar mi ambiente ${icon("right")}</a>
    </div></div></section>
  </main>${footer()}`;
  wireBeforeAfter($app);
}

// nuevo ambiente --------------------------------------------------------------------------------------

const IDEAS = [
  "Quiero amoblar mi living. Elegí los muebles que mejor queden",
  "Un living nórdico y cálido, con un sofá de tres cuerpos, una mesa ratona redonda y una alfombra",
  "Un comedor para seis personas, de madera clara, con una lámpara colgante",
  "Un escritorio sobrio para trabajar en casa, con una biblioteca y buena luz",
];

async function nuevo() {
  const [samples, st] = await Promise.all([api("/api/muestras"), api("/api/estado")]);
  const bad = (k) => !st.claves[k].cargada || st.claves[k].valida === false;
  const noKey = bad("anthropic");
  const acc = st.modelos[st.imagen].cuenta;
  const noImage = bad(acc);
  const keyWhy = st.claves.anthropic.cargada ? "Anthropic rechaza la clave cargada." : "Para empezar falta la clave de Anthropic.";
  const imageWhy = st.claves[acc].cargada ? `${NAMES[acc]} rechaza la clave cargada: vas a recibir la lista, sin la imagen.` : `Sin clave de ${NAMES[acc]} vas a recibir la lista, sin la imagen.`;
  $app.innerHTML = `${nav("app", "nuevo")}
  <main class="page"><div class="wrap">
    <div class="page-head enter"><div><h1>Nuevo ambiente</h1><p>Una foto del ambiente vacío y unas líneas de cómo lo imaginás.</p></div></div>
    <div class="new enter d1">
      <div>
        <label class="drop" id="drop">
          <div class="empty">
            <span class="ic">${icon("image")}</span>
            <b>Arrastrá la foto del ambiente</b>
            <span class="soft">o hacé clic para elegir un archivo</span>
            <span class="mono muted" style="margin-top:8px">JPG o PNG · el ambiente vacío, con buena luz</span>
          </div>
          <input type="file" id="file" accept="image/*" aria-label="Elegir la foto del ambiente">
        </label>
        <p class="samples-h">O probá con uno de estos</p>
        <div class="samples">${samples.map((s) => `<button data-id="${esc(s.id)}" aria-label="Usar este ambiente de ejemplo"><img src="${esc(s.foto)}" alt=""></button>`).join("")}</div>
      </div>
      <form class="card form" id="form">
        <div><label class="label" for="pedido">¿Cómo lo imaginás?</label>
          <textarea id="pedido" placeholder="Un living cálido para recibir amigos, con un sofá grande, una mesa ratona redonda y mucha luz"></textarea></div>
        <div><span class="label" style="font-weight:400;color:var(--ink-3);font-size:13px">Ideas</span>
          <div class="ideas">${IDEAS.map((t) => `<button type="button">${esc(t)}</button>`).join("")}</div></div>
        ${noKey ? `<div class="notice bad">${icon("alert")}<span>${keyWhy} <a href="/ajustes">${st.claves.anthropic.cargada ? "Reemplazala" : "Cargala"} en Ajustes</a></span></div>` : ""}
        ${!noKey && noImage ? `<div class="notice">${icon("alert")}<span>${imageWhy} <a href="/ajustes">Cargarla</a></span></div>` : ""}
        <button class="btn btn-ink btn-lg btn-block" id="go" ${noKey ? "disabled" : ""}>Amoblar</button>
        <p class="hint">Tarda unos dos minutos. El catálogo tiene muebles de living, comedor y escritorio.</p>
      </form>
    </div>
  </div></main>`;

  let file = null;
  let sample = "";
  const drop = document.getElementById("drop");
  const show = (src) => {
    drop.classList.add("has");
    drop.querySelector(".prev")?.remove();
    drop.querySelector(".change")?.remove();
    drop.insertAdjacentHTML("beforeend", `<img class="prev" src="${esc(src)}" alt="La foto elegida"><button type="button" class="btn btn-ghost btn-sm change">Cambiar foto</button>`);
    drop.querySelector(".change").addEventListener("click", (e) => {
      e.preventDefault();
      file = null;
      sample = "";
      drop.classList.remove("has");
      drop.querySelector(".prev").remove();
      e.currentTarget.remove();
      document.querySelectorAll(".samples button").forEach((b) => b.classList.remove("on"));
    });
  };
  const pick = (f) => {
    if (!f || !f.type.startsWith("image/")) return toast("Elegí una imagen JPG o PNG");
    file = f;
    sample = "";
    document.querySelectorAll(".samples button").forEach((b) => b.classList.remove("on"));
    show(URL.createObjectURL(f));
  };
  document.getElementById("file").addEventListener("change", (e) => pick(e.target.files[0]));
  ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => (e.preventDefault(), drop.classList.add("over"))));
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove("over")));
  drop.addEventListener("drop", (e) => (e.preventDefault(), pick(e.dataTransfer.files[0])));
  document.querySelectorAll(".samples button").forEach((b) =>
    b.addEventListener("click", () => {
      file = null;
      sample = b.dataset.id;
      document.querySelectorAll(".samples button").forEach((x) => x.classList.toggle("on", x === b));
      show(b.querySelector("img").src.replace("w=640", "w=1200"));
    }),
  );
  const ta = document.getElementById("pedido");
  document.querySelectorAll(".ideas button").forEach((b) => b.addEventListener("click", () => ((ta.value = b.textContent), ta.focus())));

  document.getElementById("form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!file && !sample) return toast("Subí una foto del ambiente o elegí uno de los ejemplos");
    if (!ta.value.trim()) return (toast("Contá cómo imaginás el ambiente"), ta.focus());
    const go = document.getElementById("go");
    go.disabled = true;
    go.textContent = "Empezando…";
    const fd = new FormData();
    fd.append("pedido", ta.value.trim());
    if (file) fd.append("foto", file);
    else fd.append("muestra", sample);
    try {
      const { id } = await api("/api/ambientes", { method: "POST", body: fd });
      navigate(`/ambientes/${id}`);
    } catch (err) {
      toast(err.message);
      go.disabled = false;
      go.textContent = "Amoblar";
    }
  });
}

// un ambiente (en curso o listo) -------------------------------------------------------------------------

function stepIcon(s) {
  return { hecho: icon("done"), activo: icon("spin"), error: icon("alert") }[s] || icon("todo");
}

function regions(s, isExample) {
  const done = s.estado === "listo";
  const running = s.estado === "corriendo" || s.estado === "en cola";
  const showSeg = s.despues && !s.alineada;
  const visual = `
    <div class="bar">${showSeg ? `<div class="seg" data-seg><button class="on" data-v="despues">Después</button><button data-v="antes">Antes</button></div>` : `<span class="mono muted">${s.despues ? (s.alineada ? "Arrastrá para comparar" : "") : running ? "La foto que subiste" : ""}</span>`}
      ${s.despues && s.descarga ? `<a class="link" href="${esc(s.descarga)}" download>${icon("download")}Descargar imagen</a>` : ""}</div>
    <div style="position:relative">${beforeAfter(s)}
      ${!s.despues && running && s.lista.length ? `<span class="working">${icon("spin")}Dibujando el ambiente${s.intento > 1 ? ` · intento ${s.intento}` : ""}</span>` : ""}</div>
    ${s.despues ? `<p class="caption">La imagen es orientativa: los productos reales son los de la lista.</p>` : ""}`;

  const doneSecs = (s.pasos || []).reduce((n, p) => n + (p.segundos || 0), 0);
  const progress = isExample || s.origen !== "web"
    ? ""
    : `<div class="card"><h3>${done ? "Listo" : s.estado === "error" ? "Se detuvo" : s.estado === "en cola" ? "En espera" : "En curso"}</h3>
      <ol class="prog">${s.pasos.map((p) => `<li class="${p.estado}">${stepIcon(p.estado)}<span>${esc(p.titulo)}</span><span class="mono">${p.estado === "hecho" ? clock(p.segundos) : p.estado === "activo" ? clock(Math.max(0, s.segundos - doneSecs)) : ""}</span></li>`).join("")}</ol>
      <div class="prog-total"><span>Tiempo total</span><span class="mono">${clock(s.segundos)}</span></div></div>`;

  const error = s.estado === "error" ? `<div class="notice bad">${icon("alert")}<span>${esc(s.error || "La corrida se detuvo.")}</span></div>
      ${s.origen === "web" ? `<button class="btn btn-ink btn-block" data-resume>${icon("retry")}Retomar</button>` : ""}` : "";

  const wanted = !s.lista.length && s.piezas.length
    ? `<div class="card"><h3>Lo que va a buscar</h3><ul class="pieces">${s.piezas.map((p) => `<li><span>${esc(p.tipo)}</span><span class="mono muted">${esc(limitText(p.hasta))}</span></li>`).join("")}</ul></div>`
    : "";
  const actions = done ? `<div class="actions"><a class="btn btn-ghost btn-block" href="/nuevo">${icon("plus")}${isExample ? "Probar con mi ambiente" : "Nuevo ambiente"}</a></div>` : "";

  const list = s.lista.length
    ? `<div class="list-head"><h2>La lista de compra</h2><span class="mono muted">${units(s.lista)} productos · ${esc(stores(s.lista))}${s.costo ? ` · esta corrida costó ${money(s.costo)}` : ""}</span></div>
      <div class="prods">${s.lista.map((p) => `
        <article class="card prod">
          <div class="ph">${p.foto ? `<img src="${esc(p.foto)}" alt="${esc(p.nombre)}" loading="lazy">` : ""}${p.cantidad > 1 ? `<span class="qty mono">× ${p.cantidad}</span>` : ""}</div>
          <div class="bd"><span class="k"><span>${esc(p.tipo)}</span><span>${esc(p.tienda)}</span></span>
            <h3 class="n">${esc(p.nombre)}</h3>${cota(p.medidas)}<p class="why">${esc(p.porque)}</p></div>
        </article>`).join("")}</div>
      ${s.faltan && s.faltan.length ? `<div class="notice missing">${icon("alert")}<span>No encontramos nada parecido en el catálogo para: ${s.faltan.map(esc).join("; ")}</span></div>` : ""}`
    : "";

  return { visual, side: progress + error + wanted + actions, list };
}

function renderProject(s, isExample) {
  const back = isExample ? `<a class="link back" href="/#ejemplos">${icon("left")}Ejemplos</a>` : `<a class="link back" href="/ambientes">${icon("left")}Mis ambientes</a>`;
  const status =
    s.estado === "corriendo" || s.estado === "en cola"
      ? `<span class="live"><i></i>${s.estado === "en cola" ? "En espera" : "En curso"}</span>`
      : s.estado === "error"
        ? `<span class="state-bad">Se detuvo</span>`
        : "";
  const inside = (id) => `<a class="link dv-link" href="/dev/${esc(id)}">${icon("layers")}Ver por dentro</a>`;
  const meta = isExample
    ? `<span class="mono">Corrida de ejemplo · ${units(s.lista)} productos</span>${s.corrida ? inside(`terminal-${s.corrida}`) : ""}`
    : `<span class="mono">${esc(day(s.creado))}</span>${s.origen !== "web" ? `<span class="mono">${esc(VIA[s.via] || "")}</span>` : ""}${status}${inside(s.id)}`;
  $app.innerHTML = `${nav("app", isExample ? "" : "ambientes")}
  <main class="page"><div class="wrap enter">
    ${back}
    <h1 class="p-title">“${esc(s.pedido)}”</h1>
    <div class="p-meta">${meta}</div>
    <div class="p-grid"><div class="p-visual" data-r="visual"></div><aside class="side" data-r="side"></aside></div>
    <div data-r="list"></div>
  </div></main>`;
}

const last = {};
function update(s, isExample) {
  const r = regions(s, isExample);
  for (const key of ["visual", "side", "list"]) {
    if (last[key] === r[key]) continue;
    last[key] = r[key];
    const el = $app.querySelector(`[data-r="${key}"]`);
    el.innerHTML = r[key];
    if (key === "visual") wireBeforeAfter(el);
    if (key === "side")
      el.querySelector("[data-resume]")?.addEventListener("click", async (e) => {
        e.currentTarget.disabled = true;
        try {
          await api(`/api/ambientes/${s.id}/retomar`, { method: "POST" });
          project([s.id]);
        } catch (err) {
          toast(err.message);
        }
      });
  }
}

async function project([id]) {
  let s = await api(`/api/ambientes/${id}`);
  for (const k of Object.keys(last)) delete last[k];
  renderProject(s, false);
  update(s, false);
  let status = s.estado;
  let extra = 0; // después de terminar, unos segundos más por si llega la traducción
  const token = routeToken;
  while (token === routeToken && (s.estado === "corriendo" || s.estado === "en cola" || (s.estado === "listo" && !s.traducido && s.lista.length && extra < 20))) {
    await new Promise((r) => setTimeout(r, 1000));
    if (token !== routeToken) return;
    try {
      s = await api(`/api/ambientes/${id}`);
    } catch {
      continue;
    }
    if (s.estado === "listo") extra += 1;
    if (s.estado !== status) {
      status = s.estado;
      for (const k of Object.keys(last)) delete last[k];
      renderProject(s, false);
      if (s.estado === "listo") toast("Tu ambiente está listo");
    }
    update(s, false);
  }
}

async function example([id]) {
  const { ejemplos } = await examples();
  const e = ejemplos.find((x) => x.id === id);
  if (!e) return notFound();
  for (const k of Object.keys(last)) delete last[k];
  const s = { ...e, pasos: [], descarga: e.despues, costo: 0 };
  renderProject(s, true);
  update(s, true);
}

// historial -------------------------------------------------------------------------------------------

const SHOWN = 6; // corridas de la terminal a la vista, antes de "Ver todas"

async function historial() {
  const all = await api("/api/ambientes");
  const rows = all.filter((r) => r.origen === "web");
  const term = all.filter((r) => r.origen !== "web");
  const card = (r) => `
        <a class="hcard" href="/ambientes/${esc(r.id)}">
          <div class="im">${r.imagen ? `<img src="${esc(r.imagen)}" alt="" loading="lazy">` : ""}
            ${r.estado === "corriendo" || r.estado === "en cola" ? `<span class="badge live"><i></i>En curso</span>` : r.estado === "error" ? `<span class="badge bad">Se detuvo</span>` : ""}</div>
          <p class="q">“${esc(r.pedido)}”</p>
          <span class="mono muted">${esc(day(r.creado))}${r.productos ? ` · ${r.productos} productos` : ""}${r.via === "interfaz vieja" ? " · interfaz vieja" : ""}</span>
        </a>`;
  const body = rows.length
    ? `<div class="hist enter d1">${rows.map(card).join("")}</div>`
    : `<div class="empty-state card">${icon("logo")}<h2>Todavía no amoblaste ningún ambiente</h2><p>Subí una foto, contá cómo lo imaginás y la lista te queda guardada acá.</p><a class="btn btn-ink" href="/nuevo">Amoblar mi primer ambiente</a></div>`;
  const others = term.length
    ? `<section class="hist-sec enter d1"><div class="sec-head"><div><h2>Desde la terminal</h2><p>Las corridas de <span class="mono">amoblai amoblar</span> y de la interfaz vieja, en datos/resultados/amoblar</p></div>
        ${term.length > SHOWN ? `<button class="btn btn-ghost btn-sm" data-more>Ver las ${term.length}</button>` : ""}</div>
        <div class="hist" data-term>${term.slice(0, SHOWN).map(card).join("")}</div></section>`
    : "";
  $app.innerHTML = `${nav("app", "ambientes")}
  <main class="page"><div class="wrap">
    <div class="page-head enter"><div><h1>Mis ambientes</h1><p>${rows.length ? `${rows.length} ${rows.length === 1 ? "ambiente" : "ambientes"}` : "Tus pedidos y sus listas quedan guardados acá"}</p></div>
      ${rows.length ? `<a class="btn btn-ink btn-sm" href="/nuevo">${icon("plus")}Nuevo ambiente</a>` : ""}</div>
    ${body}${others}
  </div></main>`;
  $app.querySelector("[data-more]")?.addEventListener("click", (e) => {
    $app.querySelector("[data-term]").innerHTML = term.map(card).join("");
    e.currentTarget.remove();
  });
}

// ajustes ---------------------------------------------------------------------------------------------

function settingsHtml(st) {
  const model = st.modelos[st.imagen];
  const row = (k, what, ph) => {
    const name = NAMES[k];
    const c = st.claves[k];
    return `<div class="key-row"><div class="who"><b>${name}</b><span>${what}</span>
        <div class="st">${!c.cargada ? `<span class="dot bad"></span>Falta`
          : c.valida === false ? `<span class="dot bad"></span>${name} la rechaza <span class="mono muted">···${esc(c.final)}</span>`
          : `<span class="dot ok"></span>${c.valida ? "Funciona" : "Cargada"} <span class="mono muted">···${esc(c.final)}</span>`}</div></div>
      <input type="password" name="${k}" placeholder="${c.cargada ? "Reemplazar clave" : ph}" autocomplete="off" spellcheck="false"></div>`;
  };
  const meter = (k) => {
    const g = st.gasto[k];
    const pct = Math.min(100, (g.gastado / g.tope) * 100);
    return `<div class="meter"><div class="top"><span>${NAMES[k]}</span>
        <label class="mono soft cap">${money(g.gastado)} de US$ <input type="number" name="${k}" value="${g.tope}" min="0.5" max="1000" step="0.5" aria-label="Tope de ${NAMES[k]}, en dólares"></label></div>
      <div class="track"><div class="fill" style="width:${pct.toFixed(1)}%"></div></div></div>`;
  };
  return `
    <form class="card" id="keys"><h2>Claves de API</h2><p>Se guardan en el archivo .env del repo, en esta computadora. No se suben a git.</p>
      ${row("anthropic", "Lee el ambiente, busca y elige los muebles", "sk-ant-…")}
      ${row("openai", "Dibuja el ambiente con gpt-image-2", "sk-…")}
      ${row("fal", "Dibuja el ambiente con Nano Banana 2", "id:secreto")}
      <div class="foot-row"><label class="check"><input type="checkbox" name="recordar" checked>Recordar en esta computadora</label><button class="btn btn-ink btn-sm">Guardar claves</button></div>
    </form>
    <section class="card"><h2>Imagen</h2><p>El modelo que dibuja el ambiente. Si la imagen no conserva el ambiente, se vuelve a pedir hasta el tope de intentos.</p>
      <div class="pref-row"><div class="who"><b>Modelo</b><span>Usa la clave de ${NAMES[model.cuenta]}</span></div>
        <div class="seg" data-imagen>${Object.entries(st.modelos).map(([k, m]) => `<button type="button" class="${k === st.imagen ? "on" : ""}" data-v="${esc(k)}">${esc(m.nombre)}</button>`).join("")}</div></div>
      <div class="pref-row"><div class="who"><b>Intentos</b><span>El proyecto usa ${st.intentos_proyecto}. Cada intento cuesta unos ${Math.round(model.intento * 100)} centavos</span></div>
        <div class="seg num-seg" data-intentos>${[1, 2, 3, 4, 5].map((n) => `<button type="button" class="${n === st.intentos ? "on" : ""}" data-n="${n}">${n}</button>`).join("")}</div></div>
    </section>
    <form class="card" id="caps"><h2>Gasto</h2><p>Lo que lleva gastado esta web en cada cuenta, contra un tope que elegís acá: si una corrida lo pasaría, se detiene antes de pagar. Se lleva aparte del de la terminal.</p>
      ${meter("anthropic")}${meter("openai")}${meter("fal")}
      <div class="foot-row"><span class="soft small">Una corrida cuesta entre US$ 0,20 y 0,80</span><button class="btn btn-ink btn-sm">Guardar topes</button></div>
    </form>`;
}

async function ajustes() {
  const st = await api("/api/estado");
  $app.innerHTML = `${nav("app", "ajustes")}
  <main class="page"><div class="wrap">
    <div class="page-head enter"><div><h1>Ajustes</h1><p>Las claves para usar los modelos, el modelo de la imagen y lo que se lleva gastado.</p></div></div>
    <div class="settings enter d1" id="settings">${settingsHtml(st)}</div>
  </div></main>`;
  const json = (body) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const save = async (path, body, message) => {
    try {
      const st2 = await api(path, json(body));
      document.getElementById("settings").innerHTML = settingsHtml(st2);
      wire();
      toast(message(st2));
    } catch (err) {
      toast(err.message);
    }
  };
  const wire = () => {
    document.querySelectorAll("[data-intentos] button").forEach((b) =>
      b.addEventListener("click", () =>
        save("/api/preferencias", { intentos: Number(b.dataset.n) }, (s) => (s.intentos === 1 ? "Un solo intento por imagen" : `Hasta ${s.intentos} intentos por imagen`)),
      ),
    );
    document.querySelectorAll("[data-imagen] button").forEach((b) =>
      b.addEventListener("click", () => save("/api/preferencias", { imagen: b.dataset.v }, (s) => `La imagen la dibuja ${s.modelos[s.imagen].nombre}`)),
    );
    document.getElementById("caps").addEventListener("submit", (e) => {
      e.preventDefault();
      const f = e.currentTarget;
      save("/api/preferencias", { topes: Object.fromEntries(Object.keys(NAMES).map((k) => [k, f[k].value])) }, () => "Topes guardados");
    });
    document.getElementById("keys").addEventListener("submit", (e) => {
      e.preventDefault();
      const f = e.currentTarget;
      const body = { ...Object.fromEntries(Object.keys(NAMES).map((k) => [k, f[k].value])), recordar: f.recordar.checked };
      const sent = Object.keys(NAMES).filter((k) => body[k].trim());
      if (!sent.length) return toast("Escribí al menos una clave");
      save("/api/claves", body, (s) => {
        const rejected = sent.filter((k) => s.claves[k].valida === false);
        return rejected.length ? `${rejected.map((k) => NAMES[k]).join(" y ")} ${rejected.length > 1 ? "rechazan" : "rechaza"} esa clave` : body.recordar ? "Claves guardadas" : "Claves cargadas para esta sesión";
      });
    });
  };
  wire();
}

// por dentro: cada etapa de una corrida, con lo que recibió y lo que devolvió --------------------------

const fmt = (n, d = 0) => Number(n ?? 0).toLocaleString("es-AR", { minimumFractionDigits: d, maximumFractionDigits: d });
const secs = (x) => (x == null ? "" : x >= 60 ? clock(x) : `${fmt(x, 1)} s`);
const usd = (x) => (x ? money(x) : "gratis");
const tokens = (t) => (t ? `${fmt(t.entrada)} tokens de entrada · ${fmt(t.salida)} de salida${t.pensando ? `, ${fmt(t.pensando)} pensando` : ""}` : "");
const promptLink = (name) => (name ? `<a class="plink" href="/prompt/${esc(name)}" target="_blank" rel="noopener">${esc(name)}</a>` : "");
const both = (es, en) =>
  es && es !== en ? `<p>${esc(es)}</p><details class="orig"><summary>Original, como lo devolvió el modelo</summary><p>${esc(en)}</p></details>` : `<p>${esc(en)}</p>`;
const stageMeta = (parts) => `<div class="dv-meta mono">${parts.filter(Boolean).join('<span class="sep">·</span>')}</div>`;
const llmMeta = (e, ...extra) => stageMeta([esc(e.modelo || "plantilla, sin LLM"), promptLink(e.prompt), usd(e.costo), secs(e.segundos), ...extra]);
const stageHead = (n, title, what, meta = "") =>
  `<div class="dv-head"><span class="mono dv-n">${n}</span><div><h2>${title}</h2><p>${what}</p>${meta}</div></div>`;

function devSummary(d) {
  const e = d.etapas;
  const img = e.imagen || {};
  const tries = (img.intentos || []).length;
  const rows = [
    ["01", "Plan", "plan", e.plan && esc(e.plan.modelo), e.plan && promptLink(e.plan.prompt), e.plan?.costo, e.plan?.segundos],
    ["02", "Búsqueda", "busqueda", e.busqueda && `${esc(e.busqueda.metodo)}, local`, "", 0, e.busqueda?.segundos],
    ["03", "Elección", "eleccion", e.eleccion && esc(e.eleccion.modelo), e.eleccion && promptLink(e.eleccion.prompt), e.eleccion?.costo, e.eleccion?.segundos],
    ["04", "Escena", "escena", e.escena && esc(e.escena.modelo || "plantilla, sin LLM"), e.escena && promptLink(e.escena.prompt), e.escena?.costo, e.escena?.segundos],
    ["05", "Imagen", "imagen", e.imagen && (img.en_curso ? "en curso" : `${esc(img.modelo || "")}${tries > 1 ? ` · ${tries} intentos` : ""}`), "", img.costo, img.segundos],
  ];
  if (e.traduccion) rows.push(["", "Traducción", "", `${esc(e.traduccion.modelo)} · la agrega la web`, "", e.traduccion.costo, null]);
  // las corridas de la terminal copiadas de otra no tienen un tiempo de reloj: la suma de las etapas
  const total = d.segundos || rows.reduce((n, r) => n + (r[6] || 0), 0);
  return `<div class="card dv-sum"><table>
    <thead><tr><th>Etapa</th><th>Modelo</th><th>Prompt</th><th class="r">Costo</th><th class="r">Tiempo</th></tr></thead>
    <tbody>${rows.map(([n, name, anchor, model, prompt, cost, time]) => model
      ? `<tr><td>${anchor ? `<a href="#${anchor}">` : ""}<span class="mono muted">${n}</span> ${name}${anchor ? "</a>" : ""}</td><td class="mono">${model}</td><td class="mono">${prompt || ""}</td><td class="mono r">${usd(cost)}</td><td class="mono r">${secs(time)}</td></tr>`
      : `<tr class="off"><td><span class="mono">${n}</span> ${name}</td><td colspan="4" class="mono">${d.estado === "corriendo" || d.estado === "en cola" ? "todavía no" : "no llegó"}</td></tr>`).join("")}</tbody>
    <tfoot><tr><td>Total</td><td></td><td></td><td class="mono r">${money(d.costo)}</td><td class="mono r">${clock(total)}</td></tr></tfoot>
  </table></div>`;
}

function devPlan(p, d) {
  return `<section class="dv-stage" id="plan">
    ${stageHead("01", "Plan", "Mira la foto y el pedido, describe el ambiente y decide qué piezas buscar: el tipo de mueble, las medidas máximas y una ficha escrita como las del catálogo, que es lo que se busca.", llmMeta(p, tokens(p.tokens)))}
    <div class="dv-split">
      <div class="dv-photos">${d.antes ? `<img src="${esc(d.antes.replace("w=1600", "w=960"))}" alt="La foto del ambiente vacío">` : ""}${d.vistas.map((v) => `<img src="${esc(v)}" alt="Otra vista del mismo ambiente">`).join("")}</div>
      <div class="card dv-read"><h3>Cómo leyó el ambiente</h3>${both(p.ambiente_es, p.ambiente)}</div>
    </div>
    <h3 class="dv-sub">${p.piezas.length} ${p.piezas.length === 1 ? "pieza" : "piezas"}</h3>
    <ol class="dv-pieces">${p.piezas.map((x, i) => `
      <li class="card"><span class="mono dv-i">${i + 1}</span>
        <div class="dv-pc">
          <p class="dv-pn">${esc(x.pieza)}</p>
          <div class="dv-tags">${(x.tipos.length ? x.tipos : ["a elegir"]).map((t) => `<span class="kchip">${esc(t)}</span>`).join("")}${Object.keys(x.hasta).length ? `<span class="mono muted">${esc(limitText(x.hasta))}</span>` : ""}</div>
          <p class="soft">${esc(x.porque)}</p>
          <details><summary>La ficha que se busca</summary><pre>${esc(x.ficha)}</pre></details>
        </div></li>`).join("")}</ol>
    ${p.desconocidos.length ? `<div class="notice">${icon("alert")}<span>Tipos que no están en el catálogo y se descartaron: ${p.desconocidos.map(esc).join(", ")}</span></div>` : ""}
  </section>`;
}

const devCand = (c) => `<article class="dv-cand ${c.elegido ? "pick" : ""}">
    <div class="ph">${c.foto ? `<img src="${esc(c.foto)}" alt="" loading="lazy">` : ""}<span class="pos mono">${c.puesto}</span>${c.elegido ? `<span class="ok" title="El elegido">${icon("check")}</span>` : ""}</div>
    <div class="bd">
      <span class="k"><span>${esc(c.tipo)}</span><span>${esc(c.tienda)}</span></span>
      <h4 class="n" title="${esc(c.nombre_completo)}">${esc(c.nombre)}</h4>
      ${cota(c.medidas)}
      <span class="mono muted">${c.puntaje != null ? `puntaje ${fmt(c.puntaje, 2)}` : ""}${c.ranking ? ` · ${c.ranking}.º para el modelo` : ""}</span>
      <details><summary>Descripción</summary><pre>${esc(c.descripcion)}</pre></details>
    </div></article>`;

function devSearch(b) {
  return `<section class="dv-stage" id="busqueda">
    ${stageHead("02", "Búsqueda", `Para cada pieza, los ${b.por_pieza} productos del catálogo que mejor responden a su ficha, por texto y por foto, sin pasarse de las medidas. Corre en esta computadora, sin LLM.`, stageMeta([esc(b.metodo), "gratis", secs(b.segundos)]))}
    ${b.piezas.map((p, i) => `
      <div class="dv-piece">
        <p class="dv-ph"><span class="mono muted">Pieza ${i + 1}</span>${esc(p.pieza)}</p>
        <div class="dv-cands">${p.candidatos.map(devCand).join("")}</div>
      </div>`).join("")}
    ${b.vacias.length ? `<div class="notice missing">${icon("alert")}<span>Sin candidatos en el catálogo, la corrida sigue sin ellas: ${b.vacias.map(esc).join("; ")}</span></div>` : ""}
  </section>`;
}

function devChoice(c) {
  return `<section class="dv-stage" id="eleccion">
    ${stageHead("03", "Elección", `Ve la foto del ambiente y las fotos de todos los candidatos${c.imagenes ? ` (${c.imagenes} imágenes)` : ""}, y elige uno por pieza, y cuántos, para que combinen entre sí.`, llmMeta(c, tokens(c.tokens)))}
    <div class="card dv-read"><h3>La idea</h3>${both(c.idea_es, c.idea)}</div>
    <ol class="dv-picks">${c.elecciones.map((x, i) => `
      <li class="card">
        <div class="ph">${x.foto && x.cantidad ? `<img src="${esc(x.foto)}" alt="" loading="lazy">` : ""}</div>
        <div class="dv-pc">
          <span class="mono muted">Pieza ${i + 1} · ${x.cantidad ? `${x.puesto ? `${x.puesto}.º de la búsqueda` : "elegido"}${x.cantidad > 1 ? ` · × ${x.cantidad}` : ""}` : "la deja afuera"}</span>
          <h4>${esc(x.cantidad ? x.nombre : x.pieza)}</h4>
          ${x.ranking.length ? `<p class="mono muted">Su orden, por puesto en la búsqueda: ${x.ranking.map((r) => `<span title="${esc(r.nombre)}">${r.puesto ?? "?"}</span>`).join(" › ")}</p>` : ""}
          ${both(x.porque_es, x.porque)}
        </div></li>`).join("")}</ol>
  </section>`;
}

function devScene(s) {
  return `<section class="dv-stage" id="escena">
    ${stageHead("04", "Escena", s.modelo ? "Un LLM escribe el texto para el modelo de imagen." : "El texto para el modelo de imagen sale de una plantilla, con el pedido y la lista: no hace falta otro LLM.", llmMeta(s))}
    <pre class="card dv-prompt">${esc(s.texto)}</pre>
    <p class="caption">Junto con este texto, el modelo de imagen recibe la foto del ambiente y la foto de cada producto elegido, en ese orden.</p>
  </section>`;
}

function devImage(m) {
  const u = m.umbral;
  const figure = (t, label) => `
    <figure class="card dv-try">
      <div class="ph">${t.foto ? `<img src="${esc(t.foto)}" alt="${esc(label)}" loading="lazy">` : ""}</div>
      <figcaption>
        <div class="top"><b>${esc(label)}</b>${t.ok === true ? `<span class="st"><span class="dot ok"></span>Conserva el ambiente</span>` : t.ok === false ? `<span class="st no"><span class="dot bad"></span>No pasa el control</span>` : m.en_curso ? `<span class="st"><span class="dot"></span>Revisando</span>` : ""}</div>
        ${t.puntos != null ? `<dl class="mono">
          <dt>Puntos SIFT</dt><dd>${fmt(t.puntos)} <span class="muted">mín. ${u.puntos}</span></dd>
          <dt>Desplazamiento</dt><dd>${t.desplazamiento != null ? fmt(t.desplazamiento, 4) : "—"} <span class="muted">máx. ${fmt(u.desplazamiento, 2)}</span></dd>
          <dt>Reencontrados</dt><dd>${fmt((t.reencontrados || 0) * 100)} %</dd>
          <dt>SSIM</dt><dd>${fmt(t.ssim, 2)}</dd>
          ${t.costo != null ? `<dt>Costo</dt><dd>${usd(t.costo)}</dd>` : ""}</dl>` : ""}
      </figcaption>
    </figure>`;
  const tries = m.intentos.length ? m.intentos.map((t, i) => figure(t, `Intento ${i + 1}`)).join("") : m.final ? figure({ foto: m.final }, "La imagen") : "";
  return `<section class="dv-stage" id="imagen">
    ${stageHead("05", "Imagen", `Cada intento pasa un control contra la foto original: sus puntos SIFT tienen que volver a aparecer (al menos ${u.puntos}) sin moverse (desplazamiento mediano de hasta ${fmt(u.desplazamiento, 2)}). Si no pasa, se pide de nuevo; si ninguno pasa, queda el que conserva más puntos.`,
      m.en_curso ? stageMeta(["en curso"]) : stageMeta([esc(`${m.modelo || m.generador || ""}${m.calidad ? `, calidad ${m.calidad}` : ""}`), usd(m.costo), m.segundos != null ? `último intento ${secs(m.segundos)}` : ""]))}
    ${m.pendiente ? `<div class="notice">${icon("alert")}<span>Generador manual: la corrida dejó la carpeta para pegar en ChatGPT o Gemini, sin imagen.</span></div>` : ""}
    <div class="dv-tries">${tries}</div>
  </section>`;
}

const devFiles = (d) => `<section class="dv-stage" id="archivos">
    ${stageHead("", "Archivos", `Cada etapa deja su archivo en <span class="mono">${esc(d.carpeta)}</span>. Si la corrida se corta, se retoma desde ahí: lo pagado no se repite.`)}
    <div class="dv-files">${d.archivos.map((f) => `<a class="mono" href="${esc(f.url)}" target="_blank" rel="noopener">${icon("file")}${esc(f.nombre)}</a>`).join("")}</div>
  </section>`;

function renderDev(d) {
  const e = d.etapas;
  const running = d.estado === "corriendo" || d.estado === "en cola";
  const state = running ? `<span class="live"><i></i>En curso</span>` : d.estado === "error" ? `<span class="state-bad">Se detuvo</span>` : "";
  $app.innerHTML = `${nav("app")}
  <main class="page dev"><div class="wrap">
    <div class="dv-top"><a class="link" href="/ambientes/${esc(d.id)}">${icon("left")}Ver como cliente</a><a class="link" href="/dev">Todas las corridas</a></div>
    <span class="mono dv-eyebrow">Por dentro</span>
    <h1 class="p-title">“${esc(d.pedido)}”</h1>
    <div class="p-meta"><span class="mono">${esc(day(d.creado))}</span><span class="mono">${esc(VIA[d.via] || "")}</span><span class="mono">${money(d.costo)} · ${clock(d.segundos)}</span>${state}</div>
    ${d.error ? `<div class="notice bad dv-err">${icon("alert")}<span>${esc(d.error)}${d.detalle ? `<code class="mono">${esc(d.detalle)}</code>` : ""}</span></div>` : ""}
    ${devSummary(d)}
    ${e.plan ? devPlan(e.plan, d) : ""}${e.busqueda ? devSearch(e.busqueda) : ""}${e.eleccion ? devChoice(e.eleccion) : ""}${e.escena ? devScene(e.escena) : ""}${e.imagen ? devImage(e.imagen) : ""}
    ${running ? `<p class="caption dv-wait">${icon("spin")}Las etapas que faltan aparecen acá a medida que terminan</p>` : ""}
    ${devFiles(d)}
  </div></main>`;
}

async function devRun([id]) {
  let d = await api(`/api/dev/${id}`);
  renderDev(d);
  const sig = (x) => JSON.stringify([x.estado, Object.keys(x.etapas), (x.etapas.imagen?.intentos || []).map((t) => t.ok), !!x.etapas.traduccion]);
  let last = sig(d);
  const token = routeToken;
  while (token === routeToken && (d.estado === "corriendo" || d.estado === "en cola")) {
    await new Promise((r) => setTimeout(r, 2000));
    if (token !== routeToken) return;
    try {
      d = await api(`/api/dev/${id}`);
    } catch {
      continue;
    }
    if (sig(d) !== last) {
      last = sig(d);
      renderDev(d);
    }
  }
}

async function devIndex() {
  const rows = await api("/api/ambientes");
  $app.innerHTML = `${nav("app")}
  <main class="page dev"><div class="wrap">
    <div class="page-head enter"><div><span class="mono dv-eyebrow">Por dentro</span><h1>Todas las corridas</h1><p>${rows.length} corridas, de la web, de la terminal y de la interfaz vieja. Cada una muestra sus etapas: plan, búsqueda, elección, escena e imagen.</p></div></div>
    <div class="card dv-list enter d1">${rows.map((r) => `
      <a class="dv-row" href="/dev/${esc(r.id)}">
        <span class="im">${r.imagen ? `<img src="${esc(r.imagen.replace("w=720", "w=240"))}" alt="" loading="lazy">` : ""}</span>
        <span class="q">${esc(r.pedido)}</span>
        <span class="mono muted">${esc(r.via)}</span>
        <span class="mono muted">${esc(day(r.creado))}</span>
        <span class="mono muted r">${r.productos} prod.</span>
        <span class="mono r">${money(r.costo)}</span>
        <span class="st">${r.estado === "error" ? `<span class="state-bad">Se detuvo</span>` : r.estado !== "listo" ? `<span class="live"><i></i>En curso</span>` : ""}</span>
      </a>`).join("")}</div>
  </div></main>`;
}

function notFound() {
  $app.innerHTML = `${nav("app")}<main class="page"><div class="wrap"><div class="empty-state card">${icon("logo")}<h2>No encontramos esta página</h2><p>Puede que el ambiente se haya borrado o que el enlace esté mal.</p><a class="btn btn-ink" href="/">Ir al inicio</a></div></div></main>`;
}

// el router -------------------------------------------------------------------------------------------

const ROUTES = [
  [/^\/$/, landing],
  [/^\/nuevo$/, nuevo],
  [/^\/ambientes$/, historial],
  [/^\/ambientes\/([\w.-]+)$/, project],
  [/^\/ejemplos\/([\w-]+)$/, example],
  [/^\/ajustes$/, ajustes],
  [/^\/dev$/, devIndex],
  [/^\/dev\/([\w.-]+)$/, devRun],
];
let routeToken = 0;

async function render() {
  routeToken += 1;
  const path = location.pathname.replace(/\/+$/, "") || "/";
  const hit = ROUTES.find(([re]) => re.test(path));
  try {
    if (hit) await hit[1](path.match(hit[0]).slice(1));
    else notFound();
  } catch (err) {
    console.error(err);
    if (String(err.message).includes("Not Found")) notFound();
    else toast(err.message);
  }
  if (location.hash) document.querySelector(location.hash)?.scrollIntoView();
}

function navigate(to) {
  const url = new URL(to, location.origin);
  if (url.pathname === location.pathname && url.hash) {
    history.pushState(null, "", url);
    document.querySelector(url.hash)?.scrollIntoView({ behavior: "smooth" });
    return;
  }
  history.pushState(null, "", url);
  window.scrollTo(0, 0);
  render();
}

document.addEventListener("click", (e) => {
  const a = e.target.closest("a[href]");
  if (!a || a.target || a.hasAttribute("download") || e.metaKey || e.ctrlKey || e.shiftKey) return;
  const href = a.getAttribute("href");
  if (href.startsWith("http") || href.startsWith("/corridas/") || href.startsWith("/static/") || href.startsWith("/prompt/")) return;
  e.preventDefault();
  navigate(href.startsWith("#") ? location.pathname + href : href);
});
window.addEventListener("popstate", render);
window.addEventListener("scroll", () => document.querySelector(".nav")?.classList.toggle("scrolled", scrollY > 8), { passive: true });

render();
