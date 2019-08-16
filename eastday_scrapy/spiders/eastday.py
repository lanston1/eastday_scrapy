# -*- coding: utf-8 -*-
import scrapy
from scrapy import Spider, Request
from eastday_scrapy.items import EastdayScrapyItem


class EastdaySpider(Spider):
    name = 'eastday'
    allowed_domains = ['mini.eastday.com']
    url = 'http://mini.eastday.com/'

    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'DOWNLOAD_DELAY': 0,
        'COOKIES_ENABLED': False
    }


    def start_requests(self):
        yield Request(
            url = self.url,
            callback = self.parseIndexPage,
            meta = {'usedSelenium': True}
        )

    def parseIndexPage(self, response):
        '''
        解析索引页响应获取所有匹配链接，为了避免429请求太多错误，请求链接前time.sleep(1)
        :param response:
        :yield:请求获取的匹配链接
        '''
        print(response.url)
        url_list = response.xpath('//*[@id="result_list"]/li/h3/a/@href').extract()
        for i, j in enumerate(url_list):
            url_list[i] = "http:" + j
        for child_url in url_list:
            # time.sleep(1)
            yield Request(
                url = child_url,
                callback=self.parseChildurlPage,
                meta={'usedSelenium': False}
            )

    def parseChildurlPage(self, response):
        '''
        解析每一个特定内容响应获取其包含的所有翻页链接，为了避免429请求太多错误，请求链接前time.sleep(1)
        :param response:
        :yield:请求获取的翻页链接，并设置第二次请求相同的链接强制不过滤
        '''
        print(response.url)
        url_list = response.xpath('//*[@class="pagination"]/a/@href').extract()
        grand_urls= list(set(url_list))
        for i in grand_urls:
            if 'channel' in i:
                grand_urls.remove(i)
        for i, j in enumerate(grand_urls):
            grand_urls[i] = "http://mini.eastday.com/a/" + j
        grand_urls.append(response.url)
        print(grand_urls)
        for grand_url in grand_urls:
            # time.sleep(1)
            print(grand_url)
            yield Request(
                url = grand_url,
                callback=self.parseImagePage,
                dont_filter=True,
                meta={'usedSelenium': False}
            )


    def parseImagePage(self, response):
        '''
        解析每一个翻页链接响应获取title和images
        :param response:
        :return:
        '''
        print(response.url)
        title = response.xpath('//*[@class="J-title_detail title_detail"]/h1/span/text()').extract_first()
        images = response.xpath('//*[@class="widt_ad"]/img/@src').extract()
        for i, j in enumerate(images):
            images[i] = 'http:' + j
        eastday_item = EastdayScrapyItem()
        for field in eastday_item.fields:
            try:
                eastday_item[field] = eval(field)
            except:
                print('Field is Not Defined', field)
        yield eastday_item