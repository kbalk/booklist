# booklist

If you're a frequent library user, you might go online to your library's
public website and search for the latest books available from your favorite
authors.  If your list of favorite authors is long, that's a tedious task
even with saved searches.

This script, `booklist`, can make that task easier by automating the search
for any new publications by those authors.

However, this script will only work with libraries using the CARL.X
Integrated Library System.  The GitHub repository for 'latest_books' contains
a similar script written in Perl, but is designed to work with Horizon's
Information Portal version 3.23_6380.

`booklist` works by accessing a given library's website to search for
publications from a given author, of a specific media type and within the
current year.  The results are printed to the console.  The search is
repeated for each author listed in a configuration file.

The configuration file is in YAML format and provides the library's
catalog URL, default media type, authors and any specific media types
for authors.  The publication time period includes publications with an
unknown publication time as the unknown time might include the current year.

## Installation

To install the latest release from github:

```sh
git clone https://github.com/kbalk/booklist.git && cd booklist
pip install .
```

After installation, modify the default configuration file `sample_config`,
which is found in the same directory as this README.  In particular, the
catlog-url and author list should be edited to specify the appropriate
library and authors of interest.  Refer to the
['Configuration File'](#configuration-file) section for further details.

### Prerequisites

This script requires Python 3.8 or newer, plus the following libraries:

* Pytest
* PyYAML
* Voluptuous (for validation of YAML data; see [Developer Notes](#developer-notes))
* Requests

## Configuration File

The name of the YAML-formatted configuration file is a required argument
to running the `booklist` script.  The format is as follows:

Tag   | Description
------------------|-----------------
catalog-url | Required.  Must be a valid URL for a website using the CARL.X Integrated Library System.
media-type  | Optional.  The default media type is book; allowed types are listed below.
authors     | Required.  List of authors specified by first and last name and optionally by media-type.
firstname   | Required.  Sub-tag of 'authors'.  First name of author.
lastname    | Required.  Sub-tag of 'authors'.  Last name of author.
media-type  | Optional.  Sub-tag of 'authors'.  See list of media types below.

Allowed media types:

- Book
- Electronic Resource
- eBook
- eAudioBook
- Book on CD
- Large Print
- Music CD
- DVD
- Blu-Ray
- eMusic

Note:  The media types can be in upper, lower or mixed case as the case
will be ignored.  Types that consist of more than one word may be enclosed
in quotes or not.

Also, some media types are supersets, i.e., a type of 'book' includes
'large print' books.  A type of 'electronic resource' includes 'ebook'.

Also, some media types will appear to return what appears to be duplicate
entries, but the library catalog shows different ids for the entries, so
the library catalog considers them unique entries.

Example configuration file:

```YAML
catalog-url: http://catalog.library.loudoun.gov/
media-type: Book
authors:
   - firstname: James
     lastname: Patterson
     media-type: book on cd

   - firstname: Alexander
     lastname: McCall Smith
```

## Usage

```sh
Usage: booklist [-h] [-d] config_file

Search a public library's catalog website for this year's publications
from authors listed in the given config file.

positional arguments:
  config_file  Config file containing library's catalog url and
               list of authors

optional arguments:
  -h, --help   show this help message and exit
  -d, --debug  Print debug information to stdout
```

A sample configuration file named `sample_config` has been provided with
the distribution.  The format of the configuration file is described
[here](#configuration-file).

## Limitations

I wasn't able to determine the version of CARL.X used in my testing,
but even so it appears that CARL.X is configurable for the types of
filters and media it will permit.  Therefore this script may not work
for any given CARL.X ILS, but it can be used as a starting point
for any needed modifications.

## Development environment

The `pyproject.toml` file is configured to use `hatch`.  `hatch` can be
used to setup a virtual environment, run linters and formaters and the
unit tests.  Install `hatch` (version 1.10.0 or greater), then create a
virtual environment of your choice.

Note:  It is not necessary to explicitly install the linters, formatters or
test tools as those dependencies are specified in `pyproject.toml` and will
be pulled in as required.

To install `hatch`:

```sh
pip install hatch
```

Create an environment:

```sh
hatch env create
```

### Linting and formatting

```sh
# Note:  there are issues using pylint with hatch that I'm still trying
# to work out.  It may make more sense to run pylint directly.
hatch fmt -l booklist

# Check for potential formatting changes, but don't make them:
hatch fmt -f --check booklist tests

# Make necessary formatting changes:
hatch fmt -f booklist tests
```

By default `hatch` uses `pytest` for unit tests:

```sh
# Run all unit tests:
hatch test

# Code coverage:
hatch test --cover
```

### Developer Notes

The `Voluptuous` package is no longer maintained.  I researched some
alternatives to YAML validation and `strictyaml` looked like a possibility.
However, there were issues with `strictyaml` at the time I checked:

- No checks for empty strings or a minimum length.  A check of
  `Regex(r"\S+.*")` could be used, but the error message showed both
  the prior line and the line with the empty string value.
- Custom validators (used for the media types) are considered
  experimental.
- No recent efforts into maintaining the package for the last 6 months.

Example of schema used in testing `strictyaml` (without custom validator):

```
schema = Map(
    {
        "catalog-url": Url(),
        Optional("media-type"): Enum(media_types),
        "authors": Seq(
            Map(
                {
                    "firstname": Regex(r"\S+.*"),
                    "lastname": Regex(r"\S+.*"),
                    Optional("media-type"): Enum(media_types),
                },
            )
        ),
    },
)
```

If `Voluptuous` is removed from PyPi, or a better package becomes available,
then this issue will be revisited.  Alternatively, a different format, such
as TOML could be used for configuration files.
