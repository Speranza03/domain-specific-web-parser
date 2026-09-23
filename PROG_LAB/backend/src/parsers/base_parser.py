import re
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

class BaseParser:
    """
    Classe base per la gestione del parsing dei contenuti web.
    
    Fornisce le funzionalità comuni per la configurazione del browser, 
    la pulizia del testo e la logica di estrazione principale utilizzando crawl4ai.
    """

    def __init__(self):
        """
        Inizializza il parser configurando il browser.

        Configura un'istanza di BrowserConfig in modalità headless per l'esecuzione in background senza interfaccia grafica.
        """
        self.browser_cfg = BrowserConfig(headless=True)
        
    def get_crawler_config(self) -> CrawlerRunConfig:
        """
        Configurazione di default per il crawler.
        
        Questa configurazione imposta il CacheMode a BYPASS per garantire che
        i dati vengano scaricati freschi dalla rete invece di usare versioni archiviate.

        Returns:
            CrawlerRunConfig: Oggetto di configurazione con bypass della cache attivo.      
        """
        return CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        
    def clean_title(self, title: str) -> str:
        """
        Metodo base per pulire il titolo.

        Args:
            title (str): Il titolo grezzo da pulire.

        Returns:
            str: Il titolo senza spazi bianchi superflui agli estremi.
        """
        return title.strip()
        
    def clean_text(self, text: str) -> str:
        """
        Pulizia di base del testo Markdown.

        Rimuove i riferimenti alle immagini, pulisce gli spazi e normalizza 
        le righe vuote eccessive.

        Args:
            text (str): Il testo Markdown grezzo da elaborare.

        Returns:
            str: Il testo pulito e normalizzato.
        """
        if not text:
            return ""
        # regex per le immagini in formato Markdown: ![](url)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        # regex per le eccessive righe vuote
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
        
    async def parse(self, url: str) -> dict:
        """
        Logica principale di estrazione e processamento di un URL.

        Scarica il contenuto della pagina, estrae i metadati
        e processa il corpo del testo in base al tipo di pagina rilevato.

        Args:
            url (str): L'URL della pagina web da analizzare.

        Returns:
            dict: Un dizionario contenente 'url', 'domain', 'title', 'html_text' e 'parsed_text'.

        Raises:
            RuntimeError: Se il crawler non riesce a scaricare o processare correttamente l'URL.
        """
        domain = urlparse(url).netloc
        
        specific_cfg = self.get_crawler_config()
        full_html_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        
        async with AsyncWebCrawler(config=self.browser_cfg) as crawler:
            full_result = await crawler.arun(url=url, config=full_html_cfg)
            parsed_result = await crawler.arun(url=url, config=specific_cfg)
        
        if not parsed_result.success:
            raise RuntimeError(f"Parsing fallito per {url}: {parsed_result.error_message}")

        title = ""
        
        if hasattr(full_result, "metadata") and full_result.metadata:
            title = full_result.metadata.get("title", "") or ""
            
        if not title and hasattr(full_result, "html") and full_result.html:
            match = re.search(r'<title[^>]*>(.*?)</title>', full_result.html, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                
        if not title:
            last_segment = urlparse(url).path.split('/')[-1]
            title = last_segment.replace('_', ' ').replace('.html', '').replace('.php', '')

        title = self.clean_title(title)
        
        full_html_text = full_result.html if hasattr(full_result, "html") and full_result.html else ""
        
        raw_markdown = parsed_result.markdown if hasattr(parsed_result, "markdown") and parsed_result.markdown else ""
        
        parsed_html = parsed_result.html if hasattr(parsed_result, "html") and parsed_result.html else ""

        raw_source = parsed_html if getattr(self, "_page_type", "") == "news_detail" else (
            full_html_text if getattr(self, "_page_type", "") in {"series_year","film_public", "film_cast"} else raw_markdown
        )
        parsed_text = self.clean_text(raw_source)
        
        return {
            "url": url,
            "domain": domain,
            "title": title,
            "html_text": full_html_text,
            "parsed_text": parsed_text
        }
    
    async def parse_html(self, url: str, html_text: str) -> dict:
        """
        Versione alternativa del parser che processa direttamente codice HTML grezzo.

        Utile quando il contenuto HTML è già disponibile e si vuole evitare 
        una nuova richiesta di download, mantenendo però la logica di estrazione.
        Oppure qunado si vuole effettuare il parsing di una pagina 
        che nel tempo è stata aggiornata e della quale quindi si ha il gold standard 'vecchio'.

        Args:
            url (str): L'URL di origine.
            html_text (str): Il codice HTML grezzo da processare.

        Returns:
            dict: Un dizionario con i dati estratti 'url', 'domain', 'title', 'html', 'parsed_text'.        """
        domain = urlparse(url).netloc
        specific_cfg = self.get_crawler_config()
        
        title = ""
        match = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
        if not title:
            last_segment = urlparse(url).path.split('/')[-1]
            title = last_segment.replace('_', ' ').replace('.html', '').replace('.php', '')
        title = self.clean_title(title)
        
        async with AsyncWebCrawler(config=self.browser_cfg) as crawler:
            parsed_result = await crawler.arun(
                url=f"raw:{html_text}", 
                config=specific_cfg
            )
            
            raw_markdown = getattr(parsed_result, "markdown", "") or ""
            parsed_html = getattr(parsed_result, "html", "") or ""

            raw_source = parsed_html if getattr(self, "_page_type", "") == "news_detail" else (
                html_text if getattr(self, "_page_type", "") in {"series_year","film_public", "film_cast"} else raw_markdown
            )
            
            parsed_text = self.clean_text(raw_source)
            
            return {
                "url": url,
                "domain": domain,
                "title": title,
                "html_text": html_text,
                "parsed_text": parsed_text
            }