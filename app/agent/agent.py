"""
Parte 3: Agente que usa los tools.

Flujo: mensaje usuario → LLM (con tools) → si pide llamar tools, los ejecutamos
       y pasamos el resultado al LLM → repetir hasta que el LLM responda solo texto.
"""
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger("agent")


TITLE_PROMPT = """Genera un título corto (3-5 palabras) para esta conversación financiera.
Solo responde el título, sin comillas ni explicaciones.
Mensaje del usuario: {message}"""


async def generate_chat_title(first_user_message: str) -> str:
    """
    Usa el LLM para generar un título breve a partir del primer mensaje.
    Devuelve el título truncado a 200 caracteres.
    """
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
    )
    prompt = TITLE_PROMPT.format(message=first_user_message[:500])
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    title = (response.content or "Nueva conversación").strip()[:200]
    return title or "Nueva conversación"


SYSTEM_PROMPT = """Eres un asistente financiero. Respondes preguntas sobre cuentas, transacciones y gastos.
Cuando necesites datos (cuentas, transacciones, gastos por categoría), usa las herramientas disponibles.
Responde siempre en español, de forma clara y breve. Si te dan datos en JSON, resúmelos en texto.

GRÁFICOS: Cuando el usuario pida explícitamente un gráfico, una visualización o un chart (ej: "muéstrame un gráfico de gastos", "quiero ver un chart de..."), DEBES incluir al final de tu respuesta un bloque con este formato exacto:

[CHART]
{"type":"chart","chartType":"TIPO","data":{"labels":["A","B","C"],"values":[10,20,30]}}

Donde TIPO es uno de: "pie" (para proporciones), "bar" (para comparar categorías), "line" (para evolución temporal).
- labels: nombres de las categorías o etiquetas
- values: números correspondientes (totales, cantidades)

Incluye primero tu análisis en texto y luego el bloque [CHART] solo si el usuario pidió un gráfico."""


def _extract_usage(response) -> dict:
    """Extrae usage de tokens de la respuesta del LLM."""
    meta = getattr(response, "response_metadata", {}) or {}
    usage = meta.get("usage_metadata") or meta.get("usage") or {}
    return {
        "prompt_tokens": usage.get("input_tokens") or usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("output_tokens") or usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }


async def get_response_with_tools(
    message: str,
    tools: list,
    history: list[tuple[str, str]] | None = None,
) -> tuple[str, int]:
    """
    Ejecuta el agente. Devuelve (contenido_texto, total_tokens).
    """
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
    ).bind_tools(tools)

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if history:
        for role, content in history:
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=message))
    total_tokens = 0

    while True:
        response = await llm.ainvoke(messages)
        usage = _extract_usage(response)
        pt, ct, tt = usage["prompt_tokens"], usage["completion_tokens"], usage["total_tokens"]
        total_tokens += tt
        if pt or ct or tt:
            logger.info(
                "LLM call prompt_tokens=%s completion_tokens=%s total_tokens=%s",
                pt, ct, tt,
            )

        if not response.tool_calls:
            return response.content, total_tokens

        messages.append(response)

        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc.get("args", {})
            tool_id = tc["id"]
            logger.debug("tool %s invoked args=%s", tool_name, tool_args)
            tool = next((t for t in tools if t.name == tool_name), None)
            if not tool:
                content = f"Tool {tool_name} no encontrado."
            else:
                content = await tool.ainvoke(tool_args)
            messages.append(
                ToolMessage(content=str(content), tool_call_id=tool_id)
            )


def parse_chat_response(text: str) -> tuple[str, list[dict]]:
    """
    Extrae bloques [CHART] del texto. Busca [CHART] seguido de JSON
    y lo parsea (manejando objetos anidados).
    Devuelve (texto_sin_chart, lista_de_bloques_chart).
    """
    blocks = []
    i = 0
    positions_to_remove = []  # (start, end) de cada bloque [CHART]...{...}

    while True:
        idx = text.find("[CHART]", i)
        if idx == -1:
            break
        start_brace = text.find("{", idx)
        if start_brace == -1:
            i = idx + 1
            continue
        depth = 0
        end_brace = start_brace
        for j, c in enumerate(text[start_brace:], start_brace):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end_brace = j
                    break
        try:
            chart_data = json.loads(text[start_brace : end_brace + 1])
            if (
                chart_data.get("type") == "chart"
                and "chartType" in chart_data
                and "data" in chart_data
            ):
                blocks.append(chart_data)
            positions_to_remove.append((idx, end_brace + 1))
        except json.JSONDecodeError:
            positions_to_remove.append((idx, end_brace + 1))
        i = end_brace + 1

    # Quitar bloques del texto
    result = text
    for start, end in reversed(positions_to_remove):
        result = result[:start] + result[end:]
    return result.strip(), blocks
