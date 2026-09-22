# BIODATAPHARMA

Proyecto final de la asignatura Tecnología de Procesamiento de Big Data — Máster Universitario en Inteligencia Artificial Aplicada (MUIAAp), ICAI, Universidad Pontificia Comillas.

## Descripción

Sistema que automatiza la recolección, ordenación y análisis de datos de medicamentos en base a enfermedades, utilizando como fuentes la API REST de CIMA, web scraping de fichas técnicas de CIMA y datos del Ministerio de Sanidad.

**Enfermedad asignada al equipo:** Diabetes

## Equipo

- Alberto Rey
- Adrián Calderón
- Jorge Montoyo

## Estructura del repositorio

    proyecto_1_ingenieria_dato/
    ├── data/     # ficheros .xlsx generados por cada historia de usuario
    ├── src/      # scripts de Python de cada historia de usuario
    ├── requirements.txt
    └── README.md

## Historias de usuario

- **HU-1:** Extracción de medicamentos de diabetes desde la API REST de CIMA.
- **HU-2:** Web scraping de las fichas técnicas para calcular métricas de seguridad.
- **HU-3:** Enriquecimiento con datos económicos del Ministerio de Sanidad.

## Entorno de desarrollo

Entorno virtual con uv (Python 3.10):

    uv venv --python 3.10
    source .venv/bin/activate
    uv pip install -r requirements.txt
