import re
from crawl4ai import CrawlerRunConfig, CacheMode
from .base_parser import BaseParser

class CurryFuneralHomeParser(BaseParser):
    """
    Parser per il dominio curryfuneralhome.org.

    Estende la classe BaseParser per gestire l'estrazione dei contenuti dai 
    necrologi, isolando la colonna principale del testo e rimuovendo le 
    informazioni di pubblicazione tipiche del sito.
    """
    
    def get_crawler_config(self) -> CrawlerRunConfig:
        """
        Configura i parametri del crawler per curryfuneralhome.

        Esegue l'override della configurazione base per puntare al selettore 
        CSS ".narrowcolumn", che contiene il corpo principale dell'articolo/necrologio.

        Returns:
            CrawlerRunConfig: Configurazione ottimizzata per il layout del sito.
        """
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            css_selector=".narrowcolumn"
        )

    def clean_text(self, text: str) -> str:
        """
        Pulizia del testo Markdown per curryfuneralhome.

        Oltre alla pulizia base, questo metodo utilizza espressioni regolari per 
        eliminare le date di pubblicazione, le firme dell'autore 
        e le sezioni di commento/risposta standard del blog.

        Args:
            text (str): Il testo Markdown grezzo estratto dalla pagina.

        Returns:
            str: Il testo pulito, privo di metadati di pubblicazione, sezioni di commento e link residui.
        """
        text = super().clean_text(text)
        
        if text:
            text = re.sub(r"[A-Z][a-z]+ \d+(?:st|nd|rd|th)?, \d{4}\s+\|\s+Posted by.*", "", text)
            text = re.sub(r"You can follow any responses to this entry.*", "", text, flags=re.DOTALL)
            text = re.sub(r"\[\]\(.*?\)", "", text)
            
        return text.strip()