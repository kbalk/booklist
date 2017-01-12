"""Distribution setup script for booklist package."""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def readme():
    """Read the README.md file to provide a long description."""
    with open('README.md') as fh_readme:
        return fh_readme.read()

setup(
    name='booklist',
    version='0.1.0',
    packages=['booklist'],
    description='Automated search for current publications for select authors',
    long_description=readme(),
    url='https://github.com/kbalk/booklist',
    author="K. Balk",
    author_email="kbalk@pobox.com",
    license='GNU GPL v3',
    install_requires=['pytest-runner', 'pyYAML', 'voluptuous', 'requests'],
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ['booklist=booklist.main:main']
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Other/Nonlisted Topic'
    ]
)
