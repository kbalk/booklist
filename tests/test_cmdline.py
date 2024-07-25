"""Test cases related to the command line processing."""

import logging
from textwrap import dedent

import pytest

from booklist.catalog import CatalogSearchError
from booklist.config import Configurator
from booklist.main import cmdline_parser, print_search_results

# pylint: disable=missing-docstring


@pytest.fixture(scope="session", autouse=True)
def create_parser():
    return cmdline_parser()


def test_no_args(capsys, create_parser):
    # pylint thinks the fixture name 'create_parser' is redefined
    # pylint: disable=redefined-outer-name
    with pytest.raises(SystemExit):
        create_parser.parse_args([])
    _, err = capsys.readouterr()
    assert "arguments are required" in err


def test_no_required_args(capsys, create_parser):
    # pylint thinks the fixture name 'create_parser' is redefined
    # pylint: disable=redefined-outer-name
    with pytest.raises(SystemExit):
        create_parser.parse_args(["-d"])
    _, err = capsys.readouterr()
    assert "arguments are required" in err


def test_good_run(tmpdir, capsys):
    config_in = """
    catalog-url: https://catalog.library.loudoun.gov/
    media-type: ebook
    authors:
       - firstname: James
         lastname: Patterson
         media-type: book
    """
    path = tmpdir.join("goodrun")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    config_values = config.validate()
    logger = logging.getLogger()
    logger.setLevel(10)
    print_search_results(config_values, logger)
    out, _ = capsys.readouterr()
    assert "Patterson, James" in out
    assert "Book" in out


def test_bad_url(tmpdir):
    config_in = """
    catalog-url: http://loudoun.gov/
    media-type: ebook
    authors:
       - firstname: Sue
         lastname: Grafton
    """
    path = tmpdir.join("goodrun")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    config_values = config.validate()
    with pytest.raises(CatalogSearchError) as excinfo:
        print_search_results(config_values, logging.getLogger())
    assert "Response to" in str(excinfo.value)
