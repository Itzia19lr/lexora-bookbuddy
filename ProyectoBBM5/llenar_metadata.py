# llenar_metadata.py
import pandas as pd
import requests
import time
import re

RUTA_CSV     = "data/libros.csv"
GUARDAR_CADA = 50

libros = pd.read_csv(RUTA_CSV, encoding='latin-1')

# Asegurar que las columnas existen
for col in ['portada_url', 'paginas', 'año']:
    if col not in libros.columns:
        libros[col] = None

libros['portada_url'] = libros['portada_url'].fillna("").astype(str)

def limpiar_titulo(titulo):
    if pd.isna(titulo): return ""
    titulo = str(titulo)
    titulo = re.sub(r"\(.*?\)", "", titulo)
    for sep in [":", "-", ","]:
        if sep in titulo:
            titulo = titulo.split(sep)[0]
    return titulo.strip()

def buscar_open_library(titulo, autor=None):
    try:
        params = {"title": titulo, "limit": 3}
        if autor:
            params["author"] = str(autor)[:50]
        r = requests.get("https://openlibrary.org/search.json",
                         params=params, timeout=10)
        r.raise_for_status()
        docs = r.json().get("docs", [])
        for doc in docs:
            cover_id = doc.get("cover_i")
            paginas  = doc.get("number_of_pages_median")
            año      = doc.get("first_publish_year")
            portada  = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
            if portada or paginas or año:
                return portada, paginas, año
        return None, None, None
    except Exception:
        return None, None, None

# Solo procesar libros que les falta ALGO
def necesita_update(row):
    sin_portada = str(row.get('portada_url', '')).strip() == ''
    sin_paginas = pd.isna(row.get('paginas')) or row.get('paginas') == 0
    sin_año     = pd.isna(row.get('año'))
    return sin_portada or sin_paginas or sin_año

pendientes = libros[libros.apply(necesita_update, axis=1)]
print(f"Libros que necesitan actualización: {len(pendientes)} / {len(libros)}")

actualizadas = 0

for count, (i, row) in enumerate(pendientes.iterrows(), start=1):
    titulo = limpiar_titulo(row.get('titulo', ''))
    autor  = row.get('autor', None)

    portada, paginas, año = buscar_open_library(titulo, autor)

    cambios = []

    if portada and str(row.get('portada_url', '')).strip() == '':
        libros.at[i, 'portada_url'] = portada
        cambios.append('portada')

    if paginas and (pd.isna(row.get('paginas')) or row.get('paginas') == 0):
        libros.at[i, 'paginas'] = int(paginas)
        cambios.append(f'páginas={paginas}')

    if año and pd.isna(row.get('año')):
        libros.at[i, 'año'] = int(año)
        cambios.append(f'año={año}')

    if cambios:
        actualizadas += 1
        print(f"  OK  [{count}/{len(pendientes)}] {titulo[:40]} → {', '.join(cambios)}")
    else:
        print(f"  --  [{count}/{len(pendientes)}] {titulo[:40]}")

    if count % GUARDAR_CADA == 0:
        libros.to_csv(RUTA_CSV, index=False)
        print(f"  >>> Checkpoint guardado ({count} procesados)")

    time.sleep(0.3)

libros.to_csv(RUTA_CSV, index=False)

# Reporte final
sin_portada = (libros['portada_url'].str.strip() == '').sum()
sin_paginas = libros['paginas'].isna().sum()
sin_año     = libros['año'].isna().sum()

print(f"\nTerminado. {actualizadas} libros actualizados.")
print(f"Pendientes después del script:")
print(f"  Sin portada: {sin_portada}")
print(f"  Sin páginas: {sin_paginas}")
print(f"  Sin año:     {sin_año}")