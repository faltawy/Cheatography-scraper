import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import grequests
from dateutil.parser import parse
from requests_html import HTMLSession
from pywget import wget, bar_adaptive

__doc__ = "Cheatography Scraper Package"


class PdfDownloader:
    "This Class Deals With Pdf to download it"

    def __init__(self, link):
        self.link = link

    def download(self, location):

        wget.download(self.link, out=location)


class Cheatography:
    "This Class handels the Main cheatsheet Functions as (searcher)"

    def __init__(self):
        self.site_name = ""
        self.base_url = "https://cheatography.com"
        self.search_url = self.base_url + "/explore/search/?q=%s&page=%d"
        self.search_results = []

    def count_pages(self, soup) -> int:
        pagination = soup.find("div", class_="pagination")
        if pagination:
            pagination_items = [
                item.text for item in pagination.find_all("a")
            ]  # Has Some Text within it

            for item in pagination_items:
                int_items = []
                try:
                    int_item = int(item)
                    int_items.append(int_item)
                except:
                    pagination_items.remove(item)
                return sorted(int_items)[-1]
        else:
            return 1

    class CheatSheet:
        "This is the cheatsheet class"

        def __init__(
            self,
            link,
            title=None,
            puplish_date=None,
            description=None,
            download_links: list = None,
            stars: int = None,
            ratings: int = None,
        ):
            self.title = title
            self.link = link
            self.Publish_date = puplish_date
            self.download_links: list = download_links
            self.stars = stars
            self.ratings = ratings
            self.description: str = description

        @property
        def pdf_bw(self) -> str:
            for link in self.download_links:
                if link.endswith("/pdf_bw/"):
                    d = PdfDownloader(link)
                    return d
                else:
                    None

        @property
        def pdf_colored(self) -> str:
            for link in self.download_links:
                if link.endswith("/pdf/"):
                    d = PdfDownloader(link)
                    return d
                else:
                    None

        @property
        def pdf_latex(self) -> str:
            for link in self.download_links:
                if link.endswith("/latex/"):
                    d = PdfDownloader(link)
                    return d
                else:
                    None

        def __repr__(self):
            return self.title

    class SearchResult:
        "This is the search result class"

        def __init__(self, link: str, title: str = None):
            self.link: str = link
            self.title: str = title
            self.cheatography = Cheatography()  # Outer
            self.__session = HTMLSession()

        def fetch(self):
            src = self.__session.get(self.link).content
            soup = self.cheatography.get_soup(src)
            re__ = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)")
            download_tags = soup.find("aside", {"id": "downloads"}).find_all(
                "a", href=re__
            )
            rating_tags = soup.find("span", {"itemprop": "aggregateRating"})
            title = soup.title.text if not self.title else self.title
            date_published = parse(
                soup.find("meta", {"itemprop": "datePublished"}).get("content")
            )

            description_tag = soup.find(
                "p", {"class": "subdesc", "itemprop": "description"}
            )
            description = description_tag.text.title() if description_tag else None

            try:
                stars = rating_tags.find("span", {"itemprop": "ratingValue"}).text
                ratings = rating_tags.find("span", {"itemprop": "ratingCount"}).text
            except:
                stars = 0
                ratings = 0

            download_links = [link.get("href") for link in download_tags]
            cheatsheet = self.cheatography.CheatSheet(
                self.link,
                title,
                date_published,
                description,
                download_links,
                stars,
                ratings,
            )
            return cheatsheet

        def __repr__(self):
            return self.title

    def get_soup(self, content: bytes):
        soup = BeautifulSoup(content, features="html.parser")
        return soup

    def __searcher(self, kwrds: str = None, group_link=None, max_pages: int = 2):
        search_urls = []

        if kwrds is not None and group_link is None:
            plus_quote_str = quote_plus(kwrds)
            for page in range(max_pages):
                url = self.search_url % (plus_quote_str, (page + 1))
                search_urls.append(url)

        if kwrds is None and group_link is not None:
            for page in range(max_pages):
                url = group_link + "%d" % (page + 1)
                search_urls.append(url)

        search_requests = (grequests.get(url) for url in search_urls)
        search_responses = grequests.map(search_requests)

        for search_response in search_responses:
            soup = self.get_soup(search_response.content)
            re_ = re.compile("cheat_sheet")
            search_items = soup.find_all("div", {"id": re_})

            for item in search_items:
                title_tag = item.find("span", {"itemprop": "name"})
                title = title_tag.text

                link = self.base_url + title_tag.parent.get("href")
                cheatsheet = self.SearchResult(title=title, link=link)
                self.search_results.append(cheatsheet)

        if self.search_results:
            return self.search_results
        else:
            return None

    @property
    def search_count(self) -> int:
        return len(self.search_results)

    def fetch_from_link(self, link: str):
        "This Function Takes only the cheatsheet link only cheatsheet not group of them"
        cheat_sheet = self.SearchResult(link)
        return cheat_sheet.fetch()

    def fetch_group(self, link: str, max_pages=2):
        "This For fetching group of cheatsheets present in the same page like search page"
        return self.__searcher(group_link=link, max_pages=max_pages)

    def searcher(self, kwrds: str, max_pages=2):
        "This For searching the website for sheets"
        return self.__searcher(kwrds=kwrds, max_pages=max_pages, group_link=None)

    def __str__(self):
        return self.site_name
