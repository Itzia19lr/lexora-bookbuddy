# BookBuddy — Sistema de Recomendación de Libros

Sistema de recomendación personalizada de libros diseñado para operar en escenarios de **datos escasos** (densidad matricial 1.66 %) y resolver el problema de **cold start** sin requerir historial previo del usuario.

En lugar de depender de interacciones acumuladas, captura preferencias explícitas mediante cinco preguntas y genera recomendaciones desde la primera interacción, con justificación en lenguaje natural para cada sugerencia.

**Demo en vivo:** https://lexora-bookbuddy.streamlit.app

---

## Problema

Las plataformas existentes (Goodreads, Amazon) asumen que el usuario ya conoce títulos y autores. En México el promedio de lectura es de 3.9 libros/año (INEGI MOLEC, 2025) — la mayoría de los lectores potenciales queda fuera de estos sistemas desde el primer uso.

**Pregunta de investigación:** ¿Es posible generar recomendaciones personalizadas en escenarios de datos escasos, atendiendo tanto a usuarios con historial como a usuarios nuevos, mediante una interfaz accesible?

---

## Dataset

| | |
|---|---|
| Libros | 808 títulos en 21 géneros — Google Books API + Open Library |
| Usuarios | 500 perfiles sintéticos calibrados con Pew Research (2012), validados con χ² (p = 0.91) |
| Calificaciones | 6,717 sintéticas — densidad matricial 1.66 % (6,717 de 404,000 posibles) |
| División | 80/20 train-test, semilla fija = 42 |

Las calificaciones se generaron con el modelo: `r(u,i) = clip(3.0 + 2.0 · afinidad(u,i) + εᵤ + εᵢ, 1, 5)` con εᵤ ~ N(0, 0.16) y εᵢ ~ N(0, 0.09).

---

## Modelos evaluados

| Modelo | MAE | RMSE | Nota |
|---|---|---|---|
| Vector Space + TF-IDF | 0.27 | 0.34 | ⚠ Ventaja artificial — features correlacionadas con el proceso generativo de ratings |
| Híbrido (pesos optimizados) | 0.33 | 0.44 | Converge a [VS=0.04, k-NN=0.96, SVD=0.00] — equivale a k-NN puro |
| **Item-Based k-NN** | **0.34** | **0.45** | ✦ Seleccionado e implementado |
| SVD (50 factores) | 2.17 | 2.23 | ✗ Colapsa con densidad < 2 % |

**¿Por qué k-NN?** SVD necesita suficientes calificaciones para aprender representaciones latentes. Con 1.66 % de densidad el modelo no detecta patrones útiles. k-NN opera con similitud directa entre ítems y es robusto ante baja densidad. El modelo híbrido lo confirma empíricamente al asignar peso 0 a SVD.

**Generalización del modelo seleccionado:**
- 77.6 % de predicciones con error ≤ 0.5 puntos
- 97.3 % de predicciones con error ≤ 1.0 punto (escala 1–5)

---

## Estructura del repositorio

```
ProyectoBBM5/
├── data/
│   ├── libros.csv               # Metadatos de los 808 libros
│   ├── usuarios.csv             # Perfiles sintéticos de usuario
│   ├── ratings.csv              # Calificaciones sintéticas
│   ├── popularidad_libros.csv   # Scores de popularidad por libro
│   ├── generos.json             # Catálogo de géneros
│   ├── stats_anos.json          # Distribución temporal del catálogo
│   └── stats_paginas.json       # Estadísticas de extensión
├── models/                      # Modelos entrenados serializados
├── app.py                       # Aplicación principal Streamlit
├── llenar_metadata.py           # Ingesta de metadatos via Google Books API
├── llenar_portadas.py           # Obtención de portadas via Open Library
└── requirements.txt
```

---

## Instalación

```bash
git clone https://github.com/Itzia19lr/lexora-bookbuddy.git
cd lexora-bookbuddy/ProyectoBBM5
pip install -r requirements.txt
streamlit run app.py
```

El dataset ya está incluido en `data/`. Los scripts de ingesta (`llenar_metadata.py`, `llenar_portadas.py`) son opcionales y requieren una API key de Google Books como variable de entorno: `GOOGLE_BOOKS_API_KEY`.

---

## Limitaciones

- Los ratings sintéticos se generaron en función de afinidad por género — la misma variable que usa el modelo de contenido. Esto infla artificialmente las métricas de TF-IDF.
- Métricas de ranking (NDCG@k, Precision@k) son estructuralmente inapropiadas para esta densidad. Con promedio de 12.4 calificaciones por usuario, la probabilidad de que un libro recomendado aparezca en el test set es mínima aunque la recomendación sea correcta. MAE y RMSE son las métricas adecuadas para este escenario.
- No se realizaron pruebas con usuarios reales.

---

*Proyecto Final — Diplomado en Ciencia de Datos · Abril 2026*  
*Itzia Yamilé Livera Ramírez*
