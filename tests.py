#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import unittest

import requests_mock

from productscraper import (
    main,
    MainPageException,
    ProductScraper,
)


class BaseProductScraperTestCase(unittest.TestCase):
    maxDiff = None
    page_tpl = '<html><body>{}</body></html>'
    product_list_tpl = '<ul class="productLister">{}</ul>'
    product_tpl = (
        '<li>'
        '   <h3><a href="{}">{}</a></h3>'
        '   <p class="pricePerUnit">{}</p>'
        '</li>'
    )
    product_details_tpl = '<p class="productText">{}</p>'

    def _build_main_page(self, products_info, product_tpl=None):
        product_tpl = product_tpl or self.product_tpl

        products = '\n'.join(
            product_tpl.format(*info) for info in products_info
        )
        product_list = self.product_list_tpl.format(products)
        page = self.page_tpl.format(product_list)

        return page

    def _build_product_page(self, description, product_details_tpl=None):
        product_details_tpl = product_details_tpl or self.product_details_tpl
        product_details = product_details_tpl.format(description)
        page = self.page_tpl.format(product_details)
        size = '{:.2f}kb'.format(len(page)/1000.0)
        return page, size


@requests_mock.Mocker()
class ProductListTestCase(BaseProductScraperTestCase):

    def test_empty_product_list(self, req_mock):
        main_page = self.page_tpl.format('some content')
        req_mock.get('http://something.com/fruits/', text=main_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(product_data, {'results': [], 'total': 0.0})

    def test_problems_with_main_page(self, req_mock):
        req_mock.get('http://something.com/500/', status_code=500)

        scraper = ProductScraper('http://something.com/500/')

        with self.assertRaises(MainPageException):
            scraper.scrape()

    def test_product_list_missing(self, req_mock):
        main_page = self._build_main_page([])
        req_mock.get('http://something.com/fruits/', text=main_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(product_data, {'results': [], 'total': 0.0})

    def test_one_product_on_list(self, req_mock):
        main_page = self._build_main_page([
            ('http://something.com/fruits/A/', 'Fruit A', '£1.8/unit'),
        ])
        product_page, product_page_size = self._build_product_page('Tasty')
        req_mock.get('http://something.com/fruits/', text=main_page)
        req_mock.get('http://something.com/fruits/A/', text=product_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'title': 'Fruit A',
                    'description': 'Tasty',
                    'unit_price': 1.8,
                    'size': product_page_size,
                }],
                'total': 1.8,
            },
        )

    def test_multiple_products_on_list(self, req_mock):
        main_page = self._build_main_page([
            ('http://something.com/fruits/A/', 'Fruit A', '£1.8/unit'),
            ('http://something.com/fruits/B/', 'Fruit B', '£2.5'),
            ('http://something.com/fruits/C/', 'Fruit C', '1.1'),
        ])
        product_page_a, product_page_size_a = self._build_product_page('Tasty')
        product_page_b, product_page_size_b = self._build_product_page('Super Fruit')
        product_page_c, product_page_size_c = self._build_product_page('Green')
        req_mock.get('http://something.com/fruits/', text=main_page)
        req_mock.get('http://something.com/fruits/A/', text=product_page_a)
        req_mock.get('http://something.com/fruits/B/', text=product_page_b)
        req_mock.get('http://something.com/fruits/C/', text=product_page_c)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [
                    {
                        'title': 'Fruit A',
                        'description': 'Tasty',
                        'unit_price': 1.8,
                        'size': product_page_size_a,
                    },
                    {
                        'title': 'Fruit B',
                        'description': 'Super Fruit',
                        'unit_price': 2.5,
                        'size': product_page_size_b,
                    },
                    {
                        'title': 'Fruit C',
                        'description': 'Green',
                        'unit_price': 1.1,
                        'size': product_page_size_c,
                    },
                ],
                'total': 5.4,
            }
        )


