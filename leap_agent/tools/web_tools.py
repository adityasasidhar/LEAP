"""Web tools for LEAP Agent - using DDGS (free, no API)."""


def web_search(query: str, num_results: int = 5) -> dict:
    """Search the web using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
        
        return {
            "query": query,
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")[:200],
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        return {"error": str(e), "query": query}


def news_search(query: str, num_results: int = 5) -> dict:
    """Search for recent news."""
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=num_results))
        
        return {
            "query": query,
            "articles": [
                {
                    "title": r.get("title", ""),
                    "source": r.get("source", ""),
                    "date": r.get("date", ""),
                    "url": r.get("url", ""),
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        return {"error": str(e), "query": query}


def fetch_url(url: str, max_length: int = 5000) -> dict:
    """Fetch webpage content."""
    import urllib.request
    import urllib.error
    import re
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
        
        # Clean HTML
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.I)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.I)
        content = re.sub(r'<[^>]+>', ' ', content)
        content = re.sub(r'\s+', ' ', content).strip()
        
        return {
            "url": url,
            "content": content[:max_length],
            "length": len(content),
            "truncated": len(content) > max_length,
        }
    except Exception as e:
        return {"error": str(e), "url": url}


def crawl_webpage(url: str) -> dict:
    """Crawl webpage using crawl4ai for better extraction."""
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler
        
        async def _crawl():
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                return result
        
        # Run async
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(asyncio.run, _crawl()).result()
            else:
                result = loop.run_until_complete(_crawl())
        except RuntimeError:
            result = asyncio.run(_crawl())
        
        if not result.success:
            return {"error": result.error_message, "url": url}
        
        return {
            "url": url,
            "title": result.title or "",
            "content": result.markdown[:8000] if result.markdown else "",
            "links": len(result.links.get('internal', [])) if result.links else 0,
        }
    except ImportError:
        # Fallback to basic fetch
        return fetch_url(url)
    except Exception as e:
        return {"error": str(e), "url": url}
