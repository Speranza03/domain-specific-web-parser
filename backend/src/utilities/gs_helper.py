import json
import os
from parser_manager import parse_url

# Crea questa cartella se non esiste
GS_DIR = "../../../gs_data"
os.makedirs(GS_DIR, exist_ok=True)

def auto_generate_gs_entry(url: str):
    """
    Scarica e parsa un URL e aggiunge una entry al file Gold Standard del dominio.

    Esegue il parsing dell'URL tramite 'parse_url', costruisce una entry con
    i metadati estratti (url, domain, title, html_text) e lascia il campo
    "gold_text" vuoto per la compilazione manuale. La entry viene accodata
    al file JSON del dominio in 'GS_DIR'; se il file non esiste viene creato,
    se esiste viene preservato il contenuto precedente.

    Args:
        url (str): L'URL della pagina da scaricare e aggiungere al gold standard.
    """
    print(f"Sto scaricando e parsando l'URL: {url}...")
    result = parse_url(url)
    domain = result["domain"]
    
    gs_entry = {
        "url": result["url"],
        "domain": domain,
        "title": result["title"],
        "html_text": result["html_text"],
        "gold_text": ""
    }
    
    filename = os.path.join(GS_DIR, f"{domain}_gs.json")
    
    # Legge i dati vecchi se esistono
    gs_data = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                gs_data = json.load(f)
            except json.JSONDecodeError:
                pass
                
    gs_data.append(gs_entry)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(gs_data, f, indent=4, ensure_ascii=False)
        
    print(f"Aggiunto a {filename}. Vai a compilarne il campo 'gold_text' copiando il testo pulito dal browser!")

if __name__ == "__main__":
    #da inserire qui gli url che abbiamo scelto per i vari domini
    auto_generate_gs_entry("https://curryfuneralhome.org/?page_id=72")