@requests_mock.Mocker()
class ProductTestCase(BaseProductScraperTestCase):
    def test_product_price_missing(self, req_mock):
        main_page = self._build_main_page([
            ('http://something.com/fruits/A/', 'Fruit A', ''),
        ])
        product_page, product_page_size = self._build_product_page('Tasty')
        req_mock.get('http://something.com/fruits/', text=main_page)
        req_mock.get('http://something.com/fruits/A/', text=product_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'title': 'Fruit A',
                    'description': 'Tasty',
                    # 'unit_price': '?',  # unit price missing
                    'size': product_page_size,
                }],
                'total': 0.0,
            },
        )

    def test_product_price_invalid(self, req_mock):
        main_page = self._build_main_page([
            ('http://something.com/fruits/A/', 'Fruit A', '£blah/unit'),
        ])
        product_page, product_page_size = self._build_product_page('Tasty')
        req_mock.get('http://something.com/fruits/', text=main_page)
        req_mock.get('http://something.com/fruits/A/', text=product_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'title': 'Fruit A',
                    'description': 'Tasty',
                    # 'unit_price': '?',  # unit price invalid
                    'size': product_page_size,
                }],
                'total': 0.0,
            },
        )

    def test_product_price_section_missing(self, req_mock):
        product_tpl = '<li><h3><a href="{}">{}</a></h3></li>'
        main_page = self._build_main_page(
            [('http://something.com/fruits/A/', 'Fruit A')],
            product_tpl=product_tpl,
        )
        product_page, product_page_size = self._build_product_page('Tasty')
        req_mock.get('http://something.com/fruits/', text=main_page)
        req_mock.get('http://something.com/fruits/A/', text=product_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'title': 'Fruit A',
                    'description': 'Tasty',
                    'size': product_page_size,
                }],
                'total': 0.0,
            },
        )

    def test_product_title_empty(self, req_mock):
        main_page = self._build_main_page([
            ('http://something.com/fruits/A/', '', 1.2),
        ])
        product_page, product_page_size = self._build_product_page('Tasty')
        req_mock.get('http://something.com/fruits/', text=main_page)
        req_mock.get('http://something.com/fruits/A/', text=product_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'title': '',
                    'description': 'Tasty',
                    'unit_price': 1.2,
                    'size': product_page_size,
                }],
                'total': 1.2,
            },
        )

    def test_product_title_section_missing(self, req_mock):
        product_tpl = '<li><p class="pricePerUnit">{}</p></li>'
        main_page = self._build_main_page([(1.2,)], product_tpl=product_tpl)
        req_mock.get('http://something.com/fruits/', text=main_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'unit_price': 1.2,
                }],
                'total': 1.2,
            },
        )

    def test_product_link_to_details_missing(self, req_mock):
        product_tpl = '<li><h3>{}</h3><p class="pricePerUnit">{}</p></li>'
        main_page = self._build_main_page(
            [('Fruit A', 1.2)], product_tpl=product_tpl,
        )
        req_mock.get('http://something.com/fruits/', text=main_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'title': 'Fruit A',
                    'unit_price': 1.2,
                }],
                'total': 1.2,
            },
        )

    def test_product_link_without_host(self, req_mock):
        main_page = self._build_main_page([
            ('/fruits/A/', 'Fruit A', '£1.8/unit'),
        ])
        product_page, product_page_size = self._build_product_page('Tasty')
        req_mock.get('http://something.com/fruits/', text=main_page)
        req_mock.get('http://something.com/fruits/A/', text=product_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'title': 'Fruit A',
                    'description': 'Tasty',
                    'unit_price': 1.8,
                    'size': product_page_size,
                }],
                'total': 1.8,
            },
        )

    def test_product_link_without_href(self, req_mock):
        product_tpl = (
            '<li>'
            '   <h3><a>{}</a></h3>'
            '   <p class="pricePerUnit">{}</p>'
            '</li>'
        )

        main_page = self._build_main_page(
            [('Fruit A', '£1.8/unit')], product_tpl=product_tpl,
        )
        req_mock.get('http://something.com/fruits/', text=main_page)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'title': 'Fruit A',
                    'unit_price': 1.8,
                }],
                'total': 1.8,
            },
        )

    def test_product_different_responses(self, req_mock):
        main_page = self._build_main_page([
            ('/fruits/200/', 'Fruit A', '£1.8/unit'),
            ('/fruits/404/', 'Fruit B', '£1/unit'),
            ('/fruits/500/', 'Fruit C', '£1/unit'),
        ])
        product_page, product_page_size = self._build_product_page('Tasty')
        req_mock.get('http://something.com/fruits/', text=main_page)
        req_mock.get('http://something.com/fruits/200/', text=product_page, status_code=200)
        req_mock.get('http://something.com/fruits/404/', text='Not Found', status_code=404)
        req_mock.get('http://something.com/fruits/500/', text='Not Found', status_code=404)

        scraper = ProductScraper('http://something.com/fruits/')
        product_data = scraper.scrape()

        self.assertEqual(
            product_data,
            {
                'results': [
                    {
                        'title': 'Fruit A',
                        'description': 'Tasty',
                        'unit_price': 1.8,
                        'size': product_page_size,
                    },
                    {
                        'title': 'Fruit B',
                        'unit_price': 1,
                    },
                    {
                        'title': 'Fruit C',
                        'unit_price': 1,
                    },
                ],
                'total': 3.8,
            },
        )


class MainTestCase(BaseProductScraperTestCase):
    @requests_mock.Mocker()
    def test_main(self, req_mock):
        main_page = self._build_main_page([
            ('http://something.com/fruits/A/', 'Fruit A', '£1.8/unit'),
        ])
        product_page, product_page_size = self._build_product_page('Tasty')
        req_mock.get('http://something.com/fruits/', text=main_page)
        req_mock.get('http://something.com/fruits/A/', text=product_page)

        product_data = main('http://something.com/fruits/')

        self.assertEqual(
            product_data,
            {
                'results': [{
                    'title': 'Fruit A',
                    'description': 'Tasty',
                    'unit_price': 1.8,
                    'size': product_page_size,
                }],
                'total': 1.8,
            },
        )

    def test_invalid_base_url(self):
        scraped = main('invalid.com')
        self.assertEqual(
            scraped,
            "Invalid URL 'invalid.com': No schema supplied. Perhaps you meant http://invalid.com?",
        )

    @requests_mock.Mocker()
    def test_problems_with_main_page(self, req_mock):
        req_mock.get('http://something.com/500/', status_code=500)

        scraped = main('http://something.com/500/')

        self.assertEqual(
            scraped,
            "Could not fetch body of main page",
        )


if __name__ == '__main__':
    unittest.main()
