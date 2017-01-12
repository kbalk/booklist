"""Test cases related to the Configurator class"""

from textwrap import dedent
from string import Template

from pytest import raises
from booklist.config import Configurator, ConfigError

#pylint: disable=missing-docstring

def test_good_config(tmpdir):
    # Good YAML content.
    config_in = '''
    catalog-url: http://catalog.library.loudoun.gov/
    media-type: Book
    authors:
        - firstname: Sue
          lastname: Grafton
          media-type: eBook

        - firstname: Stephen
          lastname: King
    '''
    # Expected output:  the same YAML content but in a Python dictionary.
    config_out = {
        'catalog-url': 'http://catalog.library.loudoun.gov/',
        'media-type': 'Book',
        'authors': [
            {'firstname': 'Sue',
             'lastname': 'Grafton',
             'media-type': 'eBook'},
            {'firstname': 'Stephen',
             'lastname': 'King'}
        ]
    }
    path = tmpdir.join("goodfile")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    assert config_out == config.validate()

def test_missing_config():
    with raises(ConfigError) as excinfo:
        Configurator(None)
    assert 'must be a non-null string' in str(excinfo.value)

def test_empty_config(tmpdir):
    path = tmpdir.join("emptyfile")
    path.write('')
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'expected a dictionary' in str(excinfo.value)

def test_bad_yaml_format():
    config = Configurator('/etc/passwd')
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'expected a dictionary' in str(excinfo.value)

def test_extraneous_spaces(tmpdir):
    # Good YAML content with spaces before and after values.
    config_in = '''
    catalog-url:      http://catalog.library.loudoun.gov/
    media-type: Book
    authors:
        - firstname:     Sue
          lastname:   Grafton
          media-type:    eBook

        - firstname:                  Stephen
          lastname:     King
    '''
    # Expected output:  the same YAML content but in a Python dictionary.
    config_out = {
        'catalog-url': 'http://catalog.library.loudoun.gov/',
        'media-type': 'Book',
        'authors': [
            {'firstname': 'Sue',
             'lastname': 'Grafton',
             'media-type': 'eBook'},
            {'firstname': 'Stephen',
             'lastname': 'King'}
        ]
    }
    path = tmpdir.join("extraneous spaces")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    assert config_out == config.validate()
    assert config_out['authors'][0]['firstname'] == 'Sue'

def test_quoted_text(tmpdir):
    # Put the full name into the 'lastname' field and use a space for
    # the 'firstname' field.  The space in the firstname is actually kept
    # and not stripped; if a space is not used the schema will complain
    # as the minimum length for the field is 1.  I'm not sure why the space
    # isn't stripped.  The quoted lastname is fine.
    config_in = '''
    catalog-url: http://catalog.library.loudoun.gov/
    media-type: Book
    authors:
        - firstname: ' '
          lastname: 'Sue Grafton'

        - firstname: M.C.
          lastname: Quotes missing
    '''
    # Expected output:  the same YAML content but in a Python dictionary.
    config_out = {
        'catalog-url': 'http://catalog.library.loudoun.gov/',
        'media-type': 'Book',
        'authors': [
            {'firstname': ' ',
             'lastname': 'Sue Grafton'},
            {'firstname': 'M.C.',
             'lastname': 'Quotes missing'}
        ]
    }
    path = tmpdir.join("quoted_text")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    assert config_out == config.validate()

def test_bad_url(tmpdir):
    # YAML content with bad URL
    config_in = '''
    catalog-url: testing
    media-type: Book
    authors:
        - firstname: Sue
          lastname: Grafton
          media-type: eBook

        - firstname: Stephen
          lastname: King
    '''
    path = tmpdir.join("bad_url")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'catalog-url' in str(excinfo.value)

def test_url_no_http(tmpdir):
    # YAML content with URL that has no
    config_in = '''
    catalog-url: 'catalog.library.loudoun.gov'
    media-type: Book
    authors:
        - firstname: Sue
          lastname: Grafton
          media-type: eBook

        - firstname: Stephen
          lastname: King
    '''
    path = tmpdir.join("no_http")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'catalog-url' in str(excinfo.value)

