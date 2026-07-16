# Datapolis Copilot Instructions

## Stack
Django monolítico modular, templates server-rendered (sin React/Vue/Angular), Plotly.js solo en render público y en preview del dashboard.

## Apps y arquitectura
Apps existentes: `platform`, `portfolio_projects`, `data_sources`, `data_visualizations`, `dashboard`.
Arquitectura general: Django monolítico modular, templates server-rendered, sin React/Vue/Angular, sin SPA.
Modelos core: PortfolioProject, ProjectCategory, ProjectType, DataSource, ProjectVisualization.

## Dashboard interno
Layout: sidebar global + perfil analítico reutilizable a la izquierda + contenido específico a la derecha.
Secciones: `Mi portafolio` = overview, `Proyectos` = listado, `Detalle` = vista de proyecto.
Partials compartidos: `apps/dashboard/templates/dashboard/partials/analyst_profile_card.html`, `apps/dashboard/templates/dashboard/partials/visualization_card.html`.
CSS compartido: `static/dashboard/css/dashboard.css` — reutilizar clases existentes (`dashboard-card`, `dashboard-badge`, `dashboard-grid`, `dashboard-button-primary/secondary`, `dashboard-empty-state`), evitar estilos inline o duplicados.
Patrón visual: cards blancas, bordes dashed suaves, badges arriba a la derecha, botones limpios. Paleta: `#3E7C7B`, `#7FB7BE`, `#B7C4C7`, `#E6E8E6`, `#D8A7B1`, `#FFFFFF`.

## Infraestructura
Deploy: Railway, vía Dockerfile con entrypoint.sh (migrate + collectstatic + gunicorn). No tocar Docker/infra salvo que se pida explícitamente.

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
