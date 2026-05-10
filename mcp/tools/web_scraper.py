"""
Web scraping tool using Playwright.
Use for: scraping URLs the user shares, competitor analysis, pricing research.
"""

import asyncio
import ipaddress
import re
from urllib.parse import urlparse


def _is_safe_url(url: str) -> tuple[bool, str]:
    """
    SSRF protection: validate URL before fetching.
    Blocks internal IPs, private ranges, localhost, and non-HTTP schemes.
    """
    parsed = urlparse(url)

    # Only allow http/https
    if parsed.scheme not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are allowed."

    # Enforce HTTPS in production (optional, can be relaxed for dev)
    # if parsed.scheme != "https":
    #     return False, "Only HTTPS URLs are allowed for security."

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: no hostname found."

    # Block localhost and common internal hostnames
    blocked_hostnames = {
        "localhost", "127.0.0.1", "0.0.0.0", "::1",
        "10.0.0.1", "192.168.1.1", "172.16.0.1",
    }
    if hostname.lower() in blocked_hostnames:
        return False, "Access to internal/localhost addresses is not allowed."

    # Block common internal TLDs and patterns
    if re.search(r'\.(internal|local|corp|home|lan|private|test)$', hostname, re.I):
        return False, "Internal domain names are not allowed."

    # Block IP-based URLs to prevent private IP access
    try:
        ip = ipaddress.ip_address(hostname)
        # Block all private, loopback, link-local, reserved, and multicast
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False, "Access to internal IP addresses is not allowed."
    except ValueError:
        pass  # Not an IP, proceed

    # Block metadata endpoints (AWS, GCP, Azure)
    if re.match(r'169\.254\.\d+\.\d+', hostname) or hostname == "metadata.google.internal":
        return False, "Access to cloud metadata endpoints is not allowed."

    return True, ""


async def _scrape_async(url: str) -> dict:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        # Remove noise
        await page.evaluate("""() => {
            document.querySelectorAll('script,style,nav,footer,aside,[role=navigation]')
                    .forEach(el => el.remove());
        }""")
        title = await page.title()
        content = await page.evaluate("() => document.body.innerText")
        await browser.close()
        return {"title": title, "content": content[:6000]}


def scrape_webpage(url: str, user_id: int) -> dict:
    """MCP tool: scrape a webpage and return its text content."""
    is_safe, reason = _is_safe_url(url)
    if not is_safe:
        return {"error": f"URL not allowed: {reason}"}

    try:
        result = asyncio.run(_scrape_async(url))
        return {
            "result": {
                "url": url,
                "title": result["title"],
                "content_preview": result["content"][:500],
                "full_content": result["content"],
            },
            "insight": f"Scraped '{result['title']}' from {url}."
        }
    except Exception as e:
        return {"error": f"Could not scrape URL: {str(e)}"}
