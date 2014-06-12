from setuptools import setup


setup(name='SimpleQueueManager',
      version='0.1',
      description='Simple Queue Manager',
      author='Mehdi Sadeghi',
      author_email='sade@iwm.fraunhofer.de',
      url='',
      requires=['Flask',
                'Flask-SQLAlchemy',
                'Flask-Login',
                'Flask-Admin',
                'Flask-WTF',
                'py-bcrypt'])