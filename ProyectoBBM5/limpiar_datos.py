import pandas as pd
import unicodedata

df = pd.read_csv('data/libros.csv', encoding='utf-8')
df.to_csv('data/libros_backup.csv', index=False, encoding='utf-8')

def corregir_encoding(texto):
    if not texto or pd.isna(texto):
        return texto
    texto = str(texto)
    try:
        corregido = texto.encode('latin-1').decode('utf-8')
        if corregido.isprintable():
            return unicodedata.normalize('NFC', corregido)
    except:
        pass
    try:
        return unicodedata.normalize('NFC', texto)
    except:
        return texto

df['autor']  = df['autor'].apply(corregir_encoding)
df['titulo'] = df['titulo'].apply(corregir_encoding)

col_ano = next((c for c in df.columns
                if c.strip().lower() in ('ano', 'año', 'ano_publicacion', 'año_publicacion')), None)

if col_ano:
    df[col_ano] = pd.to_numeric(df[col_ano], errors='coerce')
    df.loc[df[col_ano] > 2025, col_ano] = pd.NA

for col in ['titulo', 'autor', 'genero']:
    if col in df.columns:
        df[col] = df[col].str.strip()

df.to_csv('data/libros.csv', index=False, encoding='utf-8')
print(f"Libros procesados: {len(df)}")
print(f"Autores únicos: {df['autor'].nunique()}")
