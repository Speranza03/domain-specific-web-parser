import json
from src.parser_manager import parse_url
from src.evaluation_service import evaluate_texts

GS_PATH = "../gs_data/www.mymovies.it_gs.json"
URL = "https://www.mymovies.it/film/2025/cinque-secondi/cast/"

def test_single_evaluation():
    """
    Esegue la valutazione del parser su un singolo URL.

    Carica il file Gold Standard, individua la entry corrispondente all'URL
    definito in 'URL', riesegue il parsing della pagina tramite 'parse_url'
    e confronta il testo prodotto con il gold_text tramite 'evaluate_texts'.
    Stampa il titolo della pagina e le metriche di valutazione risultanti.

    Raises:
        ValueError: Se l'URL non è presente nel file Gold Standard.
    """
    with open(GS_PATH, "r", encoding="utf-8") as f:
        gs_data = json.load(f)

    # Trova l'entry corrispondente all'URL
    gold_entry = next((item for item in gs_data if item["url"] == URL), None)
    
    if not gold_entry:
        raise ValueError(f"URL non trovato nel GS: {URL}")

    # Riesegue il parsing
    result = parse_url(URL)

    # Esegue la valutazione quantitativa tra il testo appena parsato e quello da te scritto a mano
    evaluation = evaluate_texts(result["parsed_text"], gold_entry["gold_text"])

    print(f"TITLE: {result['title']}")
    print(f"EVALUATION: {evaluation}")

if __name__ == "__main__":
    test_single_evaluation()
