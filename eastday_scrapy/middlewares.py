# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from scrapy.http import HtmlResponse
from logging import getLogger
import time
import random
from scrapy.utils.project import get_project_settings
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message




class EastdayScrapySpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomUserAgentMiddleware(object):
    '''
    随机更换User-Agent
    '''
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; Media Center PC 6.0; InfoPath.2; MS-RTC LM 8)'
        ]

    def process_requests(self, request, spider):
        request.hearders['User-Agent'] = random.choice(self.user_agents)



class EastdayScrapyDownloaderMiddleware(object):
    '''
    用chrome抓取页面
    :param request: Request请求对象
    :param spider: Spider对象
    :return: HtmlResponse响应
    '''

    def __init__(self):
        self.logger = getLogger(__name__)
        self.mySetting = get_project_settings()
        self.keyword = self.mySetting['KEYWORD']
        self.timeout = self.mySetting['SELENIUM_TIMEOUT']
        self.isLoadImage = self.mySetting['LOAD_IMAGE']
        self.windowHeight = self.mySetting['WINDOW_HEIGHT']
        self.windowWidth = self.mySetting['windowWidth']
        self.browser = webdriver.Chrome()

        if self.windowHeight and self.windowWidth:
            self.browser.set_window_size(self.windowHeight, self.windowWidth)
        self.browser.set_page_load_timeout(self.timeout)
        self.wait = WebDriverWait(self.browser, self.timeout)


    def process_request(self, request, spider):

        usedSelenium= request.meta.get('usedSelenium', False)
        if usedSelenium:
            print(f"chrome is getting page......")
            try:
                self.browser.get(request.url)
                input = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="bdcsMain"]')))
                time.sleep(2)
                input.clear()
                input.send_keys(self.keyword)
                input.send_keys(Keys.ENTER)
                self.browser.switch_to.window(self.browser.window_handles[1])
                time.sleep(10)
                self.wait.until(EC.presence_of_element_located((By.XPATH,'//*[@id="search_type"]')))
                #将滚动条拉到最后
                scroll_height = 0
                while scroll_height != self.browser.execute_script("return document.body.scrollHeight;"):
                    scroll_height = self.browser.execute_script("return document.body.scrollHeight;")
                    time.sleep(2)
                    self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                    self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="ajax_tips"]')))
                return HtmlResponse(url=request.url,
                                    body=self.browser.page_source,
                                    request=request,
                                    encoding='utf-8',
                                    status=200)
            except Exception as e:
                print(f"chrome getting page error, Exception = {e}")
                return HtmlResponse(url=request.url, status=500, request=request)

        else:
            return None



    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)




class TooManyRequestsRetryMiddleware(RetryMiddleware):
    '''
    handle 429 Too Many Requests
    time.sleep(5) # If the rate limit is renewed in a minute, put 5 seconds, and so on.
    '''

    def __init__(self, crawler):
        super(TooManyRequestsRetryMiddleware, self).__init__(crawler.settings)
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        elif response.status == 429:
            self.crawler.engine.pause()
            time.sleep(5)
            self.crawler.engine.unpause()
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider)
        elif response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider)
        return response
















