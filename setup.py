from setuptools import setup, find_packages
setup(
    name="gphotos",
    version="0.2",
    packages=find_packages(),
    entry_points={
        'console_scripts':
            ['gphotos-cli=gphotos.gphotos_cli:main']},
    install_requires=[
        'google-api-python-client-py3',
        'oauth2client',
        'tqdm'
        ],

    author="Steve Newbury",
    author_email="steve@sjnewbs.net",
    url="https://github.com/stevenewb0s/gphotos-cli",
)
