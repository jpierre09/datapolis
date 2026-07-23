# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos

Desarrollo vía Docker Compose (ver `Makefile`):
```
make up               # docker compose up --build
make down
make migrate          # migrate dentro del contenedor web
make createsuperuser
make shell            # shell dentro del contenedor web
make check            # python manage.py check
```

Sin Docker (venv en `.venv`, Python 3.12):
```
python manage.py runserver
python manage.py migrate
python manage.py makemigrations <app>
python manage.py test apps.data_visualizations   # tests por app
python manage.py test apps.data_visualizations.tests.SomeTestCase.test_algo  # test individual
python manage.py collectstatic
```
Tests existentes: `apps/data_sources/tests.py`, `apps/data_visualizations/tests.py`, `apps/external_dashboards/tests.py`, `apps/platform/tests.py`, `apps/portfolio_projects/tests.py`. No hay linter/formatter configurado en el repo.

## Stack

Django 6.0 monolítico modular, templates server-rendered (sin React/Vue/Angular, sin SPA). Plotly.js solo en render público y en preview del dashboard. Auth vía `django-allauth` (login clásico + Google OAuth). Postgres en producción/Docker (`DATABASE_URL`), SQLite como fallback local. Estáticos servidos con Whitenoise (`CompressedManifestStaticFilesStorage`).

## Apps y arquitectura

- `apps/platform` — landing pública, páginas institucionales. `urls.py` montado en `/`.
- `apps/portfolio_projects` — modelos core del portafolio público (`PortfolioProject`, `ProjectCategory`, `ProjectType`) y sus vistas públicas (`/projects/`, `/u/<slug>/`, `/u/<slug>/projects/<slug>/`).
- `apps/data_sources` — modelo `DataSource` y su procesamiento (`services.py`); un dataset tiene `processing_status` (debe ser `"processed"` antes de poder graficarse).
- `apps/data_visualizations` — modelo `ProjectVisualization` + `engine/` (motor de construcción de payloads de gráficas, independiente de views/templates):
  - `engine/readers.py` — lee el `DataSource` a un DataFrame de pandas.
  - `engine/aggregators.py` — aplica agregaciones (`sum`, `average`, `count`, `minimum`, `maximum`).
  - `engine/builder.py` — orquesta: valida `visualization_type` contra `SUPPORTED_VISUALIZATION_TYPES` (`bar_chart`, `line_chart`, `scatter_plot`, `pie_chart`, `data_table`, `kpi_card`) y que el dataset esté `processed`, arma el payload.
  - `engine/serializers.py` — payload final consumido por Plotly.js.
  - `engine/exceptions.py` — `VisualizationEngineError`, usada para no romper la vista si falla el build (ver regla de payloads abajo).
- `apps/dashboard` — área autenticada (`/dashboard/`), namespace de URLs `dashboard`. Contiene `PublicProfile`, `dataset_columns.py` (introspección de columnas de un dataset), y las vistas CRUD de proyectos/datasets/visualizaciones del usuario logueado.
- `apps/external_dashboards` — app scaffoldeada (modelos aún vacíos, sin URLs montadas en `datapolis_project/urls.py`); confirmar alcance antes de asumir que algo ahí ya existe o está en uso.

Login: `LOGIN_URL = "login"`, redirige a `dashboard:overview`. Rutas de auth: `/login/`, `/logout/`, `/accounts/` (allauth, incluye Google OAuth).

## Dashboard interno

Layout: sidebar global + perfil analítico reutilizable a la izquierda + contenido específico a la derecha.
Secciones: `Mi portafolio` = overview, `Proyectos` = listado, `Detalle` = vista de proyecto.
Partials compartidos: `apps/dashboard/templates/dashboard/partials/analyst_profile_card.html`, `apps/dashboard/templates/dashboard/partials/visualization_card.html`.
CSS compartido: `static/dashboard/css/dashboard.css` — reutilizar clases existentes (`dashboard-card`, `dashboard-badge`, `dashboard-grid`, `dashboard-button-primary/secondary`, `dashboard-empty-state`), evitar estilos inline o duplicados.
Patrón visual: cards blancas, bordes dashed suaves, badges arriba a la derecha, botones limpios. Paleta: `#3E7C7B`, `#7FB7BE`, `#B7C4C7`, `#E6E8E6`, `#D8A7B1`, `#FFFFFF`.

## Infraestructura

Deploy: Railway, vía `Dockerfile` con `entrypoint.sh` (migrate + collectstatic + gunicorn). No tocar Docker/infra salvo que se pida explícitamente.

## Reglas de economía (aplican siempre)
- No expliques el código generado a menos que se pida explícitamente.
- No agregues comentarios salvo que la lógica sea no obvia.
- No repitas el contexto del prompt en tu respuesta; ve directo al código.
- No propongas alternativas o mejoras no solicitadas; si ves un problema real, una línea al final basta.
- Genera solo los archivos/bloques pedidos, no el proyecto completo.
- NUNCA reescribas un archivo completo si solo cambia una sección. Usa bloques de cambios ("diffs") o muestra solo la función/clase modificada.

## Reglas de alcance
- No crear apps nuevas sin pedirlo explícitamente.
- No crear migraciones ni tocar modelos salvo estrictamente necesario — si es necesario, decirlo antes de generar el código.
- No introducir auth, formularios, upload de archivos o edición salvo que la tarea puntual lo pida.
- Mantener todo en español (UI, strings, nombres de template) salvo nombres de código Python/Django (variables, funciones, clases en inglés como es convención).
- Views preparan los datos; templates sin lógica compleja (evitar filtros/tags custom salvo necesidad clara).

## Convenciones
- Estados de proyecto se mapean en la view (draft/published/archived → Borrador/Publicado/Archivado), nunca hardcodeados en template.
- Cards en vez de tablas para listados.
- Reusar datos de modelos existentes antes de proponer campos nuevos.
- Diccionarios de traducción (tipo de gráfica, agregación) viven en un único lugar dentro de `apps/data_visualizations`, nunca repetidos/hardcodeados en templates.
- Al generar payloads para preview/mini-preview, envolver en try/except y exponer un flag de error legible a la card, nunca romper la vista completa.
