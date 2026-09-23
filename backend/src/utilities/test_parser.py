from src.parser_manager import parse_url 

url = "https://www.mymovies.it/film/2025/cinque-secondi/cast/"
result = parse_url(url)
print(len(result['html_text']))
print(len(result['parsed_text']))
print(f"TITLE: {result['title']}")
print(f"DOMAIN: {result['domain']}")
print(f"HTML TEXT PREVIEW:\n{result['html_text'][:500]}")
print(f"\nPARSED TEXT PREVIEW:\n{result['parsed_text'][:10000]}")


