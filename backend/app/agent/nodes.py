import json
import re
import traceback
import unicodedata
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
        temperature=0.1,
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


def _normalize_text(text: str) -> str:
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _text_contains_term(text: str, term: str) -> bool:
    return _normalize_text(term) in _normalize_text(text)


DEST_STOP_WORDS = {
    "con", "un", "una", "de", "del", "la", "el", "los", "las", "para", "por",
    "en", "y", "e", "o", "u", "the", "a", "an", "with", "for", "and", "or",
    "presupuesto", "budget", "usd", "eur", "euros", "dollars", "dolares",
    "dólares", "mi", "my", "from", "desde", "que", "qué",
}


def _sanitize_destination(name: str) -> str:
    if not name or not name.strip():
        return ""
    words = re.findall(r"[A-Za-zÀ-ÿ]+", name)
    clean: list[str] = []
    for word in words:
        if word.lower() in DEST_STOP_WORDS:
            break
        clean.append(word)
    if not clean:
        return name.strip().title()
    return " ".join(w.capitalize() for w in clean)


def _extract_destination_regex(message: str) -> str | None:
    skip_leading = {"un", "una", "el", "la", "los", "las", "the", "a", "an", "mi", "my"}
    patterns = [
        r"(?:quiero\s+)?(?:viajar|ir|travel|visit)\s+(?:a|to)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)",
        r"^([A-Za-zÀ-ÿ]+)\s+\d+\s*(?:d[ií]as?|days?)",
        r"(?:a|para|visitar|visit|to)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            sanitized = _sanitize_destination(match.group(1).strip())
            if sanitized and _normalize_text(sanitized) not in skip_leading:
                return sanitized
    return None


def _destination_matches_text(text: str, destination: str) -> bool:
    if not destination:
        return True
    if _text_contains_term(text, destination):
        return True
    sanitized = _sanitize_destination(destination)
    primary = sanitized.split()[0] if sanitized else ""
    return len(primary) >= 3 and _text_contains_term(text, primary)


def _finalize_destination_preference(preferences: dict, message: str) -> dict:
    regex_dest = _extract_destination_regex(message)
    if regex_dest:
        preferences["desired_destination"] = regex_dest
    elif preferences.get("desired_destination"):
        preferences["desired_destination"] = _sanitize_destination(preferences["desired_destination"])
    else:
        preferences["desired_destination"] = None
    return preferences


def _extract_budget_regex(message: str) -> str | None:
    patterns = [
        r"presupuesto\s+(?:de\s+)?(\d+[\.,]?\d*\s*(?:USD|EUR|usd|eur|€|\$|euros?|dólares?|dolares?))",
        r"(\d+[\.,]?\d*)\s*(USD|EUR|usd|eur|euros?|dólares?|dolares?)",
        r"(\d+)\s*€",
        r"€\s*(\d+)",
        r"\$\s*(\d+)",
        r"(\d+)\s*\$",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _extract_duration_regex(message: str) -> str | None:
    match = re.search(r"(\d+)\s*(d[ií]as?|days?)", message, re.IGNORECASE)
    return match.group(0) if match else None


def _enrich_preferences_from_message(preferences: dict, message: str) -> dict:
    if not preferences.get("budget"):
        budget = _extract_budget_regex(message)
        if budget:
            preferences["budget"] = budget
    if not preferences.get("duration"):
        duration = _extract_duration_regex(message)
        if duration:
            preferences["duration"] = duration
    return _finalize_destination_preference(preferences, message)


def collect_preferences(state: AgentState) -> dict:
    last_message = state["messages"][-1].content if state["messages"] else ""
    lang = detect_language(last_message)

    system_prompt = f"""You are a travel preference extractor. Extract travel preferences from the user's message.

CRITICAL: If the user mentions a specific destination city or country they want to visit, put ONLY the place name in "desired_destination" (e.g. "Cancun", not "Cancun con presupuesto"). Do NOT include prepositions or budget words in the destination name.

Respond in JSON only with these fields:
- "origin": city of departure (null if not mentioned)
- "budget": budget with currency (null if not mentioned)
- "dates": travel dates or month (null if not mentioned)
- "duration": trip duration (null if not mentioned)
- "interests": array of interests (empty if not mentioned)
- "travel_style": "solo", "couple", "family", "friends", or null
- "desired_destination": the specific place the user wants to go to (null if not mentioned)

User language: {"Spanish" if lang == "es" else "English"}"""

    content = llm_invoke_safe(system_prompt, f"User message: {last_message}", lang)

    if content:
        try:
            preferences = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
            if "desired_destination" not in preferences:
                preferences["desired_destination"] = None
            preferences = _enrich_preferences_from_message(preferences, last_message)
        except json.JSONDecodeError:
            preferences = {
                "origin": None, "budget": None, "dates": None,
                "duration": None, "interests": [], "travel_style": None,
                "desired_destination": None,
            }
            preferences = _enrich_preferences_from_message(preferences, last_message)
    else:
        lang_from_msg = detect_language(last_message)
        preferences = {
            "origin": None,
            "budget": _extract_budget_regex(last_message),
            "dates": "octubre" if "octubre" in last_message.lower() or "october" in last_message.lower() else None,
            "duration": _extract_duration_regex(last_message),
            "interests": ["travel"],
            "travel_style": None,
            "desired_destination": _extract_destination_regex(last_message),
        }
        preferences = _finalize_destination_preference(preferences, last_message)
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
        desired_destination=prefs.get("desired_destination", ""),
        duration=prefs.get("duration", ""),
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


def _parse_price(price_str: str) -> tuple[float | None, str | None]:
    if not price_str:
        return None, None

    s = price_str.strip()
    currency = None
    if re.search(r"\$|USD", s, re.IGNORECASE):
        currency = "USD"
    elif re.search(r"€|EUR", s, re.IGNORECASE):
        currency = "EUR"

    num_part = re.sub(r"[€$]|\b(EUR|USD)\b", "", s, flags=re.IGNORECASE).strip()
    match = re.search(r"(\d[\d.,]*)", num_part)
    if not match:
        return None, currency

    num_str = match.group(1)

    if "," in num_str and "." in num_str:
        if num_str.rfind(",") > num_str.rfind("."):
            num_str = num_str.replace(".", "").replace(",", ".")
        else:
            num_str = num_str.replace(",", "")
    elif "," in num_str:
        parts = num_str.split(",")
        if len(parts[-1]) == 2:
            num_str = num_str.replace(",", ".")
        else:
            num_str = num_str.replace(",", "")
    elif "." in num_str:
        parts = num_str.split(".")
        if len(parts[-1]) == 3 and len(parts) > 1:
            num_str = num_str.replace(".", "")

    try:
        return float(num_str), currency
    except ValueError:
        return None, currency


def _get_budget_value(budget_str: str | None) -> tuple[float | None, str | None]:
    if not budget_str:
        return None, None
    value, currency = _parse_price(budget_str)
    if currency is None:
        if "usd" in budget_str.lower() or "$" in budget_str:
            currency = "USD"
        elif "eur" in budget_str.lower() or "€" in budget_str or "euro" in budget_str.lower():
            currency = "EUR"
    return value, currency


def _price_appears_in_text(price_str: str, text: str) -> bool:
    if not price_str or not text:
        return False
    if _normalize_text(price_str) in _normalize_text(text):
        return True
    price_num, _ = _parse_price(price_str)
    if price_num is None:
        return False
    compact = re.sub(r"[^\d]", "", text)
    num_str = str(int(price_num)) if price_num == int(price_num) else str(price_num).replace(".", "")
    return num_str in compact


def _is_grounded_in_sources(
    dest: dict,
    search_results: list[dict],
    raw_content: list[dict],
    allowed_urls: set[str],
) -> bool:
    name = dest.get("name", "")
    price = str(dest.get("estimated_price", ""))
    source = dest.get("source", "")

    if not name or not price or not source:
        return False

    if source not in allowed_urls:
        return False

    corpus_parts: list[str] = []
    for r in search_results:
        if r.get("url") == source:
            corpus_parts.append(f"{r.get('title', '')} {r.get('content', '')}")
    for item in raw_content:
        if item.get("url") == source:
            corpus_parts.append(f"{item.get('title', '')} {item.get('content', '')}")

    corpus = " ".join(corpus_parts)
    if not corpus:
        return False

    if not _destination_matches_text(corpus, name):
        return False

    return _price_appears_in_text(price, corpus)


def _normalize_currency(curr: str | None) -> str | None:
    if curr in ("€", "EUR"):
        return "EUR"
    if curr in ("$", "USD"):
        return "USD"
    return curr


def _convert_currency(amount: float, from_curr: str, to_curr: str) -> float:
    if from_curr == to_curr:
        return amount
    # Fixed approximate rate for budget comparison only
    if from_curr == "USD" and to_curr == "EUR":
        return amount * 0.92
    if from_curr == "EUR" and to_curr == "USD":
        return amount * 1.08
    return amount


def _price_exceeds_budget(price_str: str, budget_value: float | None, budget_currency: str | None) -> bool:
    if budget_value is None:
        return False
    price_num, price_currency = _parse_price(price_str)
    if price_num is None:
        return False

    if 2020 <= price_num <= 2040:
        return True

    budget_curr_norm = _normalize_currency(budget_currency)
    price_curr_norm = _normalize_currency(price_currency)

    if budget_curr_norm and not price_curr_norm:
        return True

    if price_curr_norm and budget_curr_norm and price_curr_norm != budget_curr_norm:
        price_num = _convert_currency(price_num, price_curr_norm, budget_curr_norm)

    return price_num > budget_value


def _extract_destinations_from_results(
    results: list[dict],
    desired_dest: str,
    budget_value: float | None,
    budget_currency: str | None,
    lang: str,
    seen_names: set | None = None,
) -> list[dict]:
    seen = seen_names or set()
    destinations = []
    required_term = desired_dest if desired_dest else None

    for r in results:
        title = r.get("title", "")
        snippet = r.get("content", "")[:300]
        combined = title + " " + snippet

        if required_term and not _destination_matches_text(combined, required_term):
            continue

        price_match = re.search(
            r"(?:(\d+[\.,]?\d*)\s*(EUR|USD|€|\$)|(€|\$)\s*(\d+[\.,]?\d*))",
            snippet,
        )
        if not price_match:
            continue

        price_str = price_match.group(0).strip()
        price_num, currency = _parse_price(price_str)
        if price_num is None:
            continue

        if 2020 <= price_num <= 2040:
            continue

        if currency is None:
            if price_match.group(2) in ("$", "USD") or price_match.group(3) == "$":
                currency = "USD"
            elif price_match.group(2) in ("€", "EUR") or price_match.group(3) == "€":
                currency = "EUR"

        if not _price_appears_in_text(price_str, snippet):
            continue

        if budget_value and _price_exceeds_budget(price_str, budget_value, budget_currency):
            continue

        if required_term:
            name = desired_dest
        else:
            name = None
            dest_match = re.search(
                r"(?:travel|viajar|going|visit|visitar|destination|destino)\s+(?:to|a|en)\s+(\w+(?:\s+\w+)?)",
                combined,
                re.IGNORECASE,
            )
            if dest_match:
                candidate = dest_match.group(1).strip().capitalize()
                if len(candidate) > 2:
                    name = candidate

            if not name:
                stop_words = {
                    "the", "a", "an", "top", "best", "cheap", "budget", "guide", "viaje",
                    "viajes", "verano", "travel", "destinos", "destinations", "guía",
                    "los", "las", "how", "why", "qué", "que", "consejos", "tips",
                    "ultimate", "complete", "ofertas", "deals", "mejores", "best",
                }
                first_word = title.split()[0].strip(".,!?;:") if title.split() else ""
                if first_word.lower() not in stop_words and len(first_word) > 2:
                    name = first_word

        if not name:
            continue

        name_clean = name.strip().rstrip(".,!?;:")
        nl = _normalize_text(name_clean)
        if not name_clean or nl in seen:
            continue
        seen.add(nl)

        destinations.append({
            "name": name_clean,
            "country": "",
            "estimated_price": price_str,
            "currency": currency or "EUR",
            "best_season": "",
            "why_lowcost": snippet[:150],
            "value_score": 3,
            "activities": ["Travel", "Explore"],
            "source": r.get("url", ""),
        })

        if len(destinations) >= 5:
            break

    return destinations


def extract_and_rank(state: AgentState) -> dict:
    lang = state["language"]
    prefs = state["preferences"]
    desired_dest = prefs.get("desired_destination", "")
    budget_value, budget_currency = _get_budget_value(prefs.get("budget"))

    search_results = state.get("search_results", [])
    raw_content = state.get("raw_content", [])
    allowed_urls = {r.get("url", "") for r in search_results if r.get("url")}

    all_seen_names = set()
    desired_destinations = []
    other_destinations = []

    if desired_dest:
        desired_results = [
            r for r in search_results
            if _destination_matches_text(r.get("title", "") + r.get("content", ""), desired_dest)
        ]
        if desired_results:
            desired_destinations = _extract_destinations_from_results(
                desired_results, desired_dest, budget_value, budget_currency, lang, all_seen_names,
            )
    else:
        other_destinations = _extract_destinations_from_results(
            search_results, "", budget_value, budget_currency, lang, all_seen_names,
        )

    if desired_dest:
        all_destinations = desired_destinations
    else:
        all_destinations = other_destinations[:7]

    if not all_destinations and search_results:
        context_parts = []
        for item in state.get("raw_content", []):
            context_parts.append(f"Source: {item['title']} ({item['url']})\n{item['content'][:1500]}")

        search_snippets = []
        for r in search_results:
            search_snippets.append(f"- {r.get('title', '')}: {r.get('content', '')[:200]}")

        focus = f"CRITICAL: The user asked about {desired_dest}. Focus ONLY on {desired_dest}." if desired_dest else ""
        budget_note = f"CRITICAL BUDGET: Max {budget_value} {budget_currency or ''}. Every price MUST be under this." if budget_value else ""

        system_prompt = f"""You are a budget travel expert. Extract low-cost destinations ONLY from the search results below.

{focus}
{budget_note}

STRICT RULES — violations mean the answer is rejected:
- ONLY extract destinations and prices that appear verbatim in the search results.
- For each item you MUST include the exact "source" URL from the search results where you found the price.
- estimated_price MUST be copied exactly from the source text — never estimate or round.
- DO NOT invent destinations, prices, URLs, or countries.
- If no valid grounded results exist, respond with an empty JSON array: []
- Respond with a JSON array only.

Language: {'Spanish' if lang == 'es' else 'English'}
"""
        content = llm_invoke_safe(
            system_prompt,
            f"Search snippets:\n{chr(10).join(search_snippets[:15])}\n\nDetailed content:\n{chr(10).join(context_parts[:3])}",
            lang,
        )

        if content:
            try:
                raw = content.strip().removeprefix("```json").removesuffix("```").strip()
                parsed = json.loads(raw)
                for d in parsed:
                    price = d.get("estimated_price", "")
                    if desired_dest and not _destination_matches_text(d.get("name", ""), desired_dest):
                        continue
                    if budget_value and _price_exceeds_budget(price, budget_value, budget_currency):
                        continue
                    if not _is_grounded_in_sources(d, search_results, raw_content, allowed_urls):
                        continue
                    name_key = _normalize_text(d.get("name", ""))
                    if name_key in all_seen_names:
                        continue
                    all_seen_names.add(name_key)
                    all_destinations.append(d)
            except json.JSONDecodeError:
                pass

    return {"destinations": all_destinations[:7]}


def generate_response(state: AgentState) -> dict:
    lang = state["language"]
    prefs = state["preferences"]
    destinations = state.get("destinations", [])

    prefs = state["preferences"]
    desired_dest = prefs.get("desired_destination", "")
    budget_value, budget_currency = _get_budget_value(prefs.get("budget"))
    budget_info = f" (máx. {budget_value} {budget_currency})" if budget_value else ""

    def _looks_valid(dest: dict) -> bool:
        name = dest.get("name", "")
        if not name or len(name) < 3 or len(name) > 40:
            return False
        price_num, _ = _parse_price(dest.get("estimated_price", ""))
        if price_num is not None and 2020 <= price_num <= 2040:
            return False
        return True

    destinations = [d for d in destinations if _looks_valid(d)]

    in_budget = []
    over_budget = []
    for d in destinations:
        price = d.get("estimated_price", "")
        if budget_value and _price_exceeds_budget(price, budget_value, budget_currency):
            over_budget.append(d)
        else:
            in_budget.append(d)

    shown = in_budget[:7]

    if not shown:
        if desired_dest:
            msg_es = f"No encontré información específica sobre {desired_dest} dentro de tu presupuesto{budget_info}. ¿Quieres probar con otro destino o ajustar el presupuesto?"
            msg_en = f"I couldn't find specific information about {desired_dest} within your budget{budget_info}. Want to try another destination or adjust your budget?"
        else:
            msg_es = "Lo siento, no pude encontrar destinos low-cost con esa información. ¿Puedes darme más detalles como ciudad de origen, fechas o presupuesto?"
            msg_en = "Sorry, I couldn't find low-cost destinations with that information. Can you provide more details like your origin city, dates, or budget?"
        return {"response_message": msg_es if lang == "es" else msg_en, "destinations": []}

    dest_list = "\n".join(
        f"- {d.get('name', '?')}: ~{d.get('estimated_price', '?')} {d.get('currency', 'EUR')} (⭐{d.get('value_score', 3)}/5)"
        for d in shown
    )

    if desired_dest:
        if lang == "es":
            msg = f"📌 **Información sobre {desired_dest}{budget_info}:**\n\n{dest_list}\n\n¿Quieres más detalles o ajustar algo?"
        else:
            msg = f"📌 **Information about {desired_dest}{budget_info}:**\n\n{dest_list}\n\nWant more details or adjust something?"
    else:
        if lang == "es":
            msg = f"🎯 **Destinos dentro de tu presupuesto{budget_info}:**\n\n{dest_list}\n\n¿Te interesa alguno? Puedo darte más detalles."
        else:
            msg = f"🎯 **Destinations within your budget{budget_info}:**\n\n{dest_list}\n\nInterested in any of these? I can give you more details."

    return {"response_message": msg, "destinations": shown}
