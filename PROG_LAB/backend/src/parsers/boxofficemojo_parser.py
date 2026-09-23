from crawl4ai import CrawlerRunConfig, CacheMode
from .base_parser import BaseParser
import re

class BoxOfficeMojoParser(BaseParser): 
    """
    Parser per il dominio www.boxofficemojo.com.

    Estende la classe BaseParser configurando selettori CSS specifici per 
    estrarre i dati cinematografici ed eliminare gli elementi dell'interfaccia 
    utente non necessari (dropdown, tabelle comparative, ecc.).
    """
    
    def get_crawler_config(self):
        """
        Configura i parametri del crawler per BoxOfficeMojo

        Esegue l'override del metodo base per definire i tag da includere 
        e una lista estesa di classi CSS da escludere, ottimizzando l'estrazione
        dei dati dai report del botteghino.

        Returns:
            CrawlerRunConfig: Configurazione mirata con selettori CSS e bypass cache.
        """

        tags = "main"
        excluded = ".hidden, .floating-cap-cell, .floating-header, .mojo-disabled-tab, .mojo-refinement-dropdown, .mojo-mobile-title-summary-pro-cta, .mojo-hidden-from-widescreen, .mojo-override-gutter, .mojo-heading-pro-cta, .mojo-title-release-refiner, .mojo-link-bar-internal, .mojo-imdbpro-table-view-cta, .mojo-pagination"

        return CrawlerRunConfig(css_selector = tags, excluded_selector = excluded, cache_mode=CacheMode.BYPASS)
    
    def clean_text(self, text):
        """
        Pulizia del testo Markdown per BoxOfficeMojo

        Oltre alla pulizia standard della classe base, questo metodo rimuove
        la formattazione Markdown: i link con testo vengono ridotti al solo
        testo del link, i link senza testo (loghi e immagini) vengono eliminati
        interamente, mentre grassetto e corsivo vengono spogliati dei loro
        delimitatori.

        Args:
            text (str): Il testo Markdown grezzo fornito dal crawler.

        Returns:
            str: Testo pulito, privo di formattazione Markdown e link.
        """
        
        text = super().clean_text(text)

        # Cancella i link e mantiene solo il testo
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Cancella i link vuoti associati a loghi e immagini
        text = re.sub(r'\[\]\([^)]*\)', '', text).strip()
        # Rimuove ** o __ per il grassetto
        text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
        # Rimuove * o _ per il corsivo
        text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
        
        return text