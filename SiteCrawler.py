import json
import scrapy
from scrapy import signals
from urllib.parse import urlparse, ParseResult


def get_url(parent_url, url):
    parsed_parent_url = urlparse(parent_url)
    parsed_url = urlparse(url)

    scheme = parsed_url.scheme

    if len(scheme) == 0:
        scheme = parsed_parent_url.scheme

    parsed_url = ParseResult(scheme=scheme, netloc=parsed_url.netloc, path=parsed_url.path, params=parsed_url.params,
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

    urls = []

    excluded_extensions = [
        'zip',
        'rar',
        'png',
        'jpg',
        'jpeg'
        'doc',
        'docx',
        'pdf'
    ]

    def __init__(self, **kwargs):
        super().__init__(self.name, **kwargs)

        if not hasattr(self, 'url'):
            print('URL is not provided!')

            exit(1)

        self.starting_url = self.url

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

        if self.target.netloc != parsed_url.netloc:
            return False

        extension = get_extension(url)

        if extension is not None and extension in self.excluded_extensions:
            return False

        return True
