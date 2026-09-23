import re
from urllib.parse import urlparse
from crawl4ai import CrawlerRunConfig, CacheMode
from .base_parser import BaseParser
from bs4 import BeautifulSoup

class MyMoviesParser(BaseParser):
    """
    Parser per il dominio www.mymovies.it

    Estende la classe BaseParser per gestire l'estrazione di contenuti da
    pagine eterogenee del sito, tra cui schede film, biografie, serie TV,
    news, cast e recensioni del pubblico. Il tipo di pagina viene rilevato
    automaticamente dall'URL e indirizza il testo al metodo di pulizia dedicato.
    """

    FILM_DETAIL_RE = re.compile(r"^/film/\d{4}/[^/]+$")
    PERSON_DETAIL_RE = re.compile(r"^/persone/[^/]+/\d+$")
    YEAR_LIST_RE = re.compile(r"^/(?:film|serietv)/\d{4}$")
    NEWS_DETAIL_RE = re.compile(r"^/cinemanews/\d{4}/\d+$")
    FILM_CAST_RE = re.compile(r"^/film/\d{4}/[^/]+/cast$")
    FILM_PUBLIC_RE = re.compile(r"^/film/\d{4}/[^/]+/pubblico$")
    BASE_GLYPHS_RE = r"[]+"
    TABLE_LINE_RE = r"^\|\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?$"
    UI_MARKER_RE = r"\b(Condividi|VOTA|SCRIVI|PREFERITI|Recaptcha token|Accedi o registrati)\b"
    FORM_MARKER_RE = (
        r"(Inserisci qui la tua email|La tua preferenza .*registrata|Ti abbiamo .* email|"
        r"Convalida|Attenzione\. L'invio non è andato a buon fine|Chiudi|Riceverai un avviso)"
    )

    FILM_NAV = {
        "Scheda Home", "Scheda", "Cast", "News", "Critica", "Pubblico", "Premi",
        "Cinema", "Trailer", "Poster", "Foto", "Frasi", "Frasi Celebri", "Streaming",
        "PUBBLICO", "NEWS", "STAMPA", "PREMI", "MULTIMEDIA", "SHOWTIME"
    }

    PERSON_NAV = {
        "Scheda", "Biografia", "Filmografia", "Serie TV", "Articoli", "News",
        "Foto", "Video", "Premi", "Commenti", "Frasi", "Cinema", "Streaming"
    }

    SERIES_NAV = {
    "Home", "Serie TV", "News", "Recensioni", "Poster", "Foto", "Video",
    "Streaming", "Premi", "Cast", "Scheda", "Trama"
    }

    FILM_STOP_MARKERS = [
        r"Sei d'accordo con[\s\S]{0,100}?Tutti i film da\s*€?\s*1\s*al mese",
        r"(?m)^RECENSIONI DALLA PARTE DEL PUBBLICO$",
        r"(?m)^RECENSIONI DELLA CRITICA$",
        r"(?m)^Frasi$",
        r"(?m)^STAMPA$",
        r"(?m)^PUBBLICO$",
        r"(?m)^NEWS$",
        r"(?m)^PREMI$",
        r"(?m)^MULTIMEDIA$",
        r"(?m)^SHOWTIME$",
        r"(?m)^Quanto ti piace MYmovies\.it$",
        r"(?m)^Home \| Cinema \| Database \| Film",
        r"(?m)^Copyright©",
    ]

    PERSON_STOP_MARKERS = [
        r"Ultimi film",
        r"Prossimi film",
        r"Focus",
        r"News",
        r"I film più famosi",
    ]

    SERIES_STOP_MARKERS = [
    r"\* Film\b",
    r"\* Serie TV\b",
    r"\* Generi\b",
    r"\* Cinema\b",
    r"\* Film in\b",
    r"\* Questa settimana al cinema\b",
    r"\* Dalla scorsa settimana",
    r"\* Attesissimi\b",
    r"\* Appena aggiunti\b",
    r"\* Prossimamente\b",
    r"\* Box Office\b",
    r"\* Stasera in Tv\b",
    r"\* Ultime news\b",
    r"\* Argomenti\b",
    r"Home \| Cinema \| Database \| Film",
    r"Copyright©",
    r"chevron_left"
]   
    
    NEWS_STOP_MARKERS = [
    r"Tutti i film da\s*€?\s*1\s*al mese",
]
    
    FILM_CAST_STOP_MARKERS = [
    r"\n[^\n]*\|\s*Indice",
]
    
    FILM_PUBLIC_STOP_MARKERS = [
    r"pagina:\s*(?:\d+\s*)+»?"
]
    
    def get_crawler_config(self) -> CrawlerRunConfig:
        """
        Configura i parametri del crawler per MyMovies

        Esegue l'override della configurazione base escludendo i tag HTML
        strutturalmente rumorosi (tabelle, form, iframe, ecc.) e una serie
        di selettori CSS specifici del sito legati a widget, banner e
        elementi di navigazione secondaria.

        Returns:
            CrawlerRunConfig: Configurazione ottimizzata per il layout di MyMovies.
        """

        return CrawlerRunConfig(
            excluded_tags=["table", "svg", "form", "button", "input", "textarea", "iframe", "noscript","select" ],
            cache_mode=CacheMode.BYPASS,
            excluded_selector="div.mm-hide-xs, .pulsante-span-bgfree, .mm-wide-lista-colonne, .mm-white.mm-padding-ver-16.mm-padding-hor-8.stonda6.mm-center, .mm-padding-8.mm-col.md-4.sm-12, .col-mm.xs-12.mm-white.mm-padding-8, .mm-white.mm-hover-pink.stonda3, .mm-white.stonda6.mm-btn.mm-btn-head.mm-aqua, .btn-group, .dropdown-menu ,.io-article-footer, .mm-col.xs-12.mm-white.mm-left.mm-padding-12"
        )


    async def parse(self, url: str) -> dict:
        """
        Entry point principlale per il parsing di un url.

        Rileva il tipo di pagina tramite `detect_page_type` e lo memorizza
        in `_page_type` prima di delegare l'esecuzione alla classe base.

        Args:
            url (str): L'URL della pagina da analizzare.

        Returns:
            dict: Il risultato del parsing restituito dalla classe base.
        """
        self._page_type = self.detect_page_type(url)
        return await super().parse(url)


    async def parse_html(self, url: str, html_text: str) -> dict:
        """
        Esegue il parsing direttamente da una stringa HTML fornita.

        Rileva il tipo di pagina dall'URL e lo memorizza in `_page_type`
        prima di delegare l'elaborazione alla classe base.

        Args:
            url (str): L'URL associato all'HTML, usato per il rilevamento del tipo di pagina.
            html_text (str): Il contenuto HTML grezzo da analizzare.

        Returns:
            dict: Il risultato del parsing restituito dalla classe base.
        """
        self._page_type = self.detect_page_type(url) # Calcola il tipo di pagina
        return await super().parse_html(url, html_text)
    

    def detect_page_type(self, url: str) -> str:
        """
        Determina il tipo di pagina a partire dall'URL.

        Confronta il path dell'URL con le espressioni regolari definite come
        attributi di classe per classificare la pagina in una delle categorie
        note. 
        Restituisce "generic" se nessun pattern corrisponde.

        Args:
            url (str): L'URL della pagina da classificare.

        Returns:
            str: Il tipo di pagina rilevato. Valori possibili: "film_detail",
                 "person_detail", "series_year", "film_cast", "news_detail",
                 "film_public", "generic".
        """
        path = urlparse(url).path.lower().rstrip("/")
        if self.FILM_DETAIL_RE.match(path):
            return "film_detail"
        if self.PERSON_DETAIL_RE.match(path):
            return "person_detail"
        if self.YEAR_LIST_RE.match(path):
            return "series_year"
        if self.FILM_CAST_RE.match(path):
            return "film_cast"
        if self.NEWS_DETAIL_RE.match(path):
            return "news_detail"
        if self.FILM_PUBLIC_RE.match(path):
            return "film_public"
        return "generic"


    def clean_text(self, text: str) -> str:
        """
        Metodo che gestisce i vari metodi per la pulizia del testo.
        
        Legge il tipo di pagina memorizzato in `_page_type` e instrada il testo
        al metodo di pulizia specializzato corrispondente.
        Se il tipo non è
        riconosciuto o non è stato impostato, applica la pulizia generica.

        Args:
            text (str): Il testo grezzo da pulire.

        Returns:
            str: Il testo pulito, elaborato dal metodo appropriato al tipo di pagina.   
        """
        page_type = getattr(self, "_page_type", "generic")
        if page_type == "film_detail":
            return self.clean_film_text(text)
        if page_type == "person_detail":
            return self.clean_person_text(text)
        if page_type == "series_year":
            return self.clean_series_text(text)
        if page_type == "news_detail":
            return self.clean_news_text(text)
        if page_type == "film_cast":
            return self.clean_film_cast_text(text)
        if page_type == "film_public":
            return self.clean_film_public_text(text)
        return self.clean_generic_text(text)


    def _normalize_base(self, text: str) -> str:
        """
        Esegue la normalizzazione del testo, comune a tutti i tipi di pagina.

        Standardizza i fine riga, rimuove immagini e link Markdown convertendoli
        in solo testo, elimina i template `{{...}}`, i glifi decorativi e gli
        spazi orizzontali multipli. Tronca infine il testo a partire dal primo
        titolo di primo livello (`# Titolo`), scartando tutto ciò che precede.

        Args:
            text (str): Il testo grezzo da normalizzare.

        Returns:
            str: Il testo normalizzato, pronto per le fasi di pulizia successive.
        """
        text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"\[([^\]]*)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"\{\{[^}]+\}\}", "", text)
        text = re.sub(self.BASE_GLYPHS_RE, "", text)
        text = re.sub(r"[ \t\f\v]+", " ", text)
        m = re.search(r"(?m)^#\s+.+$", text)
        return text[m.start():] if m else text


    def _filter_lines(self, text: str, nav: set[str], meta_max_len: int) -> str:
        """
        Rimuove le righe indesiderate dal testo.

        Rimuove riga per riga: righe di tabella Markdown, voci di navigazione
        presenti nel set `nav`, elementi di interfaccia (pulsanti, form),
        sequenze puramente numeriche o simboliche. Rimuove inoltre la prima
        riga di metadati inline (es. regista | anno | durata) che segue
        immediatamente il titolo `# ...`, se la sua lunghezza non supera
        `meta_max_len` caratteri.

        Args:
            text (str): Il testo da filtrare.
            nav (set[str]): Insieme delle voci di navigazione da eliminare.
            meta_max_len (int): Lunghezza massima oltre la quale la riga di metadati dopo il titolo non viene rimossa.

        Returns:
            str: Il testo con le righe indesiderate eliminate.
        """
        out, title_seen, removed_meta = [], False, False

        for line in text.split("\n"):
            s = line.strip()

            if (s.startswith("|") and s.endswith("|")) or re.match(self.TABLE_LINE_RE, s):
                continue
            if s in nav:
                continue
            if re.search(self.UI_MARKER_RE, s, re.I):
                continue
            if re.search(self.FORM_MARKER_RE, s, re.I):
                continue
            if re.fullmatch(r"\d{1,4}", s) or re.fullmatch(r"[\|\s_]+", s):
                continue
            if re.fullmatch(r"[]+", s):
                continue
            if s.startswith("# "):
                title_seen = True
                out.append(line)
                continue

            if title_seen and not removed_meta:
                removed_meta = True
                if "|" in s and len(s) <= meta_max_len:
                    continue

            out.append(line)

        return "\n".join(out)


    def _apply_stop_markers(self, text: str, stop_markers: list[str], flags: int) -> str:
        """
        Tronca il testo alla prima occorrenza di uno stop marker.

        Cerca nel testo tutti i pattern presenti in `stop_markers` e ritaglia
        il testo fino alla posizione del match più vicino all'inizio, scartando
        tutto ciò che segue.

        Args:
            text (str): Il testo da troncare.
            stop_markers (list[str]): Lista di pattern regex che definiscono i punti di taglio.
            flags (int): Flag regex opzionali (es. re.I, re.S). Default: 0.

        Returns:
            str: Il testo troncato, o il testo originale se nessun marker viene trovato.        
        """
        cuts = [m.start() for p in stop_markers if (m := re.search(p, text, flags))]
        return text[:min(cuts)] if cuts else text


    def _strip_markdown_emphasis(self, text: str) -> str:
        """
        Rimuove grassetti e corsivi in formato Markdown.

        Gestisce le varianti con asterischi (`**`, `*`) e underscore (`__`, `_`),
        preservando il testo interno. Rimuove inoltre eventuali delimitatori
        'orfani' rimasti dopo le sostituzioni.

        Args:
            text (str): Il testo contenente formattazione Markdown.

        Returns:
            str: Il testo privo di marcatori di grassetto e corsivo.
        """
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"__(.*?)__", r"\1", text)
        text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
        return re.sub(r"(?<!\w)(?:__|\*\*)(?!\w)", "", text)


    def _final_cleanup(self, text: str) -> str:
        """
        Pulizia finale degli spazi bianchi e della punteggiatura residua.

        Rimuove le righe composte esclusivamente da spazi, trattini o simboli
        di separazione, normalizza gli spazi multipli, elimina gli spazi prima
        della punteggiatura e comprime le sequenze di righe vuote a un massimo
        di una riga vuota.

        Args:
            text (str): Il testo da rifinire.

        Returns:
            str: Il testo pulito e pronto per l'uso.
        """
        text = re.sub(r"(?m)^[\s\-\|_.,:;!]+$", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)
        return text.strip() 


    def clean_film_text(self, text: str) -> str:
        """
        Pulizia specifica per le schede film.

        Applica la normalizzazione base, filtra le voci di navigazione
        di `FILM_NAV` e rimuove elementi residui come la label "Da vedere YYYY",
        il link "Cast completo", le varianti errate di "MYmonetro" e le righe
        di aggiornamento. Tronca il testo agli stop marker di `FILM_STOP_MARKERS`.

        Args:
            text (str): Il testo Markdown grezzo della scheda film.

        Returns:
            str: Il testo pulito con i soli contenuti informativi della scheda.
        """
        text = self._normalize_base(text)
        text = self._filter_lines(text, self.FILM_NAV, meta_max_len=80)

        text = re.sub(r"\bDa vedere\s+\d{4}\b", "", text, flags=re.I)
        text = re.sub(r"\bCast completo\b", "", text, flags=re.I)
        text = re.sub(r"\bMYmo\s+netro\b", "MYmonetro", text, flags=re.I)
        text = re.sub(r"(?im)^Ultimo aggiornamento .+\n?", "", text)

        text = self._apply_stop_markers(text, self.FILM_STOP_MARKERS, re.I | re.S)
        text = self._strip_markdown_emphasis(text)
        return self._final_cleanup(text)


    def clean_person_text(self, text: str) -> str:
        """
        Pulizia specifica per le pagine di biografia.

        Applica la normalizzazione base, filtra le voci di navigazione di
        `PERSON_NAV` e tronca il testo agli stop marker di `PERSON_STOP_MARKERS`,
        che corrispondono alle sezioni di filmografia e approfondimento
        non pertinenti alla biografia.

        Args:
            text (str): Il testo Markdown grezzo della pagina biografica.

        Returns:
            str: Il testo pulito con i soli contenuti biografici.
        """
        text = self._normalize_base(text)
        text = self._filter_lines(text, self.PERSON_NAV, meta_max_len=100)

        text = self._apply_stop_markers(text, self.PERSON_STOP_MARKERS, re.I | re.M)
        text = self._strip_markdown_emphasis(text)
        return self._final_cleanup(text)

    
    def clean_series_text(self, text: str) -> str:
        """
        Pulizia specifica per le pagine di serie tv.
        
        Opera direttamente sull'HTML tramite BeautifulSoup: rimuove tag inutili, 
        decompone i selettori CSS rumorosi e sblocca i blocchi trama nascosti prima di estrarre il testo. 
        Sul testo risultante applica la normalizzazione base, regex per rimuovere etichette
        UI residue (ordinamento, filtri, badge JustWatch) e tronca agli stop
        marker di `SERIES_STOP_MARKERS`.

        Args:
            text (str): L'HTML grezzo della pagina di elenco serie TV.

        Returns:
            str: Il testo pulito con i titoli e le trame delle serie
        """
        soup = BeautifulSoup(text, "html.parser")

        # elimina tag interi sempre inutili
        for tag in soup(["script", "style", "svg", "noscript", "iframe", "form", "button", "input", "textarea"]):
            tag.decompose()
        for h1 in soup.find_all("h1"):
            h1.string = "# " + h1.get_text(strip=True)
        # elimina blocchi rumorosi per selector
        selectors = [
            "div.mm-hide-xs",
            ".pulsante-span-bgfree",
            ".mm-wide-lista-colonne",
            ".mm-white.mm-padding-ver-16.mm-padding-hor-8.stonda6.mm-center",
            ".mm-padding-8.mm-col.md-4.sm-12",
            ".col-mm.xs-12.mm-white.mm-padding-8",
            ".mm-white.mm-hover-pink.stonda3",
            ".mm-white.stonda6.mm-btn.mm-btn-head.mm-aqua",
            ".mm-padding-8.mm-col.md-12",
            ".mm-col.xs-12.mm-white.mm-left.mm-padding-12",
            ".mm-padding-8.mm-col.md-4.sm-6",
            ".stonda6.mm-btn.mm-btn-head.mm-aqua",
            ".menu-link-rapidi",
            ".accordion",
            ".mm-padding-4.mm-pointer.mm-pink.stonda3",
            ".mm-red.mm-padding-4.stonda6.mm-small",
            ".mm-show-sm.mm-show-md.link-bianco",
            ".mmo-slider",
            ".search-container",
        ]
        for sel in selectors:
            for el in soup.select(sel):
                el.decompose()
        # apri i blocchi hidden che ti servono
        for el in soup.select('div[id^="trama"]'):
            classes = el.get("class", [])
            el["class"] = [c for c in classes if c != "hidden"]
        # rimuove completamente il titolo della pagina
        if soup.title:
            soup.title.decompose()
        # adesso trasformi in testo
        text = soup.get_text(" ", strip=False)

        # normalizzazione base
        text = self._normalize_base(text)
        text = text.replace("&nbsp;", " ").replace("&amp;", "&")

        # qui metti le tue regex / stop markers
        text = re.sub(r"ordina per:\s*Filtri attivi:\s*", "", text, flags=re.I)
        text = re.sub(r"Recensione\s*❯", "", text, flags=re.I)
        text = re.sub(r"(Recensione|Cast)(\s*\|\s*(Recensione|Cast|Rassegna stampa|Pubblico|Forum))*","",text,flags=re.I)
        text = re.sub(r"Rassegna stampa\s*\|?", "", text, flags=re.I)
        text = re.sub(r"[▽❯]+", "", text)
        text = re.sub(r"Espandi", "", text)
        text = re.sub(r"Parte del gruppo\s*e", "", text)
        text = re.sub(r"Powered by\s*JustWatch", "", text, flags=re.IGNORECASE)

        text = self._apply_stop_markers(text, self.SERIES_STOP_MARKERS, re.I)
        text = self._strip_markdown_emphasis(text)
        return self._final_cleanup(text)    


    def clean_news_text(self, text: str) -> str:
        """
        Pulizia specifica per le pagine di news.

        Opera sull'HTML tramite BeautifulSoup per rimuovere tag e selettori
        CSS legati alla navigazione e ai menu. Sul testo estratto applica la
        normalizzazione base, rimuove la stringa "Parte del gruppo e" e tronca
        il contenuto agli stop marker di `NEWS_STOP_MARKERS`, che intercettano
        i banner promozionali in coda all'articolo.

        Args:
            text (str): L'HTML grezzo della pagina di news.

        Returns:
            str: Il testo pulito con il solo contenuto dell'articolo.
        """
        soup = BeautifulSoup(text, "html.parser")

        for tag in soup(["script", "style", "svg", "noscript", "iframe", "form", "button", "input", "textarea" ,"select"]):
            tag.decompose()

        if soup.title:
            soup.title.decompose()
        for h1 in soup.find_all("h1"):
            h1.string = "# " + h1.get_text(strip=True)
        selectors = [
            ".btn.main_menu", 
            ".dropdown-menu",
            ".hidden-sm",
            ".hidden-lg.visible-xs",
            ".btn.btn-info.btn-sm",
            ".search-container",
        ]
        for sel in selectors:
            for el in soup.select(sel):
                el.decompose()
        text = soup.get_text(" ", strip=False)
        text = self._normalize_base(text)
        text = text.replace("&nbsp;", " ").replace("&amp;", "&")
        # taglio della coda
        text = re.sub(r"Parte del gruppo\s*e", "", text, flags=re.IGNORECASE)
        text = self._apply_stop_markers(text, self.NEWS_STOP_MARKERS, re.I | re.S)
        text = self._strip_markdown_emphasis(text)
        return self._final_cleanup(text)
    

    def clean_film_cast_text(self , text: str) -> str:
        """
        Pulizia specifica per le pagine del cast di un film.

        Opera sull'HTML tramite BeautifulSoup per rimuovere navigazione,
        rating e link decorativi. Sul testo estratto applica la normalizzazione
        base, rimuove la descrizione estesa del punteggio MYmonetro, il suffisso
        "/5", le righe di ricerca avanzata e tronca il contenuto agli stop marker
        di `FILM_PUBLIC_STOP_MARKERS`.

        Args:
            text (str): L'HTML grezzo della pagina del cast.

        Returns:
            str: Il testo pulito con i soli dati del cast.
        """
        soup = BeautifulSoup(text, "html.parser")

        for tag in soup(["script", "style", "svg", "noscript", "iframe", "form", "button", "input", "textarea" ,"select"]):
            tag.decompose()

        if soup.title:
            soup.title.decompose()
        for h1 in soup.find_all("h1"):
            h1.string = "# " + h1.get_text(strip=True)
        selectors = [
            ".menu_head_link",
            ".menu_head_tit",
            ".linknolinkrosa",
            ".rec_link_disattivo",
            ".navigazione",
        ]
        for sel in selectors:
            for el in soup.select(sel):
                el.decompose()
        text = soup.get_text(" ", strip=False)
        text = self._normalize_base(text)
        text = text.replace("&nbsp;", " ").replace("&amp;", "&")
        # taglio della coda
        text = re.sub(r"M\s*Y\s*M\s*O\s*N\s*E\s*T\s*R\s*O", "MYMONETRO", text, flags=re.I)
        text = re.sub(r"Parte del gruppo\s*e", "", text)
        text = re.sub(r"\s*dizionari\s+critica\s+pubblico\b", "", text, flags=re.I)
        text = re.sub(r"(?im)^.*ricerca(?:&nbsp;|\s)+avanzata.*\n?", "", text)
        text = self._apply_stop_markers(text, self.FILM_CAST_STOP_MARKERS, re.I | re.S)
        text = self._strip_markdown_emphasis(text)
        return self._final_cleanup(text) 


    def clean_film_public_text(self, text: str) -> str:
        """
        Pulizia specifica per le pagine delle recensioni del pubblico.

        Opera sull'HTML tramite BeautifulSoup per rimuovere i controlli
        interattivi delle recensioni: pulsanti "d'accordo/non d'accordo",
        form di risposta, link di apertura profilo utente e testi parziali
        nascosti. Sul testo estratto applica la normalizzazione base, rimuove
        la breadcrumb iniziale, le stringhe "d'accordo?" e "[-]" e tronca il
        contenuto agli stop marker di `FILM_PUBLIC_STOP_MARKERS`.

        Args:
            text (str): L'HTML grezzo della pagina delle recensioni del pubblico.

        Returns:
            str: Il testo pulito con i soli testi delle recensioni.
        """
        soup = BeautifulSoup(text, "html.parser")

        for tag in soup(["script", "style", "svg", "noscript", "iframe", "form", "button", "input", "textarea" ,"select"]):
            tag.decompose()

        if soup.title:
            soup.title.decompose()
        selectors = [
            ".menu_head_link",
            ".menu_head_tit",
            ".rec_link_disattivo",
            ".rec_link_attivo",
        ]
        for sel in selectors:
            for el in soup.select(sel):
                el.decompose()
        for h1 in soup.find_all("h1"):
            h1.string = "# " + h1.get_text(strip=True)
        for el in soup.find_all(id=re.compile(r"^daccordo(si|no)\d+$")):
            el.decompose()
        for el in soup.find_all(id=re.compile(r"^apriform\d+$")):
            el.decompose()
        for el in soup.find_all(id=re.compile(r"^chiudiform\d+$")):
            el.decompose()
        for el in soup.find_all(id=re.compile(r"^parziale\d+$")):
            if "[+]" in el.get_text():
                el.decompose()
        for el in soup.find_all(id=re.compile(r"^apriutente\d+$")):
            el.decompose()
        for el in soup.select(".linknolinkrosa"):
            el.decompose()
        text = soup.get_text(" ", strip=False)
        text = self._normalize_base(text)
        text = self._apply_stop_markers(text, self.FILM_PUBLIC_STOP_MARKERS, re.I | re.S)
        text = re.sub(r"(?im)^.*ricerca(?:&nbsp;|\s)+avanzata.*\n?", "", text)
        text = text.replace("&nbsp;", " ").replace("&amp;", "&")
        text = text.replace("d'accordo?", " ")
        text = text.replace("[-]", " ")
        text = re.sub(r"Home\s*»\s*film\s*»\s*\d{4}\s*»\s*.*?\s*»\s*pubblico","",text,flags=re.I | re.S)
        text = self._strip_markdown_emphasis(text)
        return self._final_cleanup(text)
    

    def clean_generic_text(self, text: str) -> str:
        """
        Pulizia generica per pagine non categorizzate.

        Applica la sola pipeline di base (normalizzazione, rimozione enfasi
        Markdown, cleanup finale) senza logiche specifiche per tipo di pagina.
        Usato come fallback quando `_page_type` non corrisponde a nessuna
        categoria nota.

        Args:
            text (str): Il testo grezzo della pagina.

        Returns:
            str: Il testo normalizzato e ripulito.
        """
        text = self._normalize_base(text)
        text = self._strip_markdown_emphasis(text)
        return self._final_cleanup(text)