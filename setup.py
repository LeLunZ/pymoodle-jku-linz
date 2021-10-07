from pathlib import Path

from setuptools import setup

try:
    this_directory = Path(__file__).absolute().parent
    with open((this_directory / 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = ''

try:
    this_directory = Path(__file__).absolute().parent
    with open((this_directory / 'requirements.txt'), encoding='utf-8') as f:
        requirements = f.readlines()
    requirements = [line.strip() for line in requirements]
except FileNotFoundError:
    requirements = []

setup(
    name='pymoodle-jku',
    long_description_content_type='text/markdown',
    long_description=long_description,
    packages=['pymoodle_jku', 'pymoodle_jku.classes', 'pymoodle_jku.client', 'pymoodle_jku.utils'],
    version='1.1.5',
    license='BSD 3-Clause',
    description='A client for the moodle page of JKU Linz.',
    author='LeLunZ',
    author_email='l.accounts+pypi@pm.me',
    url='https://github.com/LeLunZ/pymoodle-jku-linz',
    download_url='https://github.com/LeLunZ/pymoodle-jku-linz/archive/1.1.5.tar.gz',
    keywords=['moodle', 'jku', 'linz', 'jku linz'],
    install_requires=requirements,
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Utilities',
        'Topic :: Education',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Typing :: Typed',
        'License :: OSI Approved :: BSD License',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Natural Language :: English',
    ],
    entry_points={
        'console_scripts': ['pymoodle=pymoodle_jku.pymoodle:main'],
    }
)
