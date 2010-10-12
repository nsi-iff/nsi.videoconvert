from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='nsi.videoconvert',
      version=version,
      description="A package to convert any kind of video to ogg.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Eduardo Braga',
      author_email='ebfj8@gmail.com',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
          'twisted',
          'zope.interface'
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
