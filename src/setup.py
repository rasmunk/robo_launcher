from setuptools import setup, find_packages

setup(name='robo_launcher',
      version='0.1',
      description='Launches the robo infrastructure',
      author='Rasmus Munk',
      author_email='munk1@live.dk',
      packages=find_packages(),
      install_requires=['selenium', 'docker', 'GitPython'],
      scripts=['bin/RoboLauncher.py']
      )
