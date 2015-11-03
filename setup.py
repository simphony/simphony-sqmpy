import os
from setuptools import setup, find_packages


def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(name='sqmpy',
      version='0.4',
      description='A simple queue manager to submit and monitor jobs on'
                  'computing resources.',
      long_description=(read('README.rst')),
      url='http://github.com/mehdisadeghi/sqmpy',
      license='BSD',
      author='Mehdi Sadeghi',
      author_email='sade@iwm.fraunhofer.de',
      packages=find_packages(exclude=['tests*']),
      include_package_data=True,
      zip_safe=False,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Natural Language :: English',
          'License :: OSI Approved :: BSD License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
      ],
      data_files=['config.py',
                  'run.py'],
      install_requires=['Flask',
                        'Flask-SQLAlchemy',
                        'Flask-Login',
                        'Flask-WTF',
                        'Flask-CSRF',
                        'Flask-Uploads',
                        'enum34',
                        'saga-python',
                        'py-bcrypt',
                        'names',
                        'gevent'],
      )
