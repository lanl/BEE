from setuptools import setup

setup(
    name='bee-launcher',
    version='0.1',
    packages=['bee_launcher'],
    url='https://github.com/LANL/BEE',
    license='https://github.com/lanl/BEE/blob/master/LICENSE',
    author='LANL',
    author_email='pbryant1@kent.edu',
    description='BEE: Build and Execute Environment',
    install_requires=[
        'termcolor',
        'PyYAML', 'pexpect'
    ],
    entry_points={
        'console_scripts': [
            'bee-launcher = bee_launcher.__main__:main'
        ]
    }
)