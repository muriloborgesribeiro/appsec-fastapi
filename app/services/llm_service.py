from openai import OpenAI

from app.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL, RAG_TEMPERATURE

_SYSTEM_PROMPT = (
    "Voce e um assistente de IA especializado em responder duvidas "
    "sobre o projeto APPSPEC.\n\n"
    "Regras:\n"
    "1. Responda APENAS com base nos trechos da documentacao "
    "fornecidos abaixo no CONTEXTO.\n"
    "2. NAO invente informacoes, referencias, numeros ou citacoes "
    "que nao estejam presentes no contexto.\n"
    "3. Se a informacao nao estiver disponivel no contexto, diga: "
    '"Nao encontrei essa informacao na documentacao do projeto."\n'
    "4. Cite a fonte (arquivo) de onde a informacao foi extraida.\n"
    "5. Responda em portugues brasileiro de forma clara e objetiva.\n\n"
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
