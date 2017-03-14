try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'dockerstat',
    'author': 'Jyrki K',
    'url': 'https://github.com/sofkaski/dockerstat',
    'download_url': 'https://github.com/sofkaski/dockerstat',
    'author_email': 'jyrkiokaski@gmail.com',
    'version': '1.0',
    'install_requires': ['nose'],
    'packages': ['dockerstat','dockerstat/docker','dockerstat/stats'],
    'scripts': [],
    'name': 'dockerstat'
}

setup(**config)
