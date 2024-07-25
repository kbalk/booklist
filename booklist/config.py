#!/usr/bin/env python3
"""Contains Configurator and ConfigError classes

The Configurator class reads and validates the configuration file.  The
configuration file contains:
    - URL for the library's catalog website,
    - optional default for desired media type ('Book' is assumed otherwise),
    - list of authors; each entry in the list must contain the author's first
      and last name, and optionally the desired media type for that author.

The ConfigError class is used to report errors found in the configuration
file.

---------------------------------------------------------------------------
The config file is expected to be in in YAML format.  The tags are:

catalog-url:
    Required.  Must be a valid URL for a website using the CARL.X
    Integrated Library System.

media-type:
    Optional.  The default media type is 'book'; allowed types are:
        book
        electronic resource
        ebook
        eaudiobook
        book on cd
        large print
        music cd
        dvd
        blu-ray
        emusic
    These types can be in upper, lower or mixed case as the case will
    be ignored.  Types that are more than one word can be enclosed in
    quotes or not; it won't matter.

    Note that some media types are supersets, i.e., a type of 'book'
    includes 'large print' books.  A type of 'electronic resource'
    includes 'ebook'.

authors:
    Required.  List of authors specified by first and last name and
    optionally by media-type.

authors sub-tags:
    firstname:
        Required.  First name of author.

    lastname:
        Required.  Last name of author.

    media-type:
        Optional.  See media-type above for the allowed values.

---------------------------------------------------------------------------
Example YAML config file:

    catalog-url: https://catalog.library.loudoun.gov/
    media-type: Book
    authors:
        - firstname: James
          lastname: Patterson
          media-type: book on cd

        - firstname: Alexander
          lastname: McCall Smith
"""

import logging

from voluptuous import (
    All,
    Invalid,
    Length,
    MultipleInvalid,
    Required,
    Schema,
    Url,
)
from yaml import YAMLError, safe_load


class ConfigError(Exception):
    """Exception used for reporting problems with config file.

    Problems can include reading or validating the config file.

    Attributes:
       msg - description of type of error
    """


class Configurator:
    """Handles configuration file processing for the booklist.

    Refer to self._schema for the expected config file format.
    """

    # ConfigError is not a general error, but specific to this class.
    ConfigError = ConfigError

    # The following list contains most of the supported media types
    # allowed by the CARL-X ILS.  This is a list of maps, with each map
    # consisting of a media type config name and the equivalent name for
    # use in the URL query string.
    #
    # Note:  when validating the media type name found in the config file,
    # the name will first be converted to lower case before comparing it
    # against this list.
    #
    # Note2:  Some media types don't have a "shortAuthor" field and as
    # responses without an author are ignored, no values are returned.
    # These media types are not allowed as they would be misleading.
    # Examples of those media types: Visual Materials, Video Recording,
    # eVideo, eJournal.
    #
    # Note3:  Some media types appear to return duplicate entries, but the
    # detailed information shows unique ids for the entries.  Examples of
    # those media types: eAudioBook and AudioBook.  So the "e" version of
    # the media type is allowed and the non-"e" version is not.
    MEDIA_TYPES = [
        {"configName": "book", "FacetName": "Book"},
        {
            "configName": "electronic resource",
            "FacetName": "Electronic Resource",
        },
        {"configName": "ebook", "FacetName": "eBook"},
        {"configName": "eaudiobook", "FacetName": "eAudioBook"},
        {"configName": "book on cd", "FacetName": "Book on CD"},
        {"configName": "large print", "FacetName": "Large Print"},
        {"configName": "music cd", "FacetName": "Music CD"},
        {"configName": "dvd", "FacetName": "DVD"},
        {"configName": "blu-ray", "FacetName": "Blu-Ray"},
        {"configName": "emusic", "FacetName": "eMusic"},
    ]
    DEFAULT_MEDIA_TYPE = "Book"

    def __init__(self, config_filename, logger=None):
        """Initialize the configuration filename and map of config values.

        Args:
           config_filename (str): name of config file; must be a YAML file.
           logger (logging instance):  caller's logger
        """
        if not config_filename or not isinstance(config_filename, str):
            raise ConfigError("Config filename must be a non-null string")

        self.logger = logger or logging.getLogger(__name__)

        self._filename = config_filename
        self.logger.info("Config file:  %s", self._filename)

        # Validation rules for YAML configuration file.
        self._schema = Schema(
            {
                Required("catalog-url"): All(Url(str), Length(min=1)),
                "media-type": All(str, Configurator.validate_media_type),
                Required("authors"): [
                    {
                        Required("firstname"): All(str, Length(min=1)),
                        Required("lastname"): All(str, Length(min=1)),
                        "media-type": All(
                            str, Configurator.validate_media_type
                        ),
                    }
                ],
            }
        )

    @staticmethod
    def validate_media_type(media_type):
        """Returns exception if media type invalid, else FacetName string.

        This function is called as part of the schema validation.  Not only
        is the media_type validated, but the value is transformed to the
        string needed for the URL request.

        Args:
            media_type (str):  one of the MEDIA_TYPES['configName'] values

        Returns:
            str:  MEDIA_TYPES['FacetName'] equivalent for given media_type

        Raises:
            voluptuous.Invalid:  media_type is not one of the acceptable media
                type names
        """
        media = media_type.lower()
        facet_name = None
        for mapping in Configurator.MEDIA_TYPES:
            if mapping["configName"] == media:
                facet_name = mapping["FacetName"]
                break
        else:
            raise Invalid(f"Media type of '{media_type}' is invalid.")
        return facet_name

    def validate(self):
        """Return contents of config file if valid, else raise an exception.

        Reads and load the yaml file, then verifies it against the schema.

        Returns:
            dict:  Map of configuration values

        Raises:
            ConfigError:  The file can't be found or read, the file is
                 malformed, or is not consistent with the schema.
        """
        # Attempt to read the YAML-formatted config file.
        yaml_config = None
        try:
            with open(self._filename, "r", encoding="utf-8") as fh_yamlfile:
                try:
                    # Read the YAML formatted information using safe_load().
                    # safe_load() will only recognize standard YAML tags
                    # and can't construct an arbitrary Python object.  As
                    # the config file only requires strings and a uri,
                    # safe_load() will suffice.
                    yaml_config = safe_load(fh_yamlfile)
                except (YAMLError, TypeError) as exc:
                    raise ConfigError(
                        f"Config file '{self._filename}' not a valid YAML file:  {exc}"
                    ) from None
        except IOError as exc:
            raise ConfigError(
                f"Config file '{self._filename}': {exc}"
            ) from None

        # Validate the YAML content against the schema and return the
        # transformed content.
        dict_config = None
        try:
            dict_config = self._schema(yaml_config)
        except MultipleInvalid as exc:
            msg = [f"Config file '{self._filename}' fails schema validation: "]
            for error in exc.errors:
                msg.append(str(error))
            raise ConfigError("\n".join(msg)) from None

        self.logger.debug(f"Config object:  {dict_config}")
        return dict_config
