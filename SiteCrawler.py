import json
import scrapy
from scrapy import signals
from urllib.parse import urlparse, ParseResult


def get_url(parent_url, url):
    parsed_parent_url = urlparse(parent_url)
    parsed_url = urlparse(url)

    scheme = parsed_url.scheme
    netloc = parsed_url.netloc
    path = parsed_url.path

    if len(scheme) == 0:
        scheme = parsed_parent_url.scheme

    if len(netloc) == 0:
        netloc = parsed_parent_url.netloc

    if path == '/':
        path = ''

    parsed_url = ParseResult(scheme=scheme, netloc=netloc, path=path, params=parsed_url.params,
                             query=parsed_url.query, fragment='')

    return parsed_url.geturl()


def get_extension(url):
    parsed_url = urlparse(url)

    path = parsed_url.path

    if len(path) == 0 or '.' not in path:
        return None

    parts = path.split('.')

    return parts[len(parts) - 1]


class SiteCrawler(scrapy.Spider):
    name = "site_crawler"

    starting_url = None
    target = None
    unique_params = False

    urls = []

    excluded_extensions = [
        'js',
        'css'
        'swf',
        'zip',
        'rar',
        'png',
        'jpg',
        'jpeg'
        'doc',
        'docx',
        'pdf',
        'exe'
    ]

    excluded_scheme = [
        'javascript',
        'tel'
    ]

    def __init__(self, **kwargs):
        super().__init__(self.name, **kwargs)

        if not hasattr(self, 'url'):
            print('URL is not provided!')

            exit(1)

        self.starting_url = self.url

        if hasattr(self, 'unique-params'):
            self.unique_params = True

        self.target = urlparse(self.starting_url)

        # print('Starting url: %s' % self.starting_url)

        self.start_urls = [self.starting_url]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SiteCrawler, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def parse(self, response):
        for url in response.xpath('//a/@href').extract():
            url = get_url(response.url, url)

            if self.is_valid_url(url):
                if self.add_url(url):
                    yield scrapy.Request(url, callback=self.parse)

        for action in response.xpath('//form/@action').extract():
            url = get_url(response.url, action)

            if self.is_valid_url(url):
                if self.add_url(url):
                    yield scrapy.Request(url, callback=self.parse)

    def spider_closed(self, spider):
        data = {
            'target': self.starting_url,
            'urls': self.urls
        }

        print(json.dumps(data))

    def add_url(self, url):
        if url not in self.urls:
            self.urls.append(url)

            return True

        return False

    def is_valid_url(self, url):
        parsed_url = urlparse(url)

        if self.target.scheme != parsed_url.scheme:
            return False

        if self.target.netloc != parsed_url.netloc:
            return False

        if parsed_url.scheme in self.excluded_scheme:
            return False

        extension = get_extension(url)

        if extension is not None and extension in self.excluded_extensions:
            return False

        if len(parsed_url.query) > 0 and self.unique_params and not self.is_unique_url_with_params(url):
            return False

        return True

    def is_unique_url_with_params(self, url):
        parsed_url = urlparse(url)
        params = self.get_query_keys(url)

        for added_url in self.urls:
            added_parsed_url = urlparse(added_url)

            if added_parsed_url.path != parsed_url.path:
                continue

            added_url_params = self.get_query_keys(url)

            n = 0

            for param in params:
                if param in added_url_params:
                    n = n + 1

            if n == len(params):
                return False

        return True

    def get_query_keys(self, url):
        parsed_url = urlparse(url)

        parts = parsed_url.query.split('&')

        params = []

        for part in parts:
            split = part.split('=')

            params.append(split[0])

        return params
