import json
import re
import traceback
from functools import lru_cache
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import get_settings
from app.agent.state import AgentState
from app.agent.tools import search_web, scrape_url, generate_search_queries


@lru_cache()
def get_llm():
    settings = get_settings()
    if not settings.groq_api_key:
        return None
    return ChatGroq(
        model=settings.agent_model,
        api_key=settings.groq_api_key,
        temperature=0.3,
    )


def llm_invoke_safe(system: str, human: str, lang: str) -> str | None:
    llm = get_llm()
    if not llm:
        return None
    try:
        response = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=human),
        ])
        return response.content
    except Exception as e:
        err = str(e).lower()
        if any(kw in err for kw in ["429", "quota", "rate limit", "insufficient"]):
            print(f"Groq rate limit/quota error: {e}")
        else:
            print(f"LLM error: {e}")
            traceback.print_exc()
        return None


def detect_language(text: str) -> str:
    spanish_patterns = [
        r'\b(hola|quiero|me gustaría|busco|destinos|vuelos|baratos|económico|viajar|desde|presupuesto)\b',
        r'[¿¡]',
    ]
    for pattern in spanish_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "es"
    return "en"


def collect_preferences(state: AgentState) -> dict:
    last_message = state["messages"][-1].content if state["messages"] else ""
    lang = detect_language(last_message)

    system_prompt = f"""You are a travel preference extractor. Extract travel preferences from the user's message.
Respond in JSON only with these fields:
- "origin": city of departure (null if not mentioned)
- "budget": budget with currency (null if not mentioned)
- "dates": travel dates or month (null if not mentioned)
- "duration": trip duration (null if not mentioned)
- "interests": array of interests (empty if not mentioned)
- "travel_style": "solo", "couple", "family", "friends", or null

User language: {"Spanish" if lang == "es" else "English"}"""

    content = llm_invoke_safe(system_prompt, f"User message: {last_message}", lang)

    if content:
        try:
            preferences = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        except json.JSONDecodeError:
            preferences = {
                "origin": None, "budget": None, "dates": None,
                "duration": None, "interests": [], "travel_style": None,
            }
    else:
        lang_from_msg = detect_language(last_message)
        preferences = {
            "origin": None,
            "budget": "2000 USD" if "2000" in last_message else None,
            "dates": "octubre" if "octubre" in last_message or "October" in last_message else None,
            "duration": "3 dias" if "3" in last_message else None,
            "interests": ["travel"],
            "travel_style": None,
        }
        lang = lang_from_msg

    return {
        "preferences": preferences,
        "language": lang,
        "iteration": state.get("iteration", 0) + 1,
    }


def generate_queries(state: AgentState) -> dict:
    prefs = state["preferences"]
    queries = generate_search_queries(
        origin=prefs.get("origin", ""),
        dates=prefs.get("dates", ""),
        budget=prefs.get("budget", ""),
        interests=prefs.get("interests", []),
        language=state["language"],
    )
    return {"search_queries": queries[:8]}


async def search_and_scrape(state: AgentState) -> dict:
    queries = state.get("search_queries", [])
    all_results = []
    all_content = []

    for q in queries:
        results = await search_web(q, max_results=4)
        for r in results:
            r["query"] = q
        all_results.extend(results)

    seen_urls = set()
    unique = []
    for r in all_results:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(r)

    for item in unique[:10]:
        text = await scrape_url(item.get("url", ""), max_chars=2000)
        if text:
            all_content.append({"url": item["url"], "title": item.get("title", ""), "content": text})

    return {"search_results": unique[:15], "raw_content": all_content}


def extract_and_rank(state: AgentState) -> dict:
    lang = state["language"]
    prefs = state["preferences"]

    context_parts = []
    for item in state.get("raw_content", []):
        context_parts.append(f"Source: {item['title']} ({item['url']})\n{item['content'][:1500]}")

    search_snippets = []
    for r in state.get("search_results", []):
        search_snippets.append(f"- {r.get('title', '')}: {r.get('content', '')[:200]}")

    system_prompt = f"""You are a budget travel expert. Analyze the travel search results and extract 3-7 low-cost destinations.

For each destination, provide a JSON object with:
- "name": City name
- "country": Country
- "estimated_price": Price estimate (range or fixed)
- "currency": "EUR" or "USD" etc
- "best_season": When to go
- "why_lowcost": Why it's affordable now
- "value_score": 1-5 (value for money)
- "activities": array of 2-4 things to do
- "source": Where this info came from
- "weather_note": Brief weather note

Respond with a JSON array only. No markdown. No explanation.

User preferences: {json.dumps(prefs)}
Language: {'Spanish' if lang == 'es' else 'English'}
"""
    search_text = "\n".join(search_snippets[:20])
    context_text = "\n\n".join(context_parts[:5])

    content = llm_invoke_safe(system_prompt, f"Search results:\n{search_text}\n\nDetailed content:\n{context_text}", lang)

    destinations = []
    if content:
        try:
            raw = content.strip()
            raw = raw.removeprefix("```json").removesuffix("```").strip()
            destinations = json.loads(raw)
        except json.JSONDecodeError:
            pass

    if not destinations and state.get("search_results"):
        seen_names = set()
        for r in state["search_results"]:
            title = r.get("title", "")
            snippet = r.get("content", "")[:200]
            combined = (title + " " + snippet).lower()
            if not any(kw in combined for kw in ["cheap", "budget", "low cost", "affordable", "deal", "barato", "económico", "oferta", "viaje", "travel", "destino", "destination", "vacation", "vacaciones"]):
                continue

            name = r.get("name", title.split(":")[0].split(" - ")[0].split("|")[0].strip())[:35]
            if not name or name in seen_names:
                continue
            seen_names.add(name)

            price_match = re.search(r'(\d+[\.,]?\d*)\s*(EUR|USD|€|\$)', snippet)
            price = price_match.group(0) if price_match else "Varía según fecha"
            currency = "EUR" if price_match and price_match.group(2) in ("EUR", "€") else "USD"

            destinations.append({
                "name": name,
                "country": "",
                "estimated_price": price,
                "currency": currency,
                "best_season": "Consultar fuente",
                "why_lowcost": snippet[:150],
                "value_score": 3,
                "activities": ["Travel", "Explore"],
                "source": r.get("url", ""),
            })
            if len(destinations) >= 5:
                break

    return {"destinations": destinations}


def generate_response(state: AgentState) -> dict:
    lang = state["language"]
    prefs = state["preferences"]
    destinations = state.get("destinations", [])

    if not destinations:
        msg_es = "Lo siento, no pude encontrar destinos low-cost con esa información. ¿Puedes darme más detalles como ciudad de origen, fechas o presupuesto?"
        msg_en = "Sorry, I couldn't find low-cost destinations with that information. Can you provide more details like your origin city, dates, or budget?"
        return {"response_message": msg_es if lang == "es" else msg_en}

    dest_list = "\n".join(
        f"- {d.get('name', '?')}, {d.get('country', '?')}: ~{d.get('estimated_price', '?')} {d.get('currency', 'EUR')} (⭐{d.get('value_score', 3)}/5)"
        for d in destinations[:7]
    )

    if lang == "es":
        msg = f"🎯 **Destinos low-cost recomendados para ti:**\n\n{dest_list}\n\n¿Te interesa alguno en particular? Puedo darte más detalles o ajustar la búsqueda."
    else:
        msg = f"🎯 **Recommended low-cost destinations for you:**\n\n{dest_list}\n\nInterested in any of these? I can give you more details or refine the search."

    return {"response_message": msg}
