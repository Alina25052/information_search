from pycoder.items import PycoderItem

import scrapy
from urllib.parse import urljoin

class PycoderSpider(scrapy.Spider):
    name = 'pycoder'
    start_urls = ['https://flo.discus-club.ru/katalog-cvetov.html']
    visited_urls = []
    

    def parse(self, response):
        if response.url not in self.visited_urls:
            self.visited_urls.append(response.url)
            SET_SELECTOR='a.nspImageWrapper::attr(href)'
            for post_link in response.css(SET_SELECTOR).extract():
                url = urljoin(response.url, post_link)
                yield response.follow(url, callback=self.parse_flowers)
          

            #NEXT_PAGE = 'a.paginator__page-relative::attr(href)'
            #next_page = response.css(NEXT_PAGE).extract()
            #if chet < 10:
                #print(chet)
                #next_page_url = 'https://eda.ru/recepty?page=' + str(chet)
                #yield response.follow(next_page_url, callback=self.parse)
                

    def parse_flowers(self, response):
        item = PycoderItem()
        title = response.css('h1.article-title::text').extract_first()
        body = response.css('p::text').extract_first()
        url = response.url
        item['title'] = title
        item['body'] = body
        item['url'] = url
        yield item


