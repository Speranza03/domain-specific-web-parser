import asyncio
from urllib.parse import urlparse
from .parsers.base_parser import BaseParser
from .parsers.curryfuneralhome_parser import CurryFuneralHomeParser
from .parsers.mymovies_parser import MyMoviesParser
from .parsers.wikipedia_parser import WikipediaParser
from .parsers.boxofficemojo_parser import BoxOfficeMojoParser

def get_parser_for_url(url: str) -> BaseParser:
    """
    Seleziona il parser appropriato in base al dominio dell'URL.

    Estrae il dominio dall'URL e lo confronta con i domini supportati,
    restituendo l'istanza del parser specializzato corrispondente.
    Se il dominio non corrisponde a nessuna regola nota, restituisce
    un'istanza del parser generico 'BaseParser'.

    Args:
        url (str): L'URL da cui estrarre il dominio per la selezione del parser.

    Returns:
        BaseParser: Un'istanza del parser specifico per il dominio, oppure di 'BaseParser' come fallback.
    """
    domain = urlparse(url).netloc
    
    if "curryfuneralhome.org" in domain:
        return CurryFuneralHomeParser()
    elif "wikipedia.org" in domain:
        return WikipediaParser()
    elif "mymovies.it" in domain:
         return MyMoviesParser()
    elif "www.boxofficemojo.com" in domain:
         return BoxOfficeMojoParser()
    else:
        # Fallback se il dominio non ha regole specifiche
        return BaseParser()


async def _async_parse_url(url: str) -> dict:
    """
    Esegue il fetch e il parsing asincrono di un URL.

    Seleziona il parser appropriato tramite 'get_parser_for_url' e delega
    l'intera operazione di crawling e pulizia al metodo 'parse' del parser adatto.

    Args:
        url (str): L'URL della pagina da scaricare e analizzare.

    Returns:
        dict: Il risultato del parsing restituito dal parser selezionato.
    """
    parser = get_parser_for_url(url)
    return await parser.parse(url)


def parse_url(url: str) -> dict:
    """
    Funzione principale esportata per il parsing di un URL.

    Avvolge '_async_parse_url' in 'asyncio.run', rendendo il crawler
    asincrono utilizzabile in contesti sincroni.

    Args:
        url (str): L'URL della pagina da analizzare.

    Returns:
        dict: Il risultato del parsing restituito dal parser selezionato.
    """
    return asyncio.run(_async_parse_url(url))


async def _async_parse_html(url: str, html_text: str) -> dict:
    """
    Esegue il parsing asincrono su un contenuto HTML già disponibile in memoria.

    Seleziona il parser appropriato tramite 'get_parser_for_url', 
    poi delega l'elaborazione al metodo 'parse_html' del parser,
    che non esegue alcun fetch di rete.

    Args:
        url (str): L'URL associato all'HTML, usato esclusivamente per selezionare il parser corretto.
        html_text (str): Il contenuto HTML grezzo da analizzare.

    Returns:
        dict: Il risultato del parsing restituito dal parser selezionato.
    """
    parser = get_parser_for_url(url)
    return await parser.parse_html(url, html_text)


def parse_html_content(url: str, html_text: str) -> dict:
    """
    Interfaccia sincrona per il parsing di HTML grezzo. 

    Funzione wrapper di '_async_parse_html'rendendo accessibile
    il parsing da HTML in-memory in contesti sincroni.

    Args:
        url (str): L'URL associato all'HTML, usato per selezionare il parser.
        html_text (str): Il contenuto HTML grezzo da analizzare.

    Returns:
        dict: Il risultato del parsing restituito dal parser selezionato.
    """
    return asyncio.run(_async_parse_html(url, html_text))
