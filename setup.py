from distutils.core import setup
setup(
  name = 'pymoodle-jku',
  packages = ['pymoodle_jku', 'pymoodle_jku.Classes', 'pymoodle_jku.Client'],
  version = '0.1.4',
  license='BSD 3-Clause',
  description = 'A client for the moodle page of https://www.jku.at',
  author = 'LeLunZ',
  author_email = 'l.accounts@pm.me',
  url = 'https://github.com/LeLunZ/pymoodle-jku-linz',
  download_url = 'https://github.com/LeLunZ/pymoodle-jku-linz/archive/0.1.4.tar.gz',
  keywords = ['moodle', 'jku', 'linz', 'jku linz'],
  install_requires=[
          'pytube',
          'lxml',
          'requests-futures'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
)