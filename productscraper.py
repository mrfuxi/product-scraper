#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Products Scraper.

Usage:
  productscraper.py URL

Options:
  -h --help     Show this screen.
"""

import os
import re
import sys
import json
from urlparse import urljoin

import requests
from bs4 import BeautifulSoup
from docopt import docopt


class MainPageException(Exception):
    pass


class ProductScraper(object):
    '''
    ProductsScaper provides a way of extracting inforation about products form given URL
    Base url has to point to a page with list of products.

    Usage:

    >>> from productscraper import ProductScraper
    >>> scraper = ProductScraper('http://somewhere.com/fruits/')
    >>> product_data = scraper.scrape()
    >>> print product_data
    {
        'results': [{
            'title': 'Fruit A',
            'description': 'Tasty',
            'unit_price': 1.8,
            'size': '1.22kb',
        }],
        'total': 1.8,
    }

    It expects to work on base page html that contains:
    <ul class="productLister">
        <li>
            <h3>
                <a href="URL">Title</a>
            </h3>
            <tag class="pricePerUnit">£1.8/unit</tag>
        </li>
    </ul>

    And details page that contains:
    <p class="productText">
        Some details about the product
    </p>
    '''

    NUMBER_REGEX = re.compile(r'\d*\.\d+|\d+')

    def __init__(self, start_url):
        self._start_url = start_url

    def scrape(self):
        ''' Scrapes product web page.
        Returns a dict with info about products and total cost (1 of each)

        {
            'results': [{
                'title': 'Fruit A',
                'description': 'Tasty',
                'unit_price': 1.8,
                'size': '1.22kb',
            }],
            'total': 1.8,
        }
        '''

        main_page_content = self._get(self._start_url)
        if not main_page_content:
            # If start page does not have any content,
            # there is no point going furhter (emtpy page, http error, ...)
            raise MainPageException("Could not fetch body of main page")

        main_page = self._parse(main_page_content)

        results = []
        total = 0.0
        for product in self._products(main_page):
            product_data = self._product_info(product)
            total += product_data.get('unit_price', 0.0)
            results.append(product_data)

        product_data = {
            'results': results,
            'total': round(total, 2),
        }

        return product_data

    def _get(self, url):
        ''' Wraper around requests maily to handle relative URLs '''

        url = urljoin(self._start_url, url)
        response = requests.get(url)
        if response.ok:
            return response.text
        else:
            return None

    @staticmethod
    def _products(page):
        ''' Wraper around requests maily to handle relative URLs

        Expected html structure:
        <ul class="productLister">
            <li>
                ...
            </li>
        </ul>
        '''

        product_list_el = page.body.find('ul', class_='productLister')
        if not product_list_el:
            return []

        products = product_list_el.find_all('li', recursive=False)
        return products

    def _product_info(self, product):
        ''' Extracts available info from product listed on base page.
        Returned dict will contain as much info as it was possible to gather:
        - title
        - description (separate request to detail page)
        - size of details page in kb
        - unit price

        Expected html structure:
        <li>
            <h3>
                <a href="URL">Title</a>
            </h3>
            <tag class="pricePerUnit">£1.8/unit</tag>
        </li>
        '''
        info = {}
        info.update(self._product_title_section(product))
        info.update(self._product_price_section(product))

        return info

    @staticmethod
    def _parse(page_content):
        ''' Pases content in consistent way '''
        return BeautifulSoup(page_content, 'html5lib')

    def _product_title_section(self, product):
        ''' Parses title section of product on the list.
        Returns dict with all info it could get:
        - title
        - description (separate request to detail page)
        - size of details page in kb

        Expected html structure of title section:
        <h3>
            <a href="URL">Title</a>
        </h3>

        Expected html structure of details page:
        <p class="productText">
            Some details about the product
        </p>
        '''

        info = {}

        title_el = product.find('h3')
        if not title_el:
            return info
        info['title'] = title_el.text.strip()

        link_el = title_el.find('a')
        if not link_el or not link_el.attrs.get('href'):
            return info

        details_url = link_el.attrs.get('href')
        details_page_content = self._get(details_url)
        if not details_page_content:
            return info

        details_page = self._parse(details_page_content)
        description = details_page.find(class_='productText').text
        info['description'] = description.strip()

        page_size = len(details_page_content)
        info['size'] = '{:.2f}kb'.format(page_size/1000.0)

        return info

    def _product_price_section(self, product):
        ''' Parses price section of product on the list.
        Returns dict with unit price if present.

        Expected html structure of title section:
        <tag class="pricePerUnit">
            £1.8/unit
        </tag>
        '''

        info = {}
        unit_price_el = product.find(class_='pricePerUnit')
        if not unit_price_el:
            return info

        match = re.search(self.NUMBER_REGEX, unit_price_el.text)
        if match:
            info['unit_price'] = float(match.group())

        return info


def main(start_url):
    scraper = ProductScraper(start_url=start_url)
    try:
        return scraper.scrape()
    except requests.exceptions.ConnectionError, e:
        return 'Could not connect to {}'.format(e.request.url)
    except (MainPageException, requests.exceptions.RequestException), e:
        return e.message


if __name__ == '__main__':
    arguments = docopt(__doc__)
    start_url = arguments.get('URL', '')

    data = main(start_url)

    if isinstance(data, dict):
        print json.dumps(data, indent=4)
        sys.exit(os.EX_OK)

    print data
    sys.exit(1)
