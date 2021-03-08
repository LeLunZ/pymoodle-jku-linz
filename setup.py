from pathlib import Path

from setuptools import setup

try:
    this_directory = Path(__file__).absolute().parent
    with open((this_directory / 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = ''

setup(
    name='pymoodle-jku',
    long_description_content_type='text/markdown',
    long_description=long_description,
    packages=['pymoodle_jku', 'pymoodle_jku.Classes', 'pymoodle_jku.Client', 'pymoodle_jku.Utils'],
    version='1.0.6',
    license='BSD 3-Clause',
    description='A client for the moodle page of JKU Linz.',
    author='LeLunZ',
    author_email='l.accounts@pm.me',
    url='https://github.com/LeLunZ/pymoodle-jku-linz',
    download_url='https://github.com/LeLunZ/pymoodle-jku-linz/archive/1.0.6.tar.gz',
    keywords=['moodle', 'jku', 'linz', 'jku linz'],
    install_requires=[
        'argcomplete',
        'cryptography',
        'html2markdown',
        'keyring',
        'pick',
        'pytube',
        'lxml',
        'urllib3',
        'sty',
        'requests',
        'requests-futures',
        'io-uuid'
    ],
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    entry_points={
        'console_scripts': ['pymoodle=pymoodle_jku.pymoodle:main'],
    }
)
