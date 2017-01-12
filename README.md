# booklist.py

If you're a frequent library user, you might go online to your library's
public website and search for the latest books available from your favorite
authors.  If your list of favorite authors is long, that's a tedious task
even with saved searches.

This script, 'booklist' can make that task easier by automating the task
of determining whether the library has any new publications available for
those authors.

However, this script will only work with libraries using the CARL.X
Integrated Library System.  The GitHub repository for 'latest_books' contains
a similar script written in Perl, but is designed to work with Horizon's
Information Portal version 3.23_6380.

The 'booklist' script works by accessing a given library's website using
the appropriate POST requests, performing a search for each desired author
and media type, then printing the results.  The library's catalog URL, list
of authors and the desired media types is expected to be contained in a
YAML file created by the user.

The default media type is 'book' and the default publication time period
is the current year.  However, media with an unknown publication time
period will also be returned in a search as the unknown time might include
the current year.

## Installation

To install the latest release from github:

```sh
pip install git+git://github.com/kbalk/booklist.git
```

Next, modify the default configuration file `sample_config`, which is
found in the same directory as this README.  In particular, the catlog-url
and author list should be edited to specify the appropriate library and
authors of interest.  Refer to the sections further on for details on the
configuration file and instructions for running the script.

### Prerequisites

This script was written using Python 3.5 and tested with Pytest 3.0.5.  It
is possible that it will run on earlier versions of Python 3 or test with
earlier versions of Pytest, but that has not been verified.

* Pytest 3.0.5
* PyYAML
* Voluptuous (for validation of YAML data)
* Request

### Unit tests

Unit tests can be invoked using Pytest:

```sh
# From the booklist root directory:
pytest setup.py test

# Or, once the package is installed, tests can be simply run by:
pytest

# Code coverage:
pytest --cov=booklist
```

## Configuration File

The name of the YAML-formatted configuration file is a required argument
to running the `booklist` script.  The format of this file is as follows:

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

Note:  The media types may be in upper, lower or mixed case as the case
will be ignored.  Types that consist of more than one word may be enclosed
in quotes or not; it doesn't matter.

Also, some media types are supersets, i.e., a type of 'book' includes
'large print' books.  A type of 'electronic resource' includes 'ebook'.

Example configuration file:

```YAML
	catalog-url: http://catalog.library.loudoun.gov/
	media-type: Book
	authors:
		- firstname: James
		  lastname: Patterson
		  media-type: eBook

		- firstname: Alexander McCall
	 	  lastname: Smith
```

## Usage

```sh
Usage: booklist.py [-h] [-d] config_file

Search a public library's catalog website for this year's books from
authors listed in config file.

positional arguments:
  config_file  Config file containing library's catalog url and
               list of authors

optional arguments:
  -h, --help   show this help message and exit
  -d, --debug  Print debug information to stdout
```

A sample configuration file of `sample_config` has been provided with
the distribution.  The format of the configuration file is described
[here](#configuration-file).
