from tavily import TavilyClient
from bs4 import BeautifulSoup
import httpx
from typing import Optional
from app.config import get_settings


settings = get_settings()
tavily_client = TavilyClient(api_key=settings.tavily_api_key) if settings.tavily_api_key else None


async def search_web(query: str, max_results: int = 5) -> list[dict]:
    if tavily_client:
        response = tavily_client.search(query=query, max_results=max_results)
        return response.get("results", [])
    return []


async def scrape_url(url: str, max_chars: int = 3000) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return text[:max_chars]
    except Exception:
        return None


def generate_search_queries(
    origin: str, dates: str, budget: str,
    interests: list[str], language: str,
    desired_destination: str = "",
    duration: str = "",
) -> list[str]:
    queries = []
    lang = language if language in ("es", "en") else "en"
    b = budget.replace("€", "euros").replace("$", "dollars") if budget else ""

    if desired_destination:
        d = desired_destination
        if lang == "en":
            queries.extend([
                f"cheap flights to {d} from {origin} {dates} 2026" if origin else f"cheap flights to {d} {dates} 2026",
                f"budget travel to {d} {dates} 2026",
                f"how to visit {d} on a budget {dates} 2026",
                f"cost of traveling to {d} {dates} 2026",
                f"{d} travel guide budget {dates} 2026",
                f"cheap accommodation {d} {dates} 2026",
                f"{d} trip cost low budget 2026",
            ])
        else:
            queries.extend([
                f"vuelos baratos a {d} desde {origin} {dates} 2026" if origin else f"vuelos baratos a {d} {dates} 2026",
                f"viajar a {d} barato {dates} 2026",
                f"presupuesto para viajar a {d} {dates} 2026",
                f"cuanto cuesta viajar a {d} {dates} 2026",
                f"{d} viaje económico {dates} 2026",
                f"alojamiento barato {d} {dates} 2026",
                f"consejos viaje {d} low cost {dates} 2026",
            ])

        if duration and b:
            if lang == "en":
                queries.append(f"travel to {d} {duration} under {b} 2026")
            else:
                queries.append(f"viajar a {d} {duration} presupuesto {b} 2026")
        elif duration:
            if lang == "en":
                queries.append(f"{d} trip {duration} budget 2026")
            else:
                queries.append(f"viajar a {d} {duration} barato 2026")
        elif b:
            if lang == "en":
                queries.append(f"visit {d} on a budget {b} 2026")
                queries.append(f"how much does it cost to travel to {d} {b} 2026")
            else:
                queries.append(f"viajar a {d} presupuesto {b} 2026")
                queries.append(f"cuanto cuesta viajar a {d} {b} 2026")

        return queries

    if lang == "en":
        queries.extend([
            f"cheap flights from {origin} {dates} 2026" if origin else f"cheapest travel destinations {dates} 2026",
            f"budget travel destinations {dates} 2026",
            f"best low cost holidays from {origin} {dates} 2026" if origin else f"best low cost holidays {dates} 2026",
            f"cheapest places to visit {dates} 2026",
        ])
    else:
        queries.extend([
            f"vuelos baratos desde {origin} {dates} 2026" if origin else f"destinos baratos {dates} 2026",
            f"destinos económicos para viajar {dates} 2026",
            f"mejores destinos low cost desde {origin} {dates} 2026" if origin else f"mejores destinos low cost {dates} 2026",
            f"ofertas de viajes {dates} 2026",
        ])

    if interests:
        interest_query = " ".join(interests[:3])
        queries.append(f"{'travel' if lang == 'en' else 'viajes'} {interest_query} budget {dates} 2026")

    if budget:
        queries.append(f"vacation under {b} {dates} 2026" if lang == "en" else f"vacaciones por menos de {b} {dates} 2026")

    if origin:
        queries.append(f"cheap weekend getaways from {origin} {dates} 2026" if lang == "en" else f"escapadas baratas desde {origin} {dates} 2026")

    queries.extend([
        "secret flying deals europe 2026",
        "budget travel blog best value destinations 2026",
    ])

    return queries