def test_missing_url(tmpdir):
    config_in = '''
    media-type: Book
    authors:
        - firstname: Sue
          lastname: Grafton
          media-type: eBook

        - firstname: Stephen
          lastname: King
    '''
    path = tmpdir.join("missing_url")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'catalog-url' in str(excinfo.value)

def test_bad_media_type(tmpdir):
    config_in = '''
    catalog-url: http://catalog.library.loudoun.gov/
    media-type: nonsense
    authors:
        - firstname: Sue
          lastname: Grafton
          media-type: eBook

        - firstname: Stephen
          lastname: King
    '''
    path = tmpdir.join("bad_media_type")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'media-type' in str(excinfo.value)

def test_bad_author_media_type(tmpdir):
    config_in = '''
    catalog-url: http://catalog.library.loudoun.gov/
    media-type: Book
    authors:
        - firstname: Sue
          lastname: Grafton
          media-type: nonsense

        - firstname: Stephen
          lastname: King
    '''
    path = tmpdir.join("bad_author_media_type")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'media-type' in str(excinfo.value)

def test_optional_media_type(tmpdir):
    config_in = '''
    catalog-url: http://catalog.library.loudoun.gov/
    authors:
        - firstname: Sue
          lastname: Grafton

        - firstname: Stephen
          lastname: King
    '''
    config_out = {
        'catalog-url': 'http://catalog.library.loudoun.gov/',
        'authors': [
            {'firstname': 'Sue',
             'lastname': 'Grafton'},
            {'firstname': 'Stephen',
             'lastname': 'King'}
        ]
    }
    path = tmpdir.join("optional_media_type")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    assert config_out == config.validate()

def test_media_type_transformation(tmpdir):
    # This test also verifies all the allowed media types.
    config_in = Template('''
    catalog-url: http://catalog.library.loudoun.gov/
    media-type: $media
    authors:
        - firstname: Sue
          lastname: Grafton
    ''')
    config_out = {
        'catalog-url': 'http://catalog.library.loudoun.gov/',
        'media-type': 'Book',
        'authors': [
            {'firstname': 'Sue',
             'lastname': 'Grafton'}
        ]
    }
    for media_type in Configurator.MEDIA_TYPES:
        path = tmpdir.join("media_xforms_" + media_type['configName'])
        path.write(dedent(
            config_in.safe_substitute(media=media_type['configName'])))

        config = Configurator(str(path))
        config_out['media-type'] = media_type['FacetName']
        assert config_out == config.validate()

def test_missing_author_lastname(tmpdir):
    config_in = '''
    catalog-url: http://catalog.library.loudoun.gov/
    media-type: Book
    authors:
        - firstname: Sue

        - firstname: Stephen
          lastname: King
    '''
    path = tmpdir.join("no_lastname")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'lastname' in str(excinfo.value)

def test_missing_author_firstname(tmpdir):
    config_in = '''
    catalog-url: http://catalog.library.loudoun.gov/
    media-type: Book
    authors:
        - lastname: Grafton
          media-type: eBook

        - firstname: Stephen
          lastname: King
    '''
    path = tmpdir.join("no_firstname")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'firstname' in str(excinfo.value)

def test_author_tag_but_no_value(tmpdir):
    config_in = '''
    catalog-url: http://catalog.library.loudoun.gov/
    media-type: Book
    authors:
        -
    '''
    path = tmpdir.join("authors_no_tag")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'author' in str(excinfo.value)

def test_no_authors(tmpdir):
    config_in = '''
    catalog-url: http://catalog.library.loudoun.gov/
    media-type: Book
    authors:
    '''
    path = tmpdir.join("no_authors")
    path.write(dedent(config_in))
    config = Configurator(str(path))
    with raises(ConfigError) as excinfo:
        config.validate()
    assert 'authors' in str(excinfo.value)
