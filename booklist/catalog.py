#!/usr/bin/env python3
"""Perform a search on the library's catalog website.

Contains the CatalogSearch and CatalogSearchError classes.

Issues the appropriate POST requests to search the catalog.  The requests
are in JSON format, as are the responses.  The request data contains
filters to narrow the search to an author, year and media type.  The
reponses are used to determine the number of publications meeting those
filters and the list of publications.
"""

import http.client as http_client
import json
import logging
from datetime import datetime
from time import gmtime, mktime
from urllib.parse import urljoin

import requests
from voluptuous import Invalid

from booklist.config import Configurator

# pylint: disable=logging-format-interpolation


class CatalogSearchError(Exception):
    """Exception used for reporting problems accessing the library catalog.

    Problems can include invalid parameters, invalid sequence of method
    calls, problems connecting to the website, etc.

    Each of these problems could have their own exception handler, but
    all of them are fatal errors and no special handling will correct
    the problem.

    Also, care was taken to ensure that the error messages provide enough
    information that it's not necessary to have unique exceptions to
    create unique error messages for the user.
    """


class CatalogSearch:
    """Handles requests to a public library's catalog website.

    To perform a search on the library's catalog, two types of requests
    are needed:  one to retrieve the total number of publications
    available given a set of filters, the other to retreive publication
    information up to 'hitsPerPage' per request.

    These two requests are issued for the current year and again for
    publications with no known publication date.
    """

    # Timeout in seconds for HTTP connect and read.
    TIMEOUT = 5

    # Used for 'cache busting'; in lieu of timezone information or
    # microsecond precision an increment is used.  See __timestamp().
    TIMESTAMP_INCREMENT = 1

    # Maximum number of publications returned in a response.
    MAX_HITS_PER_PAGE = 30

    # CatalogSearchError is not a general error, but specific to this class.
    CatalogSearchError = CatalogSearchError

    def __init__(self, catalog_url, logger=None):
        """Initialize class variables and special logging.

        Args:
          catalog_url (URI):  Valid URL string for the library's catalog.
          logger (logging instance):  caller's logger
        Raises:
          CatalogSearchError:  Invalid catalog_url provided as an argument.
        """
        if not catalog_url:
            raise CatalogSearchError("Null 'catalog_url' argument.")

        # Use the caller's logger, otherwise get a module-specific logger.
        self.logger = logger or logging.getLogger(__name__)

        # If debugging is enabled, turn on debugging in the requests package.
        if self.logger.isEnabledFor(logging.DEBUG):
            http_client.HTTPConnection.debuglevel = 1
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True

        self._catalog_url = catalog_url

        # Current year as a string; used in filtering.
        self._year_filter = datetime.now().year

    @staticmethod
    def __timestamp():
        """Return a 13-digit timestamp; used as a 'cache buster' in requests.

        With the CARL.X system, the parameter '_' in a request appears to
        contain a value used as a 'cache buster'.  A cache buster value
        is checked to see if it's different from a prior request's value
        and if so, then new data is retrieved rather than using cached
        data.

        As the CARL.X system uses a 13-digit timestamp, so will we.  To
        get 13-digits, we multiply a timestamp by 1000.  That yields
        zeros at the end of the number, so we add an increment to the end
        to keep successive requests unique.

        Args:
            None
        Returns:
            int:  13-digit unique value
        """
        CatalogSearch.TIMESTAMP_INCREMENT += 1
        return int(mktime(gmtime()) * 1000) + CatalogSearch.TIMESTAMP_INCREMENT

    def __issue_request(self, endpoint, author, filter_list):
        """Issues a POST request and tests for an error in the response.

        Generic function for search-related POST requests.

        Args:
            endpoint (str):  string added to end of catalog URL.
            author (str):  author's name for use in filter.
            filter_list (list):  list of dictionaries containing filter
                                 information; this is specific to the request.
        Returns:
            requests.models.Response:  request's response
        Raises:
            CatalogSearchError:  request was bad, connnection failed or
                                 timed out.
        """
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.8",
            "Ls2pac-config-type": "pac",
            "Ls2pac-config-name": "default - Go Live load",
            "Referer": self._catalog_url,
        }

        # Create the dictionary to contain filter, sort and other
        # information.  This dictionary will be converted to JSON format
        # for the POST request.
        search_json = {
            "addToHistory": True,
            "dbCodes": [],
            "hitsPerPage": CatalogSearch.MAX_HITS_PER_PAGE,
            "sortCriteria": "NewlyAdded",
            "startIndex": 0,
            "targetAudience": "",
            "facetFilters": filter_list,
            "searchTerm": author,
        }

        # Issue the request using the given URL endpoint.  Also, provide a
        # 'cache buster' timestamp, the json 'data' containing filter
        # information, and a connection timeout value.
        try:
            response = requests.post(
                urljoin(self._catalog_url, endpoint),
                params={"_": self.__timestamp()},
                data=json.dumps(search_json),
                headers=headers,
                timeout=self.TIMEOUT,
            )
        except requests.exceptions.RequestException as exc:
            raise CatalogSearchError(exc) from None

        # Check for a non-ok status code.
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise CatalogSearchError(
                f"Response to '{self._catalog_url}' {endpoint} request:  {exc}"
            ) from None

        # Return a successful response.
        return response

    def __publications_count(self, author, filter_list):
        """Request total number of publications for the given author.

        Args:
            author (str):  author's name for use in filter.
            filter_list (list):  list of dictionaries containing filter
                                 information, e.g., year and media type.
        Returns:
            int:  total number of publications retrievable with given filter
        Raises:
            CatalogSearchError:  request failed or response was not in
                                 JSON format.
        """
        response = self.__issue_request("search/count", author, filter_list)

        # Convert the data in the response from JSON format to a dictionary.
        try:
            decoded_data = response.json()
        except ValueError as exc:
            raise CatalogSearchError(
                f"Bad JSON data in response:  {exc}"
            ) from None

        # One of the fields in the data is a 'success' indicator; check
        # that the value is true.
        if not decoded_data["success"]:
            raise CatalogSearchError(
                "Unsuccessful retrieving total number "
                "of matches on author, media and year"
            )

        # Return the other field in the data that indicates the total number
        # of available publications.
        self.logger.debug(
            f"Expected number of matches:  {decoded_data['totalHits']}"
        )
        return decoded_data["totalHits"]

    def __publications(self, author, filter_list):
        """Request a page of publications for the given author.

        Args:
            author (str):  author's name for use in filter.
            filter_list (list):  list of dictionaries containing filter
                                 information, e.g., year and media type.
        Returns:
            dictionary: information on all the publications matching the
                        filters.  The number returned will not exceed
                        CatalogSearch.MAX_HITS_PER_PAGE.
        Raises:
            CatalogSearchError:  request failed or response was not in
                                 JSON format.
        """
        response = self.__issue_request("search", author, filter_list)

        # Convert the data in the response from JSON format to a dictionary.
        try:
            decoded_data = response.json()
        except ValueError as exc:
            raise CatalogSearchError(
                f"Bad JSON data in response:  {exc}"
            ) from None

        self.logger.debug(f"Decoded response from search:  {decoded_data}")
        return decoded_data["resources"]

    @staticmethod
    def __apply_local_filters(author, publications, filtered_results):
        """Apply filters on publications that aren't performed in request

        Filter more precisely on the author name as the search can sometimes
        retrieve other publications that are not from the author.  Also,
        as the author could be one of several authors for the publication,
        an exact match shouldn't be performed on the name.

        Additionally, check for missing dictionary values for title and
        media type and use 'Unknown' as a replacement.

        Args:
            author (str):  author's name for use in filter.
            publications (list of dicts):  list to be filtered
            filtered_results (list of tuples):  publications that are not
                filtered out will be appended to this list.
        Returns:
            None; filtered_results will be updated to contain
            publications that were not excluded by the filters.
        """
        for publication in publications:
            # Some books don't have authors - don't know why,
            # but 'The Mystery Writers of America cookbook' is one
            # of them; it shows up in a search for Sue Grafton.
            if not publication["shortAuthor"]:
                continue

            pub_format = "Unknown"
            if publication["format"]:
                pub_format = publication["format"]

            pub_title = "Unknown"
            if publication["shortTitle"]:
                pub_title = publication["shortTitle"]

            if author in publication["shortAuthor"]:
                filtered_results.append((pub_format, pub_title))

    def search(self, author, media_type):
        """Perform the catalog search and parse the response.

        A search is performed for publications for the given author with
        the given media type within the current year or of an unknown
        year.

        Args:
            author (str):  author's name for use in filter.
            media_type (str):  type of media to filter on.
        Returns:
            list:  list of tuples containing the media type and publication
                   title for all publications in the current year or of an
                   unknown year.
        Raises:
            CatalogSearchError:  arguments were invalid, requests failed,
                                 responses were invalid or unexpected.
        """
        if not author or not media_type:
            raise CatalogSearchError(
                f"Arguments must be non-null:  author={author}, "
                f"media={media_type}"
            )

        # Media type one of the acceptable types?
        try:
            media = Configurator.validate_media_type(media_type)
        except Invalid as exc:
            raise CatalogSearchError(exc) from None

        # Perform two sets of requests - one for publications within the
        # current year and one for publications of an unknown year.
        filtered_results = []
        for year in ["unknown", self._year_filter]:
            filter_list = [
                {"facetDisplay": year, "facetValue": year, "facetName": "Year"},
                {
                    "facetDisplay": media,
                    "facetValue": media,
                    "facetName": "Format",
                },
            ]

            # Determine how many publications to expect so we know when
            # to stop issuing requests.
            total_count = self.__publications_count(author, filter_list)

            if total_count == 0:
                continue

            # Loop issuing requests until all the publications have been
            # retrieved
            accumulated_count = 0
            while accumulated_count < total_count:
                publications = self.__publications(author, filter_list)

                accumulated_count += len(publications)

                # Apply additional filters that can't be handled in the
                # POST request.
                self.__apply_local_filters(
                    author, publications, filtered_results
                )

            # If we retrieve more publications than expected, raise an error.
            if accumulated_count > total_count:
                raise CatalogSearchError(
                    f"Received more publications than expected; expected "
                    f"{total_count}, currently have {accumulated_count}"
                )

        # Return the list of tuples.
        return filtered_results

    @property
    def year_filter(self):
        """Return current filter value for publication year.
        Args:
            None
        Returns:
            (str):  year currently used as a filter.
        """
        return self._year_filter

    @year_filter.setter
    def year_filter(self, year_string):
        """Set the filter value for the year to the given value.

        This function would primarily be of use for unit testing to ensure
        that a known set of books could be retrieved.

        Args:
           year_string (str):  New filter value for publication year.
        Returns:
           None
        """
        if year_string:
            self._year_filter = year_string
