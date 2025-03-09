#!/usr/bin/env python3

GREEN = "\033[92m"
    # ANSI escape code to reset color
RESET = "\033[0m"
banner = f"""
{GREEN}##################################################################################
#
#  ██████╗██████╗  █████╗ ██╗    ██╗██╗     ███████╗██████╗
# ██╔════╝██╔══██╗██╔══██╗██║    ██║██║     ██╔════╝██╔══██╗
# ██║     ██████╔╝███████║██║ █╗ ██║██║     █████╗  ██████╔╝
# ██║     ██╔══██╗██╔══██║██║███╗██║██║     ██╔══╝  ██╔══██╗
# ╚██████╗██║  ██║██║  ██║╚███╔███╔╝███████╗███████╗██║  ██║
#  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝  ╚═╝
#
# Web Crawler with HTTP/2 Support — Built with Async Python & HTTPX
# Author: Mr.Ethical Yt | GitHub: https://github.com/jithender2
# Version: v1.0
##################################################################################{RESET}
    """

import argparse
import asyncio
import json
import logging
import re
import sys
import urllib.parse
from collections import deque

import httpx
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

unique_urls = set()

def parse_headers(raw_headers):
    if not raw_headers:
        return {}

    headers = {}
    header_pairs = raw_headers.split(";;")
    for pair in header_pairs:
        parts = pair.split(":", 1)
        if len(parts) == 2:
            key, value = parts[0].strip(), parts[1].strip()
            headers[key] = value
    return headers

def extract_hostname(url_string):
    try:
        parsed_url = urllib.parse.urlparse(url_string)
        if not parsed_url.netloc:
            raise ValueError("Input must be a valid absolute URL")
        return parsed_url.netloc
    except ValueError as e:
        raise e

def extract_links(html_content, base_url, inside):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []

    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        abs_link = urllib.parse.urljoin(base_url, link)
        if inside and urllib.parse.urlparse(abs_link).netloc != urllib.parse.urlparse(base_url).netloc:
            continue
        links.append((abs_link, "href", base_url))

    for script_tag in soup.find_all('script', src=True):
        link = script_tag['src']
        links.append((urllib.parse.urljoin(base_url, link), "script", base_url))

    for form_tag in soup.find_all('form', action=True):
        link = form_tag['action']
        links.append((urllib.parse.urljoin(base_url, link), "form", base_url))

    return links

async def fetch(client, url, headers, timeout):
    try:
        response = await client.get(url, headers=headers, timeout=timeout, follow_redirects=False)
        return response.text, response.status_code
    except httpx.TimeoutException:
        logger.warning(f"[timeout] {url}")
        return None, None
    except httpx.RequestError as e:
        logger.warning(f"[error] {url}: {e}")
        return None, None
    except Exception as e:
        logger.warning(f"[unexpected error] {url}: {e}")
        return None, None

async def crawl(url, headers, proxy, depth, inside, subs_in_scope, show_source, show_where, show_json, timeout, threads, insecure):
    hostname = extract_hostname(url)
    allowed_domains = [hostname]

    if "Host" in headers:
        allowed_domains.append(headers["Host"])

    if subs_in_scope:
        allowed_domains = None  # Allow subdomains

    queue = deque([(url, 0)])
    visited = set()

    limits = httpx.Limits(max_connections=threads, max_keepalive_connections=threads)

    async with httpx.AsyncClient(http2=True, verify=not insecure, proxy=proxy or None, timeout=timeout, limits=limits) as client:
        while queue:
            current_url, current_depth = queue.popleft()

            if current_depth > depth or current_url in visited:
                continue

            visited.add(current_url)

            content, status = await fetch(client, current_url, headers, timeout)

            if content and status == 200:
                links = extract_links(content, current_url, inside)
                for link, source, where in links:
                    # Filter domain scope
                    parsed_host = urllib.parse.urlparse(link).netloc

                    if allowed_domains and parsed_host not in allowed_domains and not subs_in_scope:
                        continue

                    if subs_in_scope and not re.search(rf'.*(\.|\/\/){re.escape(hostname)}((#|\/|\?).*)?', link):
                        continue

                    # Output formatting
                    if show_json:
                        result = json.dumps({"Source": source, "URL": link, "Where": where if show_where else ""})
                    elif show_source:
                        result = f"[{source}] {link}"
                    else:
                        result = link

                    if show_where and not show_json:
                        result = f"[{where}] {result}"

                    # Dedup and print
                    if result not in unique_urls:
                        unique_urls.add(result)
                        print(result)

                    # Queue next-level links
                    if current_depth + 1 <= depth:
                        queue.append((link, current_depth + 1))

def main():
    parser = argparse.ArgumentParser(description="HTTP/2 Web Crawler (using httpx)")
    parser.add_argument("-i", "--inside", action="store_true", help="Only crawl inside path.")
    parser.add_argument("-t", "--threads", type=int, default=8, help="Number of threads to utilize.")
    parser.add_argument("-d", "--depth", type=int, default=2, help="Depth to crawl.")
    parser.add_argument("-size", "--size", type=int, default=-1, help="Page size limit, in KB.")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS verification.")
    parser.add_argument("--subs", action="store_true", help="Include subdomains for crawling.")
    parser.add_argument("--json", action="store_true", help="Output as JSON.")
    parser.add_argument("-s", "--show-source", action="store_true", help="Show the source of URL.")
    parser.add_argument("-w", "--show-where", action="store_true", help="Show at which link URL is found.")
    parser.add_argument("-header", "--headers", default="", help="Custom headers separated by ';;'.")
    parser.add_argument("-u", "--unique", action="store_true", help="Show only unique URLs.")
    parser.add_argument("--proxy", default="", help="Proxy URL.")
    parser.add_argument("--timeout", type=int, default=-1, help="Max time per request in seconds.")
    parser.add_argument("--dr", "--disable-redirects", action="store_true", help="Disable following HTTP redirects.")

    args = parser.parse_args()
    headers = parse_headers(args.headers)
    proxy = args.proxy or None
    timeout = args.timeout if args.timeout > 0 else None

    if sys.stdin.isatty():
        logger.error("No URLs detected. Hint: cat urls.txt | python crawler.py")
        sys.exit(1)

    urls = [line.strip() for line in sys.stdin]

    async def run_crawlers():
        tasks = [
            crawl(
                url, headers, proxy, args.depth, args.inside, args.subs,
                args.show_source, args.show_where, args.json,
                timeout, args.threads, args.insecure
            )
            for url in urls
        ]
        await asyncio.gather(*tasks)

    asyncio.run(run_crawlers())

if __name__ == "__main__":
    print(banner)
    main()

