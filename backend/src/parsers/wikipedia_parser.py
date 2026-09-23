import re
from urllib.parse import urlparse
from crawl4ai import CrawlerRunConfig, CacheMode
from .base_parser import BaseParser

class WikipediaParser(BaseParser):
    """
    Parser per il dominio en.wikipedia.org

    Estende BaseParser per gestire l'estrazione mirata dei contenuti enciclopedici,
    isolando il corpo del testo principale ed escludendo elementi superflui come
    infobox, barre laterali, menu di navigazione e banner.
    """
    
    def get_crawler_config(self) -> CrawlerRunConfig:
        """
        Configura i parametri del crawler per Wikipedia.

        Esegue l'override del metodo base per selezionare il tag 'main' 
        ed escludere gli elementi dell'interfaccia utente 
        e le sezioni non pertinenti al contenuto dell'articolo.

        Returns:
            CrawlerRunConfig: Configurazione ottimizzata con selettori CSS e bypass della cache.
        """

        tags = "main"
        excluded = ".vector-page-toolbar, .vector-dropdown, .vector-column-end, .vector-body-before-content, .catlinks, .infobox, figure, .mw-editsection, .sidebar, .navigation-not-searchable, .noprint, .ambox"

        return CrawlerRunConfig(css_selector = tags, excluded_selector = excluded, cache_mode=CacheMode.BYPASS)
 
        
    def clean_text(self, text: str) -> str:
        """
        Pulizia del testo Markdown per Wikipedia.

        Oltre alla pulizia standard della classe base, questo metodo tronca
        il testo a partire dalle sezioni finali standard (See also, References,
        External links, ecc.), converte i link Markdown nel solo testo del
        link e rimuove i riferimenti numerici e letterali tipiche di Wikipedia
        (es. [1], [a]).

        Args:
            text (str): Il testo Markdown grezzo estratto dalla pagina.

        Returns:
            str: Testo pulito, privo di sezioni finali irrilevanti, link e riferimenti.
        """

        text = super().clean_text(text)

        #TRONCAMENTO SEZIONI FINALI
        text = re.split(r'\n#{1,5}\s+(?:See also|References|External links|Further reading|Notes|Bibliography|Sources|Citations|Publications)', text, maxsplit=1, flags=re.IGNORECASE)[0] 
        # Eliminazione URL
        text = re.sub(r'\[(.*?)\]\((?:[^)(]+|\([^)(]*\))*\)', r'\1', text)
        # Eliminazioni reference (es. [1])
        text = re.sub(r'\[\d+\]|\[[a-z]\]', '', text)

        return text.strip()