from setuptools import setup, find_packages
setup(
    name="gphotos-cli",
    version="0.1",
    packages=find_packages(),
    scripts=['gphotos-cli.py']
    install_requires=[
        'google-api-python-client-py3',
        'oauth2client'
        ],

    author="Steve Newbury",
    author_email="steve@sjnewbs.net",
    url="https://github.com/stevenewb0s/gphotos-cli",
)
