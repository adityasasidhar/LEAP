"""Web/Search tools using DDGS (DuckDuckGo Search) - No API key required, unlimited."""
import urllib.request
import urllib.error
import re
from langchain_core.tools import tool


@tool
def web_search(query: str, num_results: int = 5) -> str:
    """Search the web using DuckDuckGo. Free, no API key required.
    
    Args:
        query: Search query string
        num_results: Number of results (default: 5)
    """
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
        
        if not results:
            return f"No results found for: '{query}'"
        
        output = [f"Search results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            output.append(f"{i}. **{r.get('title', 'No title')}**")
            output.append(f"   URL: {r.get('href', 'N/A')}")
            output.append(f"   {r.get('body', '')}\n")
        
        return "\n".join(output)
    except Exception as e:
        return f"Search error: {e}"


@tool
def news_search(query: str, num_results: int = 5) -> str:
    """Search for recent news articles using DuckDuckGo. Free, no API key.
    
    Args:
        query: News topic to search for
        num_results: Number of results (default: 5)
    """
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=num_results))
        
        if not results:
            return f"No news found for: '{query}'"
        
        output = [f"News results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            output.append(f"{i}. **{r.get('title', 'No title')}**")
            output.append(f"   Source: {r.get('source', 'Unknown')} | {r.get('date', 'No date')}")
            output.append(f"   URL: {r.get('url', 'N/A')}")
            output.append(f"   {r.get('body', '')}\n")
        
        return "\n".join(output)
    except Exception as e:
        return f"News search error: {e}"


@tool
def image_search(query: str, num_results: int = 5) -> str:
    """Search for images using DuckDuckGo. Returns image URLs. Free, no API key.
    
    Args:
        query: Image search query
        num_results: Number of results (default: 5)
    """
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=num_results))
        
        if not results:
            return f"No images found for: '{query}'"
        
        output = [f"Image results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            output.append(f"{i}. **{r.get('title', 'No title')}**")
            output.append(f"   Image: {r.get('image', 'N/A')}")
            output.append(f"   Source: {r.get('url', 'N/A')}")
            output.append(f"   Size: {r.get('width', '?')}x{r.get('height', '?')}\n")
        
        return "\n".join(output)
    except Exception as e:
        return f"Image search error: {e}"


@tool
def video_search(query: str, num_results: int = 5) -> str:
    """Search for videos using DuckDuckGo. Free, no API key.
    
    Args:
        query: Video search query
        num_results: Number of results (default: 5)
    """
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.videos(query, max_results=num_results))
        
        if not results:
            return f"No videos found for: '{query}'"
        
        output = [f"Video results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            output.append(f"{i}. **{r.get('title', 'No title')}**")
            output.append(f"   Publisher: {r.get('publisher', 'Unknown')} | Duration: {r.get('duration', 'N/A')}")
            output.append(f"   URL: {r.get('content', 'N/A')}\n")
        
        return "\n".join(output)
    except Exception as e:
        return f"Video search error: {e}"


@tool
def maps_search(query: str, place: str = "") -> str:
    """Search for places/locations using DuckDuckGo Maps. Free, no API key.
    
    Args:
        query: What to search for (e.g., "restaurants", "hotels")
        place: Location to search in (e.g., "New York", "London")
    """
    try:
        from duckduckgo_search import DDGS
        
        full_query = f"{query} {place}".strip()
        
        with DDGS() as ddgs:
            results = list(ddgs.maps(full_query, max_results=5))
        
        if not results:
            return f"No places found for: '{full_query}'"
        
        output = [f"Places for '{full_query}':\n"]
        for i, r in enumerate(results, 1):
            output.append(f"{i}. **{r.get('title', 'No name')}**")
            output.append(f"   Address: {r.get('address', 'N/A')}")
            output.append(f"   Phone: {r.get('phone', 'N/A')}")
            if r.get('url'):
                output.append(f"   Website: {r.get('url')}")
            output.append("")
        
        return "\n".join(output)
    except Exception as e:
        return f"Maps search error: {e}"


@tool
def fetch_url(url: str, max_length: int = 5000) -> str:
    """Fetch and extract text content from a URL.
    
    Args:
        url: The URL to fetch
        max_length: Max content length (default: 5000)
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
        
        # Remove scripts/styles and HTML tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<[^>]+>', ' ', content)
        content = re.sub(r'\s+', ' ', content).strip()
        
        if len(content) > max_length:
            content = content[:max_length] + "... (truncated)"
        
        return f"Content from {url}:\n\n{content}"
    except Exception as e:
        return f"Fetch error: {e}"


@tool
def answers_search(query: str) -> str:
    """Get instant answers from DuckDuckGo (definitions, calculations, facts). Free.
    
    Args:
        query: Question or topic to get an instant answer for
    """
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.answers(query))
        
        if not results:
            return f"No instant answer for: '{query}'"
        
        output = [f"Answers for '{query}':\n"]
        for r in results[:3]:
            output.append(f"**{r.get('text', 'No answer')}**")
            if r.get('url'):
                output.append(f"Source: {r.get('url')}")
            output.append("")
        
        return "\n".join(output)
    except Exception as e:
        return f"Answers error: {e}"


# Export all tools - all free, no API keys needed
WEB_TOOLS = [
    web_search,
    news_search, 
    image_search,
    video_search,
    maps_search,
    fetch_url,
    answers_search,
]
