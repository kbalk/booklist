"""Test cases related to the CatalogSearch class"""

from datetime import datetime
import logging

import pytest
from booklist.catalog import CatalogSearch, CatalogSearchError

#pylint: disable=missing-docstring,redefined-outer-name

@pytest.fixture
def catalog_url(scope='module'):  #pylint: disable=unused-argument
    return 'http://catalog.library.loudoun.gov'

@pytest.fixture
def sue_grafton_publications(scope='module'):
    #pylint: disable=unused-argument
    # The following are the 2015 publications for Sue Grafton:
    return {
        'Large Print': [
            'J is for judgment',
            'K is for killer : a Kinsey Millhone mystery',
            'L is for lawless',
            'M is for malice : a Kinsey Millhone mystery',
            'N is for noose a Kinsey Millhone mystery',
            'O is for outlaw',
            'X'
        ],
        'Book': ['X'],
        'Book on CD': ['X'],
        'eAudioBook': [
            'X is for',
            'X'
        ],
        'eBook': ['X is for']
    }

def test_good_init(catalog_url):
    assert isinstance(CatalogSearch(catalog_url), CatalogSearch)

def test_good_init_with_logger(catalog_url):
    logger = logging.getLogger()
    assert isinstance(CatalogSearch(catalog_url, logger), CatalogSearch)

def test_no_url_in_init():
    with pytest.raises(CatalogSearchError) as excinfo:
        empty_url = None
        CatalogSearch(empty_url)
    assert 'argument' in str(excinfo.value)

def test_get_year_filter(catalog_url):
    catalog = CatalogSearch(catalog_url)
    assert catalog.year_filter == datetime.now().year

def test_set_year_filter(catalog_url):
    catalog = CatalogSearch(catalog_url)
    new_year = '2020'
    catalog.year_filter = new_year
    assert catalog.year_filter == new_year

def test_good_search(catalog_url, sue_grafton_publications):
    catalog = CatalogSearch(catalog_url)
    catalog.year_filter = '2015'
    results = catalog.search('Grafton, Sue', 'Book')
    print(results)
    books = sue_grafton_publications['Book']
    large_prints = sue_grafton_publications['Large Print']
    assert len(results) == len(books) + len(large_prints)
    for result in results:
        assert result[1] in books or result[1] in large_prints

def test_good_search_by_media(catalog_url, sue_grafton_publications):
    catalog = CatalogSearch(catalog_url)
    catalog.year_filter = '2015'
    results = catalog.search('Grafton, Sue', 'Book on CD')
    cd_books = sue_grafton_publications['Book on CD']
    assert len(results) == len(cd_books)
    for result in results:
        assert result[1] in cd_books

def test_bad_url():
    catalog = CatalogSearch('http://nosuchurl.com')
    with pytest.raises(CatalogSearchError) as excinfo:
        catalog.search('Grafton, Sue', 'Book')
    assert 'Response to' in str(excinfo.value)

def test_bad_search_by_media(catalog_url):
    catalog = CatalogSearch(catalog_url)
    with pytest.raises(CatalogSearchError) as excinfo:
        catalog.search('Grafton, Sue', 'bad media')
    assert 'Media type' in str(excinfo.value)

def test_bad_search_no_media(catalog_url):
    catalog = CatalogSearch(catalog_url)
    with pytest.raises(CatalogSearchError) as excinfo:
        catalog.search('Grafton, Sue', '')
    assert 'Arguments' in str(excinfo.value)

