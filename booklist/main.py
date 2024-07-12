#!/usr/bin/env python3
"""Automate search of public library website to retrieve list of publications.

Takes a YAML file with the library's catalog URL and list of authors and
issues the appropriate requests to that library's website to retrieve the
latest publications for those authors.  Only works for libraries using the
CARL.X Integrated Library System (ILS).

CARL.X ILS:
--------------------------------------------------------------------------
The CARL.X ILS is based on Web 2.0 technologies so its possible to issue
the POST requests needed to obtain the number of expected publications
and the list of those publications.  It has an "open" API, but that API
appears to be open only to paying customers, i.e., the library staff.

A request URL for CARL.X to search for a given book consists of an array of
facetFilters.  You can filter on format  (media type), publication year,
new titles, etc.  The 'New Titles' filter permits final granularity in time,
e.g., weeks or months.  However, if you go to a library website using CARL.X
and manually select a format filter, the 'New Titles' filter is no longer
selectable.  It's not clear why that is so, but a 'Publication Year' filter
is still permitted.

This script defaults to a search within a publication year and that year is
the current one.  Media with an unknown publication time period will also be
returned from a search as they are future releases that might be available
in the coming year.

Usage:
--------------------------------------------------------------------------
Usage: booklist [-h] [-d] config_file

    Search a public library's catalog website for this year's publications
    from authors listed in the given config file.

    positional arguments:
      config_file  Config file containing catalog url and list of authors

    optional arguments:
      -h, --help   show this help message and exit
      -d, --debug  Print debug information to stdout
"""

import argparse
import logging
import sys

from booklist.config import Configurator
from booklist.catalog import CatalogSearch


def cmdline_parser():
    """Return command line arguments, if they're valid.

    Args:
        None

    Returns:
        argparse.ArgumentParser - command line parser
    """
    parser = argparse.ArgumentParser(
        description=(
            "Search a public library's catalog website for this "
            "year's publications from authors listed in the given "
            "config file."
        )
    )

    parser.add_argument(
        "config_file", help="Config file with library's catalog url and list of authors"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Print debug information to stdout"
    )
    return parser


def print_search_results(config_values, logger):
    """Retrieve and print the author publications for current year.

    Args:
        config_values:  configuration info such as authors, media types
        logger (logging object):  caller's logger

    Returns:
        None

    Raises:
        CatalogSearch.CatalogSearchError:  bad parameters, connection errors,
                                           problems retrieving data
    """
    # The default type is the value specified in the config file or
    # if not found, the standard default type.
    default_media = Configurator.DEFAULT_MEDIA_TYPE
    if config_values["media-type"]:
        default_media = config_values["media-type"]

    try:
        catalog = CatalogSearch(config_values["catalog-url"], logger)
    except CatalogSearch.CatalogSearchError:
        raise  # Only occurs if constructor parameters are bad.

    for author_info in config_values["authors"]:
        author_name = f"{author_info['lastname']}, {author_info['firstname']}"
        media = default_media
        if "media-type" in author_info:
            media = author_info["media-type"]

        print(f"{author_name} -- {media}s:")
        try:
            search_results = catalog.search(author_name, media)
        except CatalogSearch.CatalogSearchError:
            raise

        # Print the search results; each entry in the results list
        # is a tuple containing the media type and publication name
        # (e.g., book title).  Since some media types are supersets
        # of other media types, it seemed useful to provide that
        # extra information.
        if search_results:
            max_width = len(max((info[0] for info in search_results), key=len))
            for resource_info in search_results:
                print(f"  [{resource_info[0]:{max_width}}]  {resource_info[1]}")


def main():
    """Main entry point for retrieving search results from library website."""
    # Parse and validate the command line arguments.
    parser = cmdline_parser()
    args = parser.parse_args()

    # Use logging for error and/or debug messages to stdout.
    loglevel = logging.DEBUG if args.debug else logging.ERROR
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:  %(message)s",
        datefmt="%H:%M:%S",
        level=loglevel,
    )
    logger = logging.getLogger()

    # Validate the config file contents and get the results in a dictionary.
    config = Configurator(args.config_file, logger)
    try:
        config_values = config.validate()
    except Configurator.ConfigError as exc:
        logging.error(exc)
        sys.exit(1)

    # Retrieve the publications for the authors in the configuration file
    # and print the results.
    try:
        print_search_results(config_values, logger)
    except CatalogSearch.CatalogSearchError as exc:
        logging.error(exc)
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
