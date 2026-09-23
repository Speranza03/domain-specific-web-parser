def format_for_json(text):
    """
    Prepara una stringa di testo grezzo per essere incollata come valore nel gold_text del file JSON.

    Rimuove gli spazi iniziali e finali, rimpiazza le virgolette doppie con'\\"' e
    converte i ritorni a capo in sequenze '\\n', e '\$' con '$' rendendo il testo
    compatibile con il formato JSON.
    Usato come helper per la scrittura manuale del campo "gold_text" nei file del gold standard.

    Args:
        text (str): Il testo grezzo copiato dal browser.

    Returns:
        str: Il testo formattato, pronto per essere incollato come valore in un file JSON.
    """
    text = text.strip()
    text = text.replace('"', '\\"')
    text = text.replace('\n', '\\n')
    text = text.replace('\$', '$')
    
    return text

text = """
testo raccolto a mano dal sito per trasformarlo in json da mettere nei file json del gs_path
""" 

print(format_for_json(text))
