# Datapolis Copilot Instructions

## Stack
Django monolítico modular, templates server-rendered (sin React/Vue/Angular), Plotly.js solo en render público.

## Estado actual
Fase activa: [actualizar aquí cada fase, ej. "Fase 15 - dashboard interno lectura"].
Apps existentes: [listar según crezca el proyecto].
Modelos core: PortfolioProject, ProjectCategory, ProjectType, DataSource, ProjectVisualization.

## Reglas de economía (aplican siempre)
- No expliques el código generado a menos que se pida explícitamente.
- No agregues comentarios salvo que la lógica sea no obvia.
- No repitas el contexto del prompt en tu respuesta; ve directo al código.
- No propongas alternativas o mejoras no solicitadas; si ves un problema real, una línea al final basta.
- Genera solo los archivos/bloques pedidos, no el proyecto completo.

## Reglas de alcance
- No crear apps nuevas sin pedirlo explícitamente.
- No crear migraciones ni tocar modelos salvo estrictamente necesario — si es necesario, decirlo antes de generar el código.
- No introducir auth, formularios, upload de archivos o edición salvo que la fase lo pida.
- No tocar Docker/infra salvo que se pida.
- Mantener todo en español (UI, strings, nombres de template) salvo nombres de código Python/Django (variables, funciones, clases en inglés como es convención).
- Views preparan los datos; templates sin lógica compleja (evitar filtros/tags custom salvo necesidad clara).

## Convenciones
- Estados de proyecto se mapean en la view (draft/published/archived → Borrador/Publicado/Archivado), nunca hardcodeados en template.
- Cards en vez de tablas para listados.
- Reusar datos de modelos existentes antes de proponer campos nuevos.
