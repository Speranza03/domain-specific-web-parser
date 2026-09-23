import json
import os
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Minerva Web UI - Frontend")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def find_gs_dir():
    """
    Cerca la directory contenente i file Gold Standard.

    Prova una lista di path predefiniti per individuare la cartella 'gs_data',
    gestendo le differenze di ambiente tra sviluppo locale e container Docker.

    Returns:
        str: Il path assoluto alla directory trovata, 
        oppure una stringa vuota se nessun path esiste.
    """
    possible_paths = [
        os.path.abspath(os.path.join(BASE_DIR, "../gs_data")), 
        "/app/gs_data", 
        "/gs_data"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return ""

GS_DIR = find_gs_dir()
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8003") 

def load_gs_data():
    """
    Carica tutti i file Gold Standard disponibili in 'GS_DIR'.

    Legge ogni file JSON con suffisso '_gs.json' nella directory e costruisce
    un dizionario indicizzato per URL, dove ogni valore è la corrispondente
    entry del gold standard. Gli errori di lettura sui singoli file vengono
    loggati e ignorati senza interrompere il caricamento degli altri.

    Returns:
        dict: Dizionario '{url: entry}' con tutte le entry caricate.
              Restituisce un dizionario vuoto se 'GS_DIR' non esiste o è vuota.
    """
    gs_data = {}
    if not GS_DIR or not os.path.exists(GS_DIR):
        return gs_data
        
    for filename in os.listdir(GS_DIR):
        if filename.endswith("_gs.json"):
            filepath = os.path.join(GS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        gs_data[item.get("url")] = item
            except Exception as e:
                print(f"Errore nella lettura del GS {filename}: {e}")
    return gs_data

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Renderizza la pagina principale dell'interfaccia web.

    Carica la lista degli URL presenti nel gold standard e la passa al
    template 'web_ui.html' per popolare il menu di selezione.

    Args:
        request (Request): L'oggetto richiesta FastAPI.

    Returns:
        HTMLResponse: La pagina HTML renderizzata con la lista degli URL del gold standard.
    """
    gs_data = load_gs_data()
    gs_urls = list(gs_data.keys())
    return templates.TemplateResponse(
        request=request, 
        name="web_ui.html", 
        context={
            "request": request, 
            "gs_urls": gs_urls  
        }
    )

@app.post("/", response_class=HTMLResponse)
async def analyze_url( request: Request, url_input: str = Form(None), gs_url: str = Form(None) ):
    """
    Esegue il parsing e, se disponibile, la valutazione di un URL.

    Riceve l'URL dal form (inserito manualmente in 'url_input' oppure
    selezionato dal menu gold standard in 'gs_url'). Contatta il backend
    per eseguire il parsing tramite GET/parse;
    se l'URL è presente nel gold standard e il testo è stato estratto correttamente,
    richiede anche la valutazione tramite POST/evaluate.
    Restituisce tutti i risultati al template per la visualizzazione.

    Args:
        request (Request): L'oggetto richiesta FastAPI.
        url_input (str, optional): URL inserito manualmente dall'utente.
        gs_url (str, optional): URL selezionato dal menu del gold standard.

    Returns:
        HTMLResponse: La pagina HTML renderizzata con i risultati del parsing,
                      il testo gold standard (se disponibile) e le metriche
                      di valutazione (se calcolabili).
    """
    target_url = gs_url if gs_url else url_input
    
    gs_data = load_gs_data()
    gs_urls = list(gs_data.keys())
    
    if not target_url:
        return templates.TemplateResponse(
            request=request, 
            name="web_ui.html", 
            context={
                "request": request, 
                "gs_urls": gs_urls,
                "error": "Per favore inserisci o seleziona un URL."
            }
        )

    raw_html = ""
    cleaned_text = ""
    gs_text = ""
    metrics = {}
    has_gs = target_url in gs_data

    if has_gs:
        gs_text = gs_data[target_url].get("gold_text", "")

    async with httpx.AsyncClient() as client:
        # A) Parse
        try:
            parse_response = await client.get(f"{BACKEND_URL}/parse", params={"url": target_url}, timeout=60.0)
            if parse_response.status_code == 200:
                result = parse_response.json()
                raw_html = result.get("html_text", "")
                cleaned_text = result.get("parsed_text", "")
            else:
                raw_html = f"Errore dal backend (HTTP {parse_response.status_code}): {parse_response.text}"
        except Exception as e:
            raw_html = f"Errore di comunicazione col backend per il parse: {str(e)}"
            
        # B) Evaluate
        if has_gs and cleaned_text and gs_text:
            try:
                eval_response = await client.post(
                    f"{BACKEND_URL}/evaluate", 
                    json={"parsed_text": cleaned_text, "gold_text": gs_text},
                    timeout=30.0
                )
                if eval_response.status_code == 200:
                    data = eval_response.json()
                    metrics = data.get("token_level_eval", {}) 
            except Exception as e:
                metrics = {"Errore": f"Impossibile calcolare metriche: {str(e)}"}

    return templates.TemplateResponse(
        request=request,
        name="web_ui.html", 
        context={
            "request": request,
            "gs_urls": gs_urls,
            "url_analyzed": target_url,
            "raw_html": raw_html,
            "cleaned_text": cleaned_text,
            "has_gs": has_gs,
            "gs_text": gs_text,
            "metrics": metrics
        }
    )