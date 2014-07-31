import os
from setuptools import setup, find_packages


def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(name='sqmpy',
      version='v1.0.0-alpha.4',
      description='Simple Queue Manager, also sqmpy, is a web interface for submitting jobs to HPC resources.',
      long_description=(read('README.rst')),
      url='http://github.com/mehdix/simple-queue-manager',
      license='BSD',
      author='Mehdi Sadeghi',
      author_email='sade@iwm.fraunhofer.de',
      packages=find_packages(exclude=['tests*']),
      include_package_data=True,
      zip_safe=False,
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Intended Audience :: Science/Research',
          'Natural Language :: English',
          'License :: OSI Approved :: BSD License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
          ],
      #data_files=['config.py',
      #            'sqmpy.db'],
      install_requires=['Flask==0.10',
                        'Flask-SQLAlchemy==1.0',
                        'Flask-Login==0.2.11',
                        'Flask-WTF==0.10.0',
                        'Flask-Admin==1.0.8',
                        'Flask-CSRF==0.9.2',
                        'enum34==1.0',
                        'saga-python==0.16',
                        'py-bcrypt==0.4'])
