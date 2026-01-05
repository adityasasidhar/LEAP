"""Web scraping tools using Crawl4AI - powerful async web scraping."""
import asyncio
from langchain_core.tools import tool


def _run_async(coro):
    """Helper to run async code in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@tool
def crawl_webpage(url: str) -> str:
    """Crawl a webpage and extract clean markdown content using Crawl4AI.
    
    Args:
        url: The URL to crawl and extract content from
    """
    async def _crawl():
        from crawl4ai import AsyncWebCrawler
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            
            if not result.success:
                return f"Failed to crawl {url}: {result.error_message}"
            
            # Get markdown content (cleaner than raw HTML)
            content = result.markdown[:8000] if result.markdown else "No content extracted"
            
            return f"**Crawled: {url}**\n\nTitle: {result.title or 'N/A'}\n\n{content}"
    
    try:
        return _run_async(_crawl())
    except Exception as e:
        return f"Crawl error: {e}"


@tool
def crawl_with_js(url: str, wait_seconds: int = 2) -> str:
    """Crawl a JavaScript-heavy webpage, waiting for dynamic content to load.
    
    Args:
        url: The URL to crawl
        wait_seconds: Seconds to wait for JS to render (default: 2)
    """
    async def _crawl():
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
        
        config = CrawlerRunConfig(
            wait_until="networkidle",
            delay_before_return_html=wait_seconds,
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            
            if not result.success:
                return f"Failed to crawl {url}: {result.error_message}"
            
            content = result.markdown[:8000] if result.markdown else "No content extracted"
            
            return f"**Crawled (JS): {url}**\n\nTitle: {result.title or 'N/A'}\n\n{content}"
    
    try:
        return _run_async(_crawl())
    except Exception as e:
        return f"Crawl error: {e}"


@tool
def extract_links(url: str) -> str:
    """Extract all links from a webpage.
    
    Args:
        url: The URL to extract links from
    """
    async def _crawl():
        from crawl4ai import AsyncWebCrawler
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            
            if not result.success:
                return f"Failed to crawl {url}"
            
            links = result.links or {}
            internal = links.get('internal', [])[:20]
            external = links.get('external', [])[:20]
            
            output = [f"**Links from {url}**\n"]
            
            if internal:
                output.append("**Internal Links:**")
                for link in internal:
                    href = link.get('href', 'N/A')
                    text = link.get('text', '')[:50]
                    output.append(f"  • {text or 'No text'}: {href}")
            
            if external:
                output.append("\n**External Links:**")
                for link in external:
                    href = link.get('href', 'N/A')
                    text = link.get('text', '')[:50]
                    output.append(f"  • {text or 'No text'}: {href}")
            
            return "\n".join(output)
    
    try:
        return _run_async(_crawl())
    except Exception as e:
        return f"Extract links error: {e}"


@tool
def extract_images(url: str) -> str:
    """Extract all images from a webpage.
    
    Args:
        url: The URL to extract images from
    """
    async def _crawl():
        from crawl4ai import AsyncWebCrawler
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            
            if not result.success:
                return f"Failed to crawl {url}"
            
            images = result.media.get('images', [])[:15] if result.media else []
            
            if not images:
                return f"No images found on {url}"
            
            output = [f"**Images from {url}** ({len(images)} found)\n"]
            for i, img in enumerate(images, 1):
                src = img.get('src', 'N/A')
                alt = img.get('alt', 'No alt text')[:60]
                output.append(f"{i}. {alt}\n   {src}")
            
            return "\n".join(output)
    
    try:
        return _run_async(_crawl())
    except Exception as e:
        return f"Extract images error: {e}"


@tool  
def screenshot_webpage(url: str) -> str:
    """Take a screenshot of a webpage and save it.
    
    Args:
        url: The URL to screenshot
    """
    async def _crawl():
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
        import base64
        import os
        
        config = CrawlerRunConfig(
            screenshot=True,
            wait_until="networkidle",
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            
            if not result.success:
                return f"Failed to screenshot {url}"
            
            if result.screenshot:
                # Save screenshot
                filename = f"/tmp/screenshot_{url.replace('/', '_').replace(':', '')[:50]}.png"
                img_data = base64.b64decode(result.screenshot)
                with open(filename, 'wb') as f:
                    f.write(img_data)
                return f"Screenshot saved to: {filename}\nTitle: {result.title}"
            
            return "No screenshot captured"
    
    try:
        return _run_async(_crawl())
    except Exception as e:
        return f"Screenshot error: {e}"


# Export all crawl4ai tools
CRAWL_TOOLS = [
    crawl_webpage,
    crawl_with_js,
    extract_links,
    extract_images,
    screenshot_webpage,
]
