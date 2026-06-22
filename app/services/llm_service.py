from openai import OpenAI

from app.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL, RAG_TEMPERATURE

_SYSTEM_PROMPT = (
    "Voce e um assistente de IA especializado em responder duvidas "
    "sobre o projeto APPSPEC.\n\n"
    "Diretrizes:\n"
    "1. Use os trechos da documentacao fornecidos no CONTEXTO como "
    "sua fonte principal de informacao.\n"
    "2. Se a pergunta nao for especifica do projeto ou se o contexto "
    "nao tiver informacao suficiente, voce pode complementar com seu "
    "conhecimento geral, desde que deixe claro o que veio do projeto "
    "e o que e conhecimento geral.\n"
    "3. NAO invente numeros, metricas ou citacoes especificas que "
    "nao estejam no contexto ou no seu conhecimento estabelecido.\n"
    "4. Cite a fonte (arquivo) quando a informacao vier do contexto.\n"
    "5. Responda em portugues brasileiro de forma clara e objetiva.\n"
    "6. Formate a resposta usando Markdown: use **negrito** para conceitos importantes, "
    "topicos com - para listas, e ``` para codigo ou exemplos numericos.\n"
    "7. Se a pergunta pedir comparacao entre modelos (ex: KNN vs SVM), "
    "apresente em topicos lado a lado.\n\n"
    "CONTEXTO:\n{contexto}"
)


def _montar_prompt(pergunta: str, chunks: list[dict]) -> str:
    if not chunks:
        contexto = "Nenhum trecho relevante encontrado na documentacao."
    else:
        linhas = []
        for _, c in enumerate(chunks, 1):
            linhas.append(f"[Fonte: {c['fonte']}]\n{c['texto']}\n")
        contexto = "\n---\n".join(linhas)
    return _SYSTEM_PROMPT.format(contexto=contexto)


def gerar_resposta(pergunta: str, chunks: list[dict]) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY nao configurada")

    client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
    prompt = _montar_prompt(pergunta, chunks)

    resposta = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": pergunta},
        ],
        temperature=RAG_TEMPERATURE,
        max_tokens=2048,
    )

    return resposta.choices[0].message.content or ""
