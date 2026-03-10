# finance-api

API REST con asistente financiero impulsado por IA. Permite consultar cuentas, transacciones y gastos mediante chat natural, con soporte para visualizaciones en gráficos.

## Características

- **Chat con agente IA**: Preguntas en lenguaje natural sobre finanzas (cuentas, transacciones, gastos por categoría)
- **Multi-conversación**: Múltiples chats con títulos generados por IA, historial persistente
- **Tools automáticos**: El LLM decide cuándo consultar la base de datos usando herramientas (tools)
- **Gráficos**: Respuestas con bloques de chart (pie, bar, line) cuando el usuario los solicita
- **API REST**: Endpoints estándar con FastAPI, CORS configurable
- **Bases de datos**: PostgreSQL para finanzas (existente) y para chat (Docker)

## Tecnologías

- **FastAPI** – Framework web asíncrono
- **LangChain + LangChain-OpenAI** – Agente con tools y modelo GPT
- **SQLAlchemy + asyncpg** – ORM asíncrono para PostgreSQL
- **Pydantic Settings** – Configuración vía variables de entorno
- **Uvicorn** – Servidor ASGI

## Requisitos

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes)
- PostgreSQL con las tablas `accounts` y `transactions` (BD finanzas)
- PostgreSQL para chat (incluido en Docker con `docker compose`)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/CRPA22/finance-api
cd finance-api

# Instalar dependencias con uv
uv sync
```

## Configuración

1. Copia el archivo de ejemplo y completa las variables:

```bash
cp .env.example .env
```

2. Edita `.env` con tus valores:

| Variable           | Descripción                                      | Ejemplo                                                       |
|--------------------|--------------------------------------------------|---------------------------------------------------------------|
| `OPENAI_API_KEY`   | API key de OpenAI                                | `sk-...`                                                      |
| `OPENAI_MODEL`     | Modelo de OpenAI a usar                          | `gpt-4o-mini`                                                 |
| `DATABASE_URL`     | URL de conexión PostgreSQL (BD finanzas)         | `postgresql+asyncpg://user:pass@localhost:5432/mi_bd`         |
| `CHAT_DATABASE_URL`| URL de la BD de chat                             | `postgresql+asyncpg://chatdb:pass@chat-db:5432/chat_db`       |
| `CORS_ORIGINS`     | Orígenes permitidos para CORS (separados por coma)| `http://localhost:5173,http://localhost:3000`                 |

## Ejecución

### Local

```bash
uv run python main.py
```

O con uvicorn:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker compose up --build
```

Crear tablas de chat (tras levantar el servicio `chat-db`):

```bash
docker compose --env-file .env run --rm api uv run python scripts/create_chat_table.py
```

La API estará disponible en `http://localhost:8000`.

## API Endpoints

Base path: `/api/v1`

### Health check

```
GET /api/v1/health
```

Respuesta: `{"status": "ok", "message": "API is running"}`

### Chat

```
POST /api/v1/chat
Content-Type: application/json
```

**Request:**

```json
{
  "message": "¿Cuánto gasté en alimentación el mes pasado?",
  "session_id": "uuid-opcional"
}
```

- `message`: Obligatorio, entre 1 y 10.000 caracteres
- `session_id`: Opcional. Si no se envía, se crea una conversación nueva

**Response:**

```json
{
  "response": "En el mes pasado gastaste un total de $1.250...",
  "blocks": [{"type": "chart", "chartType": "pie", "data": {...}}],
  "session_id": "uuid",
  "title": "Gastos alimentación marzo"
}
```

- `title`: Solo presente en el primer mensaje de una conversación; en el resto viene como `null`

### Listar conversaciones

```
GET /api/v1/chats
```

Respuesta:

```json
[
  {"session_id": "uuid", "title": "Gastos alimentación marzo", "updated_at": "2026-03-09T19:00:00Z"}
]
```

### Historial de una conversación

```
GET /api/v1/chat/history?session_id=uuid
```

Respuesta:

```json
[
  {"role": "user", "content": "¿Cuánto gasté?"},
  {"role": "assistant", "content": "En total gastaste $1.250..."}
]
```

### Eliminar conversación

```
DELETE /api/v1/chat/{session_id}
```

Respuesta: `204 No Content`

### Listar cuentas

```
GET /api/v1/accounts
```

Respuesta: lista de cuentas con `id`, `name`, `type`, `currency`, `balance`

## Documentación interactiva

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Estructura del proyecto

```
finance-api/
├── app/
│   ├── api/routes.py       # Endpoints
│   ├── agent/
│   │   ├── agent.py        # Agente LangChain + generate_chat_title
│   │   └── tools/finance.py
│   ├── core/logging_config.py
│   ├── db/
│   │   ├── database.py     # Conexión a BD finanzas y chat
│   │   ├── models.py       # Account, Transaction
│   │   ├── chat_models.py  # ChatSession, ChatMessage
│   │   └── chat_history.py # get_chat_history, list_chats, save_message, etc.
│   ├── schemas/chat.py     # ChatRequest, ChatResponse, ChatSummary
│   ├── config.py
│   └── main.py
├── scripts/
│   ├── create_chat_table.py  # Crear chat_messages y chat_sessions
│   └── inspect_db.py
├── main.py
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## Base de datos

- **BD finanzas**: PostgreSQL existente con `accounts` y `transactions`
- **BD chat**: PostgreSQL en Docker (`chat-db`) con `chat_messages` y `chat_sessions`

Las tablas de chat se crean con:

```bash
docker compose --env-file .env run --rm api uv run python scripts/create_chat_table.py
```

Para inspeccionar la BD de finanzas:

```bash
uv run python scripts/inspect_db.py
```

## Logs

Los logs se escriben a stdout y al archivo `/app/logs/app.log` (dentro del contenedor).

- **Tiempo real:** `docker compose logs -f api`
- **Archivo persistente:** `docker compose exec api tail -f /app/logs/app.log`
- **Ver últimos logs:** `docker compose exec api cat /app/logs/app.log`

El archivo se guarda en el volumen `logs_data` y persiste al reiniciar contenedores.

## Licencia

MIT
