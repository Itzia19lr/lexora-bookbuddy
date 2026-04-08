import streamlit as st
import pandas as pd
import numpy as np
import pickle
import json
from scipy.sparse import load_npz
import os
from dotenv import load_dotenv
from openai import OpenAI
import random
import base64
import unicodedata

try:
    from deep_translator import GoogleTranslator
    DEEP_TRANSLATOR_OK = True
except ImportError:
    DEEP_TRANSLATOR_OK = False

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

st.set_page_config(
    page_title="Lexora - Descubre tu próximo libro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_api_key():
    try: return st.secrets["OPENAI_API_KEY"]
    except: return os.getenv("OPENAI_API_KEY", "")

API_KEY = get_api_key()
client  = OpenAI(api_key=API_KEY) if API_KEY else None

def file_to_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

LOGO_B64  = file_to_b64("logo_lexora.png")
FONDO_B64 = file_to_b64("fondo_libros.png")

def limpiar_texto(texto):
    if not texto or pd.isna(texto): return ""
    try: return unicodedata.normalize('NFC', str(texto))
    except: return str(texto)

COLORES_GENERO = {
    "fantasy":{"bg":"#2d1b69","accent":"#a78bfa","label":"Fantasía"},
    "thriller":{"bg":"#111111","accent":"#ef4444","label":"Thriller"},
    "mystery":{"bg":"#1f2937","accent":"#60a5fa","label":"Misterio"},
    "romance":{"bg":"#9f1239","accent":"#fda4af","label":"Romance"},
    "horror":{"bg":"#0a0a0a","accent":"#ff4d4d","label":"Terror"},
    "science fiction":{"bg":"#0f172a","accent":"#38bdf8","label":"Ciencia Ficción"},
    "science+fiction":{"bg":"#0f172a","accent":"#38bdf8","label":"Ciencia Ficción"},
    "fiction":{"bg":"#1e3a5f","accent":"#93c5fd","label":"Ficción"},
    "literary fiction":{"bg":"#1e3a5f","accent":"#93c5fd","label":"Ficción Literaria"},
    "contemporary":{"bg":"#0f3460","accent":"#e94560","label":"Contemporáneo"},
    "contemporary fiction":{"bg":"#0f3460","accent":"#e94560","label":"Contemporáneo"},
    "historical fiction":{"bg":"#44271f","accent":"#f59e0b","label":"Ficción Histórica"},
    "historical+fiction":{"bg":"#44271f","accent":"#f59e0b","label":"Ficción Histórica"},
    "adventure":{"bg":"#14532d","accent":"#4ade80","label":"Aventura"},
    "young adult":{"bg":"#4a1d96","accent":"#f0abfc","label":"Jóvenes Adultos"},
    "young+adult":{"bg":"#4a1d96","accent":"#f0abfc","label":"Jóvenes Adultos"},
    "dystopia":{"bg":"#1c1917","accent":"#fb923c","label":"Distopía"},
    "graphic novel":{"bg":"#1e1b4b","accent":"#818cf8","label":"Novela Gráfica"},
    "classics":{"bg":"#3b2800","accent":"#d97706","label":"Clásicos"},
    "poetry":{"bg":"#2e1065","accent":"#d946ef","label":"Poesía"},
    "short stories":{"bg":"#312e81","accent":"#a5b4fc","label":"Cuentos"},
    "history":{"bg":"#78350f","accent":"#fcd34d","label":"Historia"},
    "philosophy":{"bg":"#334155","accent":"#94a3b8","label":"Filosofía"},
    "psychology":{"bg":"#4c1d95","accent":"#c4b5fd","label":"Psicología"},
    "biography":{"bg":"#374151","accent":"#d1d5db","label":"Biografía"},
    "autobiography":{"bg":"#374151","accent":"#d1d5db","label":"Autobiografía"},
    "business":{"bg":"#064e3b","accent":"#6ee7b7","label":"Negocios"},
    "memoir":{"bg":"#7c2d12","accent":"#fdba74","label":"Memorias"},
    "self help":{"bg":"#065f46","accent":"#34d399","label":"Autoayuda"},
    "self-help":{"bg":"#065f46","accent":"#34d399","label":"Autoayuda"},
    "science":{"bg":"#0c4a6e","accent":"#38bdf8","label":"Ciencia"},
    "nonfiction":{"bg":"#1f2937","accent":"#9ca3af","label":"No Ficción"},
    "non-fiction":{"bg":"#1f2937","accent":"#9ca3af","label":"No Ficción"},
    "true crime":{"bg":"#1a1a2e","accent":"#e94560","label":"Crimen Real"},
    "true+crime":{"bg":"#1a1a2e","accent":"#e94560","label":"Crimen Real"},
    "travel":{"bg":"#0c4a6e","accent":"#67e8f9","label":"Viajes"},
    "cooking":{"bg":"#451a03","accent":"#fb923c","label":"Cocina"},
    "art":{"bg":"#1e1b4b","accent":"#c084fc","label":"Arte"},
    "religion":{"bg":"#1c1917","accent":"#fbbf24","label":"Religión"},
    "humor":{"bg":"#78350f","accent":"#fbbf24","label":"Humor"},
    "children":{"bg":"#5b21b6","accent":"#fdba74","label":"Infantil"},
    "politics":{"bg":"#1e3a5f","accent":"#f87171","label":"Política"},
    "economics":{"bg":"#064e3b","accent":"#6ee7b7","label":"Economía"},
}
COLOR_FALLBACK = {"bg":"#1e293b","accent":"#94a3b8","label":"Libro"}

def crear_svg_portada(label, bg, accent):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="300" height="420" viewBox="0 0 300 420">
  <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{bg}"/><stop offset="100%" stop-color="#0a0a0a"/>
  </linearGradient></defs>
  <rect width="300" height="420" fill="url(#g)"/>
  <rect x="14" y="14" width="272" height="392" fill="none" stroke="{accent}" stroke-width="1.5" opacity="0.45"/>
  <text x="150" y="185" font-family="Arial" font-size="58" text-anchor="middle" opacity="0.85">📖</text>
  <line x1="55" y1="215" x2="245" y2="215" stroke="{accent}" stroke-width="1" opacity="0.5"/>
  <text x="150" y="255" font-family="Arial,sans-serif" font-size="19" font-weight="bold"
        text-anchor="middle" fill="{accent}" opacity="0.95">{label}</text>
  <line x1="55" y1="275" x2="245" y2="275" stroke="{accent}" stroke-width="1" opacity="0.3"/>
</svg>"""
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

def obtener_portada_svg(genero):
    if genero:
        k = str(genero).strip().lower()
        cfg = COLORES_GENERO.get(k) or COLORES_GENERO.get(k.replace(' ','+'))
        if cfg: return crear_svg_portada(cfg["label"], cfg["bg"], cfg["accent"])
    c = COLOR_FALLBACK
    return crear_svg_portada(c["label"], c["bg"], c["accent"])

def obtener_portada(url, genero=None):
    if url and pd.notna(url) and str(url).strip().startswith("http"):
        return str(url).strip()
    return obtener_portada_svg(genero)

def mostrar_portada(url, genero=None, use_container_width=False, width=None):
    p = obtener_portada(url, genero)
    try:
        if width: st.image(p, width=width)
        else: st.image(p, use_container_width=use_container_width)
    except:
        st.image(obtener_portada_svg(genero), use_container_width=use_container_width)

st.markdown("""
<style>
html, body, [class*="css"] { background-color: #141414 !important; color: white; }
[data-testid="stAppViewContainer"] { background-color: #141414 !important; }
[data-testid="stHeader"] { background: transparent !important; }
.block-container {
    padding-top: 0 !important; padding-left: 3rem !important;
    padding-right: 3rem !important; max-width: 1400px !important;
}
.hero-outer {
    margin-left: -3rem; margin-right: -3rem;
    width: calc(100% + 6rem); position: relative; min-height: 540px; overflow: hidden;
}
.hero-bg { position: absolute; inset: 0; background-size: cover; background-position: center top; }
.hero-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(to bottom,rgba(0,0,0,0.15) 0%,rgba(0,0,0,0.45) 50%,rgba(20,20,20,0.98) 100%);
}
.hero-logo { position: absolute; top: 2rem; left: 3rem; z-index: 3; }
.hero-logo img { height: 48px; }
.hero-body { position: absolute; bottom: 2.5rem; left: 3rem; right: 3rem; z-index: 3; }
.hero-title {
    font-size: 3.4rem; font-weight: 900; color: white;
    line-height: 1.05; margin-bottom: 0.5rem;
    text-shadow: 0 2px 16px rgba(0,0,0,0.9);
}
.hero-subtitle {
    font-size: 1.05rem; color: #e5e7eb; max-width: 640px;
    text-shadow: 0 1px 8px rgba(0,0,0,0.9); margin-bottom: 0;
}
.hero-btn-row { margin-top: 1.2rem; margin-bottom: 0.8rem; }
.section-title { font-size: 1.5rem; font-weight: 800; color: white; margin: 1.4rem 0 0.8rem 0; }
.rank-number {
    font-size: 4rem; font-weight: 900;
    color: rgba(255,255,255,0.12); line-height: 0.9; margin-bottom: -0.5rem;
}
[data-testid="stImage"] img {
    width: 100% !important; height: 260px !important;
    object-fit: cover !important; border-radius: 8px !important; display: block;
    pointer-events: none !important;
}
.poster-title {
    font-size: 0.88rem; font-weight: 700; color: white;
    height: 2.6rem; margin-top: 0.4rem; line-height: 1.3; overflow: hidden;
}
.poster-author {
    font-size: 0.82rem; color: #9ca3af; margin-bottom: 0.4rem;
    overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
}
div[data-testid="stButton"] > button {
    background: #E50914 !important; color: white !important;
    border: none !important; border-radius: 6px !important; font-weight: 600 !important;
}
div[data-testid="stButton"] > button:hover { background: #c0070f !important; }
.arrow-btn div[data-testid="stButton"] > button {
    background: rgba(255,255,255,0.08) !important;
    font-size: 1.5rem !important; border-radius: 50% !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    width: 44px !important; min-height: 44px !important; padding: 0 !important;
}
.arrow-btn div[data-testid="stButton"] > button:hover { background: rgba(255,255,255,0.18) !important; }
hr { border-color: rgba(255,255,255,0.08) !important; }
.stMarkdown, .stText, p, label, span, h1, h2, h3 { color: white !important; }
div[data-testid="stExpander"] details {
    background: rgba(255,255,255,0.04);
    border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);
}
div[data-testid="stInfo"] { background: rgba(229,9,20,0.12); color: white; }
section[data-testid="stSidebar"] { display: none; }
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.05); border-radius: 10px; padding: 0.6rem;
}
.carousel-dots { text-align: center; margin-top: 0.5rem; }
.dot { display:inline-block; width:8px; height:8px; border-radius:50%;
       background:rgba(255,255,255,0.25); margin:0 3px; }
.dot.active { background:#E50914; width:22px; border-radius:4px; }
.page-logo { margin-bottom: 0.8rem; margin-top: 0.6rem; }
.agotado-box {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px; padding: 2rem; text-align: center; margin: 1rem 0;
}
.agotado-titulo { font-size: 1.1rem; font-weight: 700; color: white; margin-bottom: 0.5rem; }
.agotado-sub { font-size: 0.9rem; color: #9ca3af; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    libros   = pd.read_csv('data/libros.csv', encoding='utf-8')
    usuarios = pd.read_csv('data/usuarios.csv', encoding='utf-8')
    ratings  = pd.read_csv('data/ratings.csv', encoding='utf-8')
    pop      = pd.read_csv('data/popularidad_libros.csv', encoding='utf-8')
    for df in [libros, usuarios, ratings, pop]:
        df.columns = [c.strip() for c in df.columns]
    for col in ['autor', 'titulo']:
        if col in libros.columns:
            libros[col] = libros[col].apply(limpiar_texto)
    with open('data/generos.json') as f: g = json.load(f)
    try:
        with open('data/stats_paginas.json') as f: sp = json.load(f)
    except: sp = {}
    try:
        with open('data/stats_anos.json') as f: sa = json.load(f)
    except: sa = {}
    return libros, usuarios, ratings, pop, g, sp, sa

@st.cache_resource
def cargar_modelos():
    sc = np.load('models/similitud_contenido.npy')
    si = np.load('models/similitud_item_item.npy')
    mc = load_npz('models/matriz_completa.npz')
    with open('models/mapeos.pkl','rb') as f: m = pickle.load(f)
    return sc, si, mc, m

libros_df, usuarios_df, ratings_df, popularidad_df, generos_list, stats_paginas, stats_anos = cargar_datos()
similitud_contenido, similitud_item_item, matriz_completa, mapeos = cargar_modelos()

user_to_idx = mapeos['user_to_idx']
book_to_idx = mapeos['book_to_idx']
idx_to_book = mapeos['idx_to_book']

_libros_reset = libros_df.reset_index(drop=True)
bookid_to_row = {row['book_id']: idx for idx, row in _libros_reset.iterrows()}

_COL_ANO = None
for _c in _libros_reset.columns:
    if _c.strip().lower() in ('ano', 'año', 'ano_publicacion', 'año_publicacion'):
        _COL_ANO = _c
        break

def get_ano(libro):
    if _COL_ANO:
        val = libro.get(_COL_ANO) if isinstance(libro, pd.Series) else getattr(libro, _COL_ANO, None)
        if val is not None and pd.notna(val):
            try: return int(float(val))
            except: pass
    for col in ['ano', 'año', 'ano_publicacion', 'año_publicacion']:
        val = libro.get(col) if isinstance(libro, pd.Series) else getattr(libro, col, None)
        if val is not None and pd.notna(val):
            try: return int(float(val))
            except: pass
    return "—"

def get_col_ano_df(df):
    for c in df.columns:
        if c.strip().lower() in ('ano', 'año', 'ano_publicacion', 'año_publicacion'):
            return c
    return None

def logo_pagina(h=38):
    if LOGO_B64:
        st.markdown(
            f'<div class="page-logo"><img src="data:image/png;base64,{LOGO_B64}" height="{h}"></div>',
            unsafe_allow_html=True)

def _ck(p, t): return f"{p}_{hash(str(t))}"

def _openai(texto, system, max_tokens=400):
    if not API_KEY or not client: return None, "sin key"
    try:
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"system","content":system},{"role":"user","content":texto}],
            max_tokens=max_tokens, temperature=0.2)
        return r.choices[0].message.content.strip(), None
    except Exception as e: return None, str(e)

