# CRAWLER

An Async Web Crawler with HTTP/2 & Proxy Support.

## Features
- Extract and crawl links up to specified depth.
- HTTP/2 support via `httpx`.
- Proxy support (e.g., Burp Suite, ZAP, etc.).
- Subdomain inclusion.
- Custom headers support.
- JSON and categorized output formats.
- Simple CLI-based tool.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/jithender2/Crawler.git
cd crawler
```
1.Create Virtual Environment(Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Install the dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Feed URLs from a file:
```bash
cat urls.txt | python crawl.py --depth 2 --proxy http://127.0.0.1:8080 --subs
```

### Available Arguments:
| Flag | Description |
|------|-------------|
| `--depth` | Set the crawling depth (default is 2) |
| `--proxy` | Set proxy URL (e.g., http://127.0.0.1:8080) |
| `--subs` | Include subdomains in scope |
| `--headers` | Custom headers in `Key:Value;;Key2:Value2` format |
| `--json` | Output result in JSON |
| `--inside` | Limit crawling to same path only |
| `--show-source` | Show source tag of URL (e.g., href, script, form) |
| `--show-where` | Show where the link was found |

## License
MIT License

## Author
Mr.Ethical YT
