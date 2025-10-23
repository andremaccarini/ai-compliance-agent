import time
import requests
import yaml
from requests.exceptions import HTTPError, RequestException

CFG = yaml.safe_load(open('configs/config.yaml', 'r'))
MAX_ARTS = int(CFG['news'].get('max_articles', 10))
TIMESPAN = CFG['news'].get('timespan', '30d')

GDELT_ENDPOINT = 'https://api.gdeltproject.org/api/v2/doc/doc'
HEADERS = {"User-Agent": "ai-compliance-agent/0.1 (+local)"}

def _gdelt_get(params, retries=3, backoff=1.8):
    """
    GET com backoff exponencial para HTTP 429/5xx.
    """
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(GDELT_ENDPOINT, params=params, headers=HEADERS, timeout=30)
            if r.status_code == 429:

                sleep_s = (backoff ** attempt) + 0.5
                time.sleep(sleep_s)
                continue
            r.raise_for_status()
            return r
        except (HTTPError, RequestException) as e:
            last_exc = e

            if getattr(e.response, "status_code", None) and 500 <= e.response.status_code < 600:
                time.sleep((backoff ** attempt) + 0.5)
                continue
            break

    if last_exc:
        raise last_exc

def search_company_news(company: str, max_articles: int = MAX_ARTS, timespan: str = TIMESPAN):
    """
    Faz uma busca simples por manchetes recentes sobre 'company'.
    Implementa backoff e retorna [] em erros tratáveis para o app mostrar mensagem amigável.
    """

    quoted = f"\"{company}\""

    params = {
        "query": quoted,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max_articles,
        "timespan": timespan,
        "sort": "DateDesc",
    }

    try:
        r = _gdelt_get(params, retries=4, backoff=2.0)
        js = r.json()
    except HTTPError as e:

        if e.response is not None and e.response.status_code == 429:
            return []

        raise
    except RequestException:

        return []

    arts = []
    for item in js.get('articles', []):
        arts.append({
            'title': item.get('title'),
            'url': item.get('url'),
            'domain': item.get('domain'),
            'language': item.get('language'),
            'seendate': item.get('seendate')
        })
    return arts
