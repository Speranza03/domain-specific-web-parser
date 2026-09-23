import json
import os
import traceback
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List
from .parser_manager import parse_url, get_parser_for_url, parse_html_content
from .evaluation_service import token_level_eval

app = FastAPI(
    title="Minerva Esonero API",
    description="API REST"
)


SUPPORTED_DOMAINS = [
    "curryfuneralhome.org",
    "en.wikipedia.org",
    "www.mymovies.it",
    "www.boxofficemojo.com"
]

class EvaluateRequest(BaseModel):
    """
    Modello per il body della richiesta POST/evaluate.

    Attributes:
        parsed_text (str): Il testo prodotto dal parser da valutare.
        gold_text (str): Il testo di riferimento (gold standard).
    """
    parsed_text: str
    gold_text: str

class PostParseRequest(BaseModel):
    """
    Modello Pydantic per il body della richiesta POST/parse.

    Attributes:
        url (str): L'URL associato all'HTML, usato per selezionare il parser.
        html_text (str): Il contenuto HTML grezzo da analizzare.
    """
    url: str
    html_text: str

def find_gs_path(domain: str) -> str:
    """
    Cerca il file Gold Standard corrispondente a un dominio.

    Prova una lista di path relativi predefiniti per individuare il file
    JSON del gold standard, gestendo le differenze di working directory
    a seconda di come viene avviato il server.

    Args:
        domain (str): Il dominio per cui cercare il file del gold standard.

    Returns:
        str: Il path al file trovato, oppure None se nessun path esiste.
    """
    possible_paths = [
        f"gs_data/{domain}_gs.json",
        f"../gs_data/{domain}_gs.json",
        f"../../gs_data/{domain}_gs.json",
        f"{domain}_gs.json"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None


@app.get("/parse", summary="Esegue il parser per un documento di un dominio")
def parse(url: str = Query(..., description="L'URL del documento da parsare")):
    """
    Scarica il contenuto di un URL e applica il parser specifico per il dominio.

    Verifica che il dominio dell'URL sia tra quelli supportati, esegue il
    fetch e il parsing tramite 'parse_url' e restituisce il contenuto estratto. 
    Restituisce 400 se il dominio non è supportato, 404 se l'URL è irraggiungibile o il contenuto è vuoto.

    Args:
        url (str): L'URL della pagina da scaricare e analizzare.

    Returns:
        dict: Dizionario con le chiavi "url", "domain", "title", "html_text" e "parsed_text".

    Raises:
        HTTPException 400: Se il dominio non è supportato.
        HTTPException 404: Se l'URL è irraggiungibile o il contenuto è vuoto.
    """
    try:
        domain = urlparse(url).netloc
        
        # Gestione Errore: Dominio non supportato
        if not any(sup in domain for sup in SUPPORTED_DOMAINS):
            raise HTTPException(status_code=400, detail="Dominio non supportato")

        result = parse_url(url)
        
        # Gestione Errore: URL irraggiungibile / contenuto vuoto
        if not result or not result.get("html_text"):
            raise HTTPException(status_code=404, detail="URL irraggiungibile")
            
        return {
            "url": result.get("url", url),
            "domain": result.get("domain", domain),
            "title": result.get("title", ""),
            "html_text": result.get("html_text", ""),
            "parsed_text": result.get("parsed_text", "")
        }
        
    except HTTPException as he:
        raise he # Rilancia gli errori HTTP (400, 404)
    except Exception as e:
        # Se esplode qualcos'altro, riporta URL irraggiungibile
        print(f"Errore durante il parsing: {traceback.format_exc()}")
        raise HTTPException(status_code=404, detail="URL irraggiungibile")


@app.post("/parse", summary="Esegue il parser per un documento da html diretto")
def parse_post(request: PostParseRequest):
    """
    Applica il parser specifico per il dominio su un HTML già disponibile in memoria.

    Verifica che il dominio dell'URL sia tra quelli supportati, poi delega
    l'elaborazione a 'parse_html_content' senza eseguire alcun fetch di rete.
    Restituisce 400 se il dominio non è supportato, 500 in caso di errore
    nell'estrazione o di eccezione imprevista.

    Args:
        request (PostParseRequest): Body della richiesta contenente l'URL e l'HTML grezzo da analizzare.

    Returns:
        dict: Il risultato del parsing restituito dal parser selezionato.

    Raises:
        HTTPException 400: Se il dominio non è supportato.
        HTTPException 500: Se l'estrazione del testo fallisce o si verifica un errore imprevisto.
    """
    try:
        domain = urlparse(request.url).netloc
        
        # Gestione Errore: Dominio non supportato
        if not any(sup in domain for sup in SUPPORTED_DOMAINS):
            raise HTTPException(status_code=400, detail="Dominio non supportato")
            
        result = parse_html_content(request.url, request.html_text)
        
        # Gestione Errore di fail
        if not result or not result.get("parsed_text"):
            raise HTTPException(status_code=500, detail="Errore nell'estrazione dal testo HTML")
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/domains", summary="Restituisce la lista dei domini assegnati")
def get_domains() -> Dict[str, List[str]]:
    """
    Restituisce la lista di tutti i domini supportati dall'API.

    Returns:
        dict: Dizionario con la chiave "domains" contenente la lista dei domini supportati.
    """
    return {"domains":SUPPORTED_DOMAINS}


@app.get("/gold_standard", summary="Restituisce il gold standard per un documento")
def get_gold_standard(url: str = Query(...)):
    """
    Recupera la entry del Gold Standard corrispondente a un URL specifico.

    Cerca il file JSON del gold standard per il dominio dell'URL tramite
    'find_gs_path' e restituisce la prima entry il cui campo "url" coincide
    con quello richiesto. Restituisce 400 se il dominio non è supportato,
    404 se il file o l'URL non vengono trovati.

    Args:
        url (str): L'URL di cui recuperare il gold standard.

    Returns:
        dict: Dizionario con le chiavi "url", "domain", "title", "html_text" e "gold_text".

    Raises:
        HTTPException 400: Se il dominio non è supportato.
        HTTPException 404: Se il file Gold Standard o l'URL non vengono trovati.
        HTTPException 500: Per qualsiasi altro errore imprevisto.
    """
    try:
        domain = urlparse(url).netloc

        if domain not in SUPPORTED_DOMAINS:
            raise HTTPException(status_code=400, detail="Dominio non supportato")
    
        gs_path = find_gs_path(domain)
        
        if not gs_path:
            raise HTTPException(status_code=404, detail=f"File Gold Standard non trovato per il dominio: {domain}")
            
        with open(gs_path, "r", encoding="utf-8") as f:
            gs_data = json.load(f)
            
        for entry in gs_data:
            if entry.get("url") == url:
                return {
                    "url": entry["url"],
                    "domain": entry.get("domain",""),
                    "title": entry.get("title",""),
                    "html_text": entry.get("html_text",""),
                    "gold_text": entry.get("gold_text", "")
                }
                
        raise HTTPException(status_code=404, detail="URL non trovato all'interno del Gold Standard.")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@app.get("/full_gold_standard", summary="Restituisce tutto il GS del dominio")
def get_full_gold_standard(domain: str = Query(...)):
    """
    Recupera tutte le entry del Gold Standard per un dominio dal file JSON.

    Carica il file JSON del gold standard tramite 'find_gs_path'
    e restituisce l'intero contenuto come lista.
    Restituisce 400 se il dominio non è supportato, 404 se il file non viene trovato.

    Args:
        domain (str): Il dominio di cui recuperare il gold standard completo.

    Returns:
        dict: Dizionario con la chiave "gold_standard" contenente la lista di tutte le entry,
              ciascuna con le chiavi "url", "domain", "title", "html_text" e "gold_text".

    Raises:
        HTTPException 400: Se il dominio non è supportato.
        HTTPException 404: Se il file Gold Standard non viene trovato.
        HTTPException 500: Per qualsiasi altro errore imprevisto.
    """
    try:
        if domain not in SUPPORTED_DOMAINS:
            raise HTTPException(status_code=400, detail="Dominio non supportato")
    
        gs_path = find_gs_path(domain)
        
        if not gs_path:
            raise HTTPException(status_code=404, detail=f"File Gold Standard non trovato per il dominio: {domain}")
            
        with open(gs_path, "r", encoding="utf-8") as f:
            gs_data = json.load(f)
            
        result_list = []
        for entry in gs_data:
            result_list.append({
                "url": entry["url"],
                "domain": entry.get("domain",""),
                "title": entry.get("title",""),
                "html_text": entry.get("html_text",""),
                "gold_text": entry.get("gold_text", "")
            })
        return {"gold_standard": result_list}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@app.post("/evaluate", summary="Restituisce le metriche di evaluation")
def evaluate(request: EvaluateRequest):
    """
    Calcola le metriche di valutazione tra parsed_text e gold_text.

    Delega il calcolo a 'token_level_eval' e restituisce precision, recall
    e F1-Score a livello di token. Il campo "x_eval" è riservato a metriche
    aggiuntive future ed è attualmente vuoto.

    Args:
        request (EvaluateRequest): Body della richiesta contenente "parsed_text" e "gold_text".

    Returns:
        dict: Dizionario con le chiavi "token_level_eval" (precision, recall, f1) 
        e "x_eval" (attualmente vuoto).

    Raises:
        HTTPException 500: Se si verifica un errore durante il calcolo delle metriche.
    """
    try:
        metrics = token_level_eval(request.parsed_text, request.gold_text)
        
        return {
            "token_level_eval": metrics,
            "x_eval": {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'evaluation: {str(e)}")


@app.get("/full_gs_eval")
def get_full_gs_eval(domain: str = Query(..., description="Il dominio su cui eseguire l'evaluation completa")):
    """
    Esegue l'evaluation su tutti gli URL contenuti nel file Json dominio.

    Per ciascuna entry del gold standard, scarica e parsa la pagina tramite
    'parse_url' e calcola le metriche con 'token_level_eval'. 
    Le metriche vengono mediate su tutti gli URL del dominio. 
    In caso di errore sul singolo URL, il parsed_text viene impostato a stringa vuota,
    penalizzando le metriche finali.

    Args:
        domain (str): Il dominio su cui eseguire l'evaluation completa.

    Returns:
        dict: Dizionario con le chiavi "token_level_eval" (precision, recall e f1)
        e "x_eval" (attualmente vuoto).

    Raises:
        HTTPException 400: Se il dominio non è supportato o il gold standard è vuoto.
        HTTPException 404: Se il file Gold Standard non viene trovato.
    """
    if domain not in SUPPORTED_DOMAINS:
        raise HTTPException(status_code=400, detail="Dominio non supportato")

    gs_path = find_gs_path(domain)
    if not gs_path:
        raise HTTPException(status_code=404, detail="File Gold Standard non trovato per il dominio richiesto")

    with open(gs_path, "r", encoding="utf-8") as f:
        gs_data = json.load(f)

    if not gs_data:
        raise HTTPException(status_code=400, detail="Il Gold Standard è vuoto.")

    total_precision = 0.0
    total_recall = 0.0
    total_f1 = 0.0
    count = len(gs_data)
    
    for entry in gs_data:
        url = entry["url"]
        gold_text = entry.get("gold_text", "")
        html_text = entry.get("html_text", "")

        try:
            if domain == "www.mymovies.it" and html_text:
                parse_result = parse_html_content(url, html_text)
            else:
                parse_result = parse_url(url)

            parsed_text = parse_result.get("parsed_text", "")
        except Exception:
            parsed_text = ""

        metrics = token_level_eval(parsed_text, gold_text)
        total_precision += metrics.get("precision", 0.0)
        total_recall += metrics.get("recall", 0.0)
        total_f1 += metrics.get("f1", 0.0)
        
    return {
        "token_level_eval": {
            "precision": round(total_precision / count, 4),
            "recall": round(total_recall / count, 4),
            "f1": round(total_f1 / count, 4)
        },
        "x_eval": {} 
    }