def _google(texto):
    if not DEEP_TRANSLATOR_OK: return None, "no instalado"
    try: return GoogleTranslator(source='auto', target='es').translate(texto[:4500]), None
    except Exception as e: return None, str(e)

def traducir_descripcion(texto):
    if not texto or pd.isna(texto): return "Sin descripción disponible."
    k = _ck("d", texto)
    if k in st.session_state: return st.session_state[k]
    r, _ = _openai(
        f"Traduce al español de México:\n\n{texto}",
        "Traduce al español de México textos de contraportada. Tono natural. Traducción COMPLETA.", 500)
    if not r: r, _ = _google(texto)
    if not r: r = texto
    st.session_state[k] = r
    return r

def traducir_titulo(titulo):
    """Traduce título al español con caché en session_state."""
    if not titulo or pd.isna(titulo): return titulo
    k = _ck("t", titulo)
    if k in st.session_state: return st.session_state[k]
    r, _ = _openai(
        f"Traduce este título de libro al español de México. Solo devuelve el título traducido, sin explicaciones ni comillas:\n\n{titulo}",
        "Eres un traductor. Solo devuelves el título traducido, nada más.", 30)
    if not r: r = titulo
    st.session_state[k] = r
    return r

GENERO_ES = {
    "fantasy":"Fantasía","thriller":"Thriller","mystery":"Misterio",
    "romance":"Romance","horror":"Terror","science fiction":"Ciencia Ficción",
    "science+fiction":"Ciencia Ficción","fiction":"Ficción",
    "literary fiction":"Ficción Literaria","contemporary":"Contemporáneo",
    "contemporary fiction":"Ficción Contemporánea",
    "historical fiction":"Ficción Histórica","historical+fiction":"Ficción Histórica",
    "adventure":"Aventura","young adult":"Jóvenes Adultos","young+adult":"Jóvenes Adultos",
    "dystopia":"Distopía","graphic novel":"Novela Gráfica","classics":"Clásicos",
    "poetry":"Poesía","short stories":"Cuentos Cortos","history":"Historia",
    "philosophy":"Filosofía","psychology":"Psicología","biography":"Biografía",
    "autobiography":"Autobiografía","business":"Negocios","memoir":"Memorias",
    "self help":"Autoayuda","self-help":"Autoayuda","science":"Ciencia",
    "nonfiction":"No Ficción","non-fiction":"No Ficción",
    "true crime":"Crimen Real","true+crime":"Crimen Real","travel":"Viajes",
    "cooking":"Cocina","art":"Arte","religion":"Religión","humor":"Humor",
    "children":"Infantil","politics":"Política","economics":"Economía",
}

def genero_es(g):
    if not g or pd.isna(g): return "—"
    return GENERO_ES.get(str(g).strip().lower(), str(g).title())

def _mejor_libro_de_genero(genero, pool_df, scores, excluir_autores):
    candidatos = pool_df[
        (pool_df['genero'] == genero) &
        (~pool_df['autor'].isin(excluir_autores))
    ]['book_id'].tolist()
    if not candidatos: return None
    scores_gen = {bid: scores[bid] for bid in candidatos if bid in scores}
    if not scores_gen: return None
    return max(scores_gen, key=scores_gen.get)

def recomendar_hibrido(pref, top_n=3, excluir_ids=None, excluir_autores=None):
    if excluir_ids     is None: excluir_ids     = set()
    if excluir_autores is None: excluir_autores = set()

    df = _libros_reset.copy()
    if pref['generos']: df = df[df['genero'].isin(pref['generos'])]

    if pref['paginas'] == 'Cortos (menos de 300 páginas)':
        df = df[df['paginas'].fillna(9999) < 300]
    elif pref['paginas'] == 'Medianos (300-500 páginas)':
        df = df[df['paginas'].isna() | ((df['paginas'] >= 300) & (df['paginas'] <= 500))]
    elif pref['paginas'] == 'Largos (más de 500 páginas)':
        df = df[df['paginas'].isna() | (df['paginas'] > 500)]

    col_ano = get_col_ano_df(df)
    if col_ano:
        ano_num = pd.to_numeric(df[col_ano], errors='coerce')
        if pref['epoca'] == 'Clásicos (antes del 2000)':
            df = df[ano_num.fillna(9999) < 2000]
        elif pref['epoca'] == 'Contemporáneos (2000-2015)':
            df = df[(ano_num >= 2000) & (ano_num <= 2015)]
        elif pref['epoca'] == 'Recientes (últimos años)':
            df = df[ano_num.fillna(0) > 2015]

    df = df[~df['book_id'].isin(excluir_ids)]
    df = df[~df['autor'].isin(excluir_autores)]
    if len(df) == 0: return pd.DataFrame(), True

    pop = df.merge(popularidad_df, on='book_id', how='left')
    if pref['popularidad'] == 'Bestsellers y libros populares':
        pop = pop.nlargest(200, 'num_ratings')
    elif pref['popularidad'] == 'Joyas escondidas poco conocidas':
        pop = pop.nsmallest(200, 'num_ratings')
    if len(pop) == 0: return pd.DataFrame(), True

    sid = pop.iloc[0]['book_id']
    i0  = bookid_to_row.get(sid)
    scores = {}
    try:
        if i0 is None: raise ValueError()
        sims = similitud_contenido[i0]
        for bid in pop['book_id'].tolist():
            i = bookid_to_row.get(bid)
            if i is not None:
                scores[bid] = float(sims[i]) + random.uniform(-0.05, 0.05)
    except:
        for bid in pop['book_id'].tolist():
            scores[bid] = random.uniform(0.5, 0.9)

    seleccionados = []
    autores_sel   = set()

    if len(pref['generos']) >= 2:
        for genero in pref['generos']:
            if len(seleccionados) >= top_n: break
            bid = _mejor_libro_de_genero(genero, pop, scores, autores_sel)
            if bid:
                autor = pop[pop['book_id'] == bid].iloc[0]['autor']
                seleccionados.append(bid)
                autores_sel.add(autor)
        if len(seleccionados) < top_n:
            ya_sel = set(seleccionados)
            for bid, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                if len(seleccionados) >= top_n: break
                row = pop[pop['book_id'] == bid]
                if row.empty or bid in ya_sel: continue
                autor = row.iloc[0]['autor']
                if autor not in autores_sel:
                    seleccionados.append(bid)
                    autores_sel.add(autor)
    else:
        for bid, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if len(seleccionados) >= top_n: break
            row = pop[pop['book_id'] == bid]
            if row.empty: continue
            autor = row.iloc[0]['autor']
            if autor not in autores_sel:
                seleccionados.append(bid)
                autores_sel.add(autor)

    if not seleccionados: return pd.DataFrame(), True

    res = _libros_reset[_libros_reset['book_id'].isin(seleccionados)].copy()
    res['score'] = res['book_id'].map(scores)
    res = res.sort_values('score', ascending=False).merge(popularidad_df, on='book_id', how='left')
    return res.head(top_n), False

def generar_explicacion(libro, pref):
    genero_libro = genero_es(getattr(libro, 'genero', None))
    if not API_KEY or not client:
        return f"Este libro es ideal para tu interés en {genero_libro}."
    prompt = (
        f'En UNA oración en español de México (máx 18 palabras), explica por qué '
        f'"{libro.titulo}" de {getattr(libro, "autor", "")} encaja con alguien que busca '
        f'libros de {genero_libro}. Solo español, sin inglés.'
    )
    try:
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            max_tokens=60, temperature=0.7)
        return r.choices[0].message.content.strip()
    except:
        return f"Este libro es ideal para tu interés en {genero_libro}."

for k, v in [('pagina','home'),('preferencias',{}),('recomendaciones',None),
             ('libro_seleccionado',None),('carousel_offset',0),
             ('ids_mostrados', set()), ('autores_mostrados', set()),
             ('agotado', False)]:
    if k not in st.session_state: st.session_state[k] = v

LIBROS_POR_PAG = 5

def mostrar_home():
    top_libros = (_libros_reset.copy()
                  .merge(popularidad_df, on='book_id', how='left')
                  .nlargest(10, 'num_ratings').reset_index(drop=True))

    offset = st.session_state.carousel_offset
    total  = len(top_libros)

    bg_style  = (f"background-image:url('data:image/png;base64,{FONDO_B64}');"
                 if FONDO_B64 else "background:linear-gradient(135deg,#1a0808 0%,#0a0a1a 100%);")
    logo_hero = (f'<img src="data:image/png;base64,{LOGO_B64}" height="48">'
                 if LOGO_B64 else '<span style="font-size:1.8rem;font-weight:900;">Lexora</span>')

    st.markdown(f"""
    <div class="hero-outer">
      <div class="hero-bg" style="{bg_style}"></div>
      <div class="hero-overlay"></div>
      <div class="hero-logo">{logo_hero}</div>
      <div class="hero-body">
        <div class="hero-title">Encuentra tu próxima<br>obsesión literaria</div>
        <div class="hero-subtitle">Explora tendencias, descubre el Top 10 de la comunidad
          y recibe recomendaciones personalizadas según tu perfil lector.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero-btn-row">', unsafe_allow_html=True)
    bc1, bc2, bc3 = st.columns([1, 1, 5])
    with bc1:
        if st.button("Personalizar", use_container_width=True):
            st.session_state.pagina = 'preguntas'; st.rerun()
    with bc2:
        if st.button("Catálogo", use_container_width=True):
            st.session_state.pagina = 'catalogo'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">🔥 Las 10 más populares</div>', unsafe_allow_html=True)

    col_prev, c1, c2, c3, c4, c5, col_next = st.columns([0.3,1,1,1,1,1,0.3])
    with col_prev:
        st.markdown('<div class="arrow-btn">', unsafe_allow_html=True)
        if st.button("‹", key="prev", disabled=(offset==0), use_container_width=True):
            st.session_state.carousel_offset = offset - LIBROS_POR_PAG; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    visibles = top_libros.iloc[offset:offset+LIBROS_POR_PAG]
    for col, (_, libro) in zip([c1,c2,c3,c4,c5], visibles.iterrows()):
        rank = offset + list(visibles.index).index(libro.name) + 1
        with col:
            st.markdown(f'<div class="rank-number">{rank}</div>', unsafe_allow_html=True)
            mostrar_portada(libro.get('portada_url'), libro.get('genero'), use_container_width=True)
            t = traducir_titulo(str(libro['titulo']))
            st.markdown(f'<div class="poster-title">{t[:32]}{"…" if len(t)>32 else ""}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="poster-author">{limpiar_texto(str(libro["autor"]))[:26]}</div>', unsafe_allow_html=True)
            if st.button("Ver más", key=f"h_{libro['book_id']}", use_container_width=True):
                st.session_state.libro_seleccionado = libro['book_id']
                st.session_state.pagina = 'detalle'; st.rerun()

    with col_next:
        st.markdown('<div class="arrow-btn">', unsafe_allow_html=True)
        if st.button("›", key="next", disabled=(offset+LIBROS_POR_PAG>=total), use_container_width=True):
            st.session_state.carousel_offset = offset + LIBROS_POR_PAG; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    pa = offset // LIBROS_POR_PAG
    tp = -(-total // LIBROS_POR_PAG)
    dots = "".join(f'<span class="dot{" active" if i==pa else ""}"></span>' for i in range(tp))
    st.markdown(f'<div class="carousel-dots">{dots}</div>', unsafe_allow_html=True)


def mostrar_catalogo():
    logo_pagina()
    st.markdown('<div class="section-title">Catálogo</div>', unsafe_allow_html=True)
    col_b, _ = st.columns([1,6])
    with col_b:
        if st.button("Volver al inicio"): st.session_state.pagina = 'home'; st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1:
        generos_es_lista = sorted(set(genero_es(g) for g in _libros_reset['genero'].dropna().unique()))
        gf = st.selectbox("Género", ["Todos"] + generos_es_lista)
    with c2: ab = st.text_input("Buscar por autor")
    with c3: tb = st.text_input("Buscar por título")

    df = _libros_reset.copy()
    if gf != "Todos":
        gen_inv  = {v: k for k, v in GENERO_ES.items()}
        gen_orig = gen_inv.get(gf, gf)
        df = df[df['genero'] == gen_orig]
    if ab: df = df[df['autor'].str.contains(ab, case=False, na=False)]
    if tb: df = df[df['titulo'].str.contains(tb, case=False, na=False)]
    df = df.head(30)

    if len(df) == 0:
        st.markdown("No se encontraron libros con esos criterios.")
        return

    cols = st.columns(5)
    for idx, libro in enumerate(df.itertuples(index=False), start=1):
        with cols[(idx-1) % 5]:
            mostrar_portada(getattr(libro,'portada_url',None), getattr(libro,'genero',None), use_container_width=True)
            t = traducir_titulo(str(libro.titulo))
            st.markdown(f'<div class="poster-title">{t[:32]}{"…" if len(t)>32 else ""}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="poster-author">{limpiar_texto(libro.autor)}</div>', unsafe_allow_html=True)
            if st.button("Ver detalle", key=f"cat_{libro.book_id}", use_container_width=True):
                st.session_state.libro_seleccionado = libro.book_id
                st.session_state.pagina = 'detalle'; st.rerun()


def mostrar_detalle():
    bid = st.session_state.get('libro_seleccionado')
    if bid is None: st.session_state.pagina = 'home'; st.rerun()

    ldf = _libros_reset[_libros_reset['book_id'] == bid]
    if ldf.empty:
        st.error("No se encontró el libro.")
        if st.button("Volver"): st.session_state.pagina = 'home'; st.rerun()
        return

    libro = ldf.iloc[0]
    logo_pagina()
    cb, _ = st.columns([1,6])
    with cb:
        if st.button("Volver"): st.session_state.pagina = 'home'; st.rerun()

    c1, c2 = st.columns([1,2])
    with c1:
        mostrar_portada(libro.get('portada_url'), libro.get('genero'), width=280)
    with c2:
        st.markdown(f"## {traducir_titulo(limpiar_texto(libro['titulo']))}")
        st.markdown(f"**{limpiar_texto(libro['autor'])}**")
        st.divider()
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Género", genero_es(libro.get('genero','')))
        with m2:
            pags = libro.get('paginas')
            st.metric("Páginas", int(pags) if pd.notna(pags) else "—")
        with m3: st.metric("Año", get_ano(libro))
        st.divider()
        st.markdown("**Descripción**")
        desc = str(libro['descripcion']) if pd.notna(libro.get('descripcion')) else "Sin descripción disponible."
        with st.spinner("Traduciendo..."):
            st.write(traducir_descripcion(desc))
        st.divider()
        ca, cb2 = st.columns(2)
        with ca:
            if st.button("Obtener recomendaciones similares", use_container_width=True):
                st.session_state.pagina = 'preguntas'; st.rerun()
        with cb2:
            if st.button("Seguir explorando el catálogo", use_container_width=True):
                st.session_state.pagina = 'catalogo'; st.rerun()


def mostrar_preguntas():
    logo_pagina()
    st.title("Personaliza tus recomendaciones")
    cb, _ = st.columns([1,6])
    with cb:
        if st.button("Volver al inicio"):
            st.session_state.pagina = 'home'; st.rerun()

    with st.form("form_pref"):
        st.markdown("### ¿Cómo describirías tu hábito de lectura?")
        tl = st.radio("hab", [
            "Soy nuevo en la lectura", "Leo ocasionalmente", "Leo con frecuencia"
        ], label_visibility="collapsed")
        st.markdown("### ¿De qué época prefieres los libros?")
        ep = st.radio("ep", [
            "Clásicos (antes del 2000)", "Contemporáneos (2000-2015)",
            "Recientes (últimos años)", "No tengo preferencia"
        ], label_visibility="collapsed")
        st.markdown("### ¿Qué extensión de libro prefieres?")
        pg = st.radio("pg", [
            "No me importa la extensión", "Cortos (menos de 300 páginas)",
            "Medianos (300-500 páginas)", "Largos (más de 500 páginas)",
        ], label_visibility="collapsed")
        st.markdown("### ¿Qué géneros te interesan? (elige al menos 2)")
        gc1, gc2 = st.columns(2)
        gs = []
        with gc1:
            st.markdown("**Ficción**")
            for g in ['fantasy','thriller','mystery','romance','horror','science+fiction']:
                if st.checkbox(genero_es(g), key=f"g_{g}"): gs.append(g)
        with gc2:
            st.markdown("**No Ficción**")
            for g in ['history','philosophy','psychology','biography','business','memoir']:
                if st.checkbox(genero_es(g), key=f"g_{g}"): gs.append(g)
        st.markdown("### ¿Qué tipo de libros buscas?")
        po = st.radio("po", [
            "Bestsellers y libros populares",
            "Joyas escondidas poco conocidas",
            "Un mix de ambos"
        ], label_visibility="collapsed")

        submitted = st.form_submit_button("Ver mis recomendaciones", use_container_width=True)
        if submitted:
            if len(gs) < 2:
                st.error("Selecciona al menos 2 géneros para continuar.")
            else:
                st.session_state.preferencias      = {
                    'tipo_lector': tl, 'epoca': ep,
                    'paginas': pg, 'generos': gs, 'popularidad': po
                }
                st.session_state.ids_mostrados     = set()
                st.session_state.autores_mostrados = set()
                st.session_state.agotado           = False
                with st.spinner("Generando recomendaciones..."):
                    res, agotado = recomendar_hibrido(st.session_state.preferencias, top_n=3)
                    st.session_state.recomendaciones = res
                    st.session_state.agotado = agotado
                    if not res.empty:
                        st.session_state.ids_mostrados.update(res['book_id'].tolist())
                        st.session_state.autores_mostrados.update(res['autor'].tolist())
                    st.session_state.pagina = 'resultados'; st.rerun()


def mostrar_resultados():
    logo_pagina()
    cb, _ = st.columns([1,6])
    with cb:
        if st.button("Volver al inicio"):
            st.session_state.pagina = 'home'; st.rerun()

    res     = st.session_state.recomendaciones
    agotado = st.session_state.agotado

    if agotado or res is None or (hasattr(res, 'empty') and res.empty):
        st.markdown("""
        <div class="agotado-box">
            <div class="agotado-titulo">Has explorado todo lo disponible con estos filtros</div>
            <div class="agotado-sub">Prueba ajustando la época, extensión o géneros para descubrir más títulos.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ajustar preferencias"):
            st.session_state.pagina = 'preguntas'; st.rerun()
        return

    n = len(res)
    st.markdown('<div class="section-title">Recomendaciones para ti</div>', unsafe_allow_html=True)

    if n < 3:
        st.warning(
            f"Solo encontramos {n} {'libro' if n==1 else 'libros'} que coincide"
            f"{'n' if n>1 else ''} exactamente con tus preferencias. "
            f"Ajusta la época o extensión para ver más opciones.")

    cols = st.columns(3)
    for idx, libro in enumerate(res.itertuples(index=False), start=1):
        with cols[idx-1]:
            mostrar_portada(getattr(libro,'portada_url',None), getattr(libro,'genero',None), use_container_width=True)
            t = traducir_titulo(str(libro.titulo))
            st.markdown(f'<div class="poster-title">{t[:32]}{"…" if len(t)>32 else ""}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="poster-author">{limpiar_texto(libro.autor)}</div>', unsafe_allow_html=True)
            with st.expander("Ver detalle"):
                pags = getattr(libro, 'paginas', None)
                p    = int(pags) if pags is not None and pd.notna(pags) else "—"
                a    = get_ano(libro)
                st.markdown(f"**{genero_es(libro.genero)}** · {p} págs · {a}")
                desc = str(libro.descripcion) if pd.notna(getattr(libro,'descripcion',None)) else "Sin descripción disponible."
                with st.spinner("Traduciendo..."):
                    st.write(traducir_descripcion(desc))
                st.info(generar_explicacion(libro, st.session_state.preferencias))

    st.divider()
    r1, r2, r3 = st.columns(3)
    with r1:
        if st.button("Mostrar otras opciones", use_container_width=True):
            with st.spinner("Buscando..."):
                nuevos, agotado = recomendar_hibrido(
                    st.session_state.preferencias, top_n=3,
                    excluir_ids=st.session_state.ids_mostrados,
                    excluir_autores=st.session_state.autores_mostrados)
                if agotado or nuevos.empty:
                    st.session_state.agotado = True
                    st.session_state.recomendaciones = pd.DataFrame()
                else:
                    st.session_state.ids_mostrados.update(nuevos['book_id'].tolist())
                    st.session_state.autores_mostrados.update(nuevos['autor'].tolist())
                    st.session_state.recomendaciones = nuevos
                st.rerun()
    with r2:
        if st.button("Cambiar preferencias", use_container_width=True):
            st.session_state.pagina = 'preguntas'; st.rerun()
    with r3:
        if st.button("Ir al inicio", use_container_width=True):
            st.session_state.pagina = 'home'; st.rerun()


def main():
    p = st.session_state.pagina
    if   p == 'home':       mostrar_home()
    elif p == 'catalogo':   mostrar_catalogo()
    elif p == 'detalle':    mostrar_detalle()
    elif p == 'preguntas':  mostrar_preguntas()
    elif p == 'resultados': mostrar_resultados()

if __name__ == "__main__":
    main()
