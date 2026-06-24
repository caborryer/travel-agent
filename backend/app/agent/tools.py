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


def generate_search_queries(origin: str, dates: str, budget: str, interests: list[str], language: str) -> list[str]:
    queries = []
    lang = language if language in ("es", "en") else "en"

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
        queries.append(f"vacation under {budget} {'euros' if lang == 'en' else 'euros'} {dates} 2026")

    queries.append(f"cheap weekend getaways from {origin} {dates} 2026" if lang == "en" else f"escapadas baratas desde {origin} {dates} 2026")

    queries.extend([
        "secret flying deals europe 2026",
        "budget travel blog best value destinations 2026",
    ])

    return queries
