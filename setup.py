try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'dockerstat',
    'author': 'Jyrki K',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'jyrkiokaski@gmail.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['dockerstat'],
    'scripts': [],
    'name': 'dockerstat'
}

setup(**config)
