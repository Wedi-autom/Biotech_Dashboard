"""Cerveau IA (OpenAI ou compatible) + recherche web DuckDuckGo."""
import os, streamlit as st
from openai import OpenAI

SYSTEM = ("Tu es un analyste buy-side senior spécialisé biotech/pharma et actions. Réponds TOUJOURS en français, "
          "de façon concise, factuelle et orientée gestion du risque (taille de position, scénarios, invalidation). "
          "Distingue faits et hypothèses, n'invente aucun chiffre absent des données fournies, signale les incertitudes. "
          "Ceci n'est pas un conseil en investissement personnalisé.")

def _secret(k, default=None):
    try:
        return st.secrets.get(k, os.getenv(k, default))
    except Exception:
        return os.getenv(k, default)

def ask(prompt: str, context: str = "") -> str:
    key = _secret("OPENAI_API_KEY")
    if not key:
        return "⚠️ Clé `OPENAI_API_KEY` absente (voir README)."
    client = OpenAI(api_key=key, base_url=_secret("OPENAI_BASE_URL"))
    try:
        r = client.chat.completions.create(
            model=_secret("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.3,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": f"{prompt}\n\n--- DONNÉES ---\n{context}"[:14000]}])
        return r.choices[0].message.content
    except Exception as e:
        return f"⚠️ Erreur IA : {e}"

@st.cache_data(ttl=1800)
def web_search(query: str, n: int = 15, news: bool = False) -> list[dict]:
    from ddgs import DDGS
    try:
        d = DDGS()
        return list(d.news(query, max_results=n) if news else d.text(query, max_results=n))
    except Exception:
        return []

def fmt(results: list[dict]) -> str:
    return "\n".join(f"- {r.get('title','')} | {r.get('body','')[:250]} | {r.get('url') or r.get('href','')}"
                     for r in results)
