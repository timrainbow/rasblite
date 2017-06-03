from setuptools import setup, find_packages
import os


setup(
    name='rasblite',
    version='1.0.0',
    url='https://github.com/timrainbow/rasblite',
    download_url='https://github.com/timrainbow/rasblite/archive/1.0.0.tar.gz',
    license='MIT License',
    author='Tim Rainbow',
    author_email='tim@timrainbow.com',
    description='Lightweight RESTful API Server Builder',
    keywords = ['REST', 'RESTFul', 'testing', 'Lightweight', 'HTTP', 'server', 'builder'],
    entry_points={
        'console_scripts': [
            'rasblite-run = rasblite.run:command_line_run',
            ],
        },
    packages=find_packages(exclude=('tests', 'docs')),
    package_data={'rasblite': ['rasblite/resources/*.ico']},
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content']
)
