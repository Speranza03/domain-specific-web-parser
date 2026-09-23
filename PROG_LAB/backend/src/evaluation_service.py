import re

def normalize_text(text: str) -> str:
    """
    Normalizza il testo per il confronto.

    Converte il testo in minuscolo, rimuove i marcatori Markdown, 
    sostituisce la punteggiatura residua con spazi e 
    comprime i whitespace multipli in uno singolo.

    Args:
        text (str): Il testo grezzo da normalizzare.

    Returns:
        str: Il testo normalizzato, 
        pronto per la tokenizzazione o il confronto diretto. 
        Restituisce una stringa vuota se l'input è None o vuoto.
    """
    if not text:
        return ""
    
    text = text.lower()
    text = re.sub(r"[#*_'\[\]()]", " ", text) 
    text = re.sub(r"[^\w\s]", " ", text)  
    text = re.sub(r"\s+", " ", text) 
    return text.strip()

def tokenize(text: str) -> list[str]:
    """
    Tokenizza il testo dopo averlo normalizzato.

    Applica 'normalize_text' e suddivide il risultato in una lista di token
    separati da spazio.

    Args:
        text (str): Il testo da tokenizzare.

    Returns:
        list[str]: La lista dei token estratti. 
        Restituisce una lista vuotase il testo normalizzato è vuoto.
    """
    normalized = normalize_text(text)
    return normalized.split() if normalized else []

def token_level_eval(parsed_text: str, gold_text: str) -> dict:
    """
    Calcola Precision, Recall e F1-Score a livello di token.

    Confronta i due testi come insiemi di token unici. 
    La precision misura quanti token del testo prodotto sono presenti nel gold standard; 
    la recall misura quanti token del gold standard sono stati recuperati; 
    l'F1 è la media armonica delle due metriche.

    Args:
        parsed_text (str): Il testo prodotto dal parser da valutare.
        gold_text (str): Il testo di riferimento (gold standard).

    Returns:
        dict: Dizionario con le chiavi "precision", "recall" e "f1",
              ciascuna arrotondata a quattro cifre decimali.
    """
    parsed_tokens = set(tokenize(parsed_text))
    gold_tokens = set(tokenize(gold_text))
    
    # L'intersezione tra i set trova i token presenti in entrambi i testi
    intersection = parsed_tokens & gold_tokens 
    
    # numero di elementi
    overlap_count = len(intersection)
    parsed_count = len(parsed_tokens)
    gold_count = len(gold_tokens)
    
    # Calcolo metriche
    precision = overlap_count / parsed_count if parsed_count > 0 else 0.0
    recall = overlap_count / gold_count if gold_count > 0 else 0.0
    
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
        
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }

def evaluate_texts(parsed_text: str, gold_text: str) -> dict:
    """
    Funzione wrapper per eseguire la valutazione tra parsed_text e gold_text.

    Args:
        parsed_text (str): Il testo prodotto dal parser da valutare.
        gold_text (str): Il testo di riferimento (gold standard).

    Returns:
        dict: Dizionario con la chiave "token_level_eval" contenente le metriche di precision, recall e F1.
    """
    return {
        "token_level_eval": token_level_eval(parsed_text, gold_text)
    }