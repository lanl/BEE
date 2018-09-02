import setuptools

setuptools.setup(
    name="bee-core",
    version="0.1.0",
    license="https://github.com/lanl/BEE/blob/master/LICENSE",
    author="Paul",
    author_email="pbryant1@kent.edu",
    packages=[
        "bee_launcher",
        "bee_monitor",
        "bee_logging",
        "bee_internal",
        "bee_orchestrator"
    ],
    include_package_date=False,
    url="https://github.com/paulbry/BEE",
    description="BEE: Build and Execute Environment",
    install_requires=[
        'termcolor',
        'PyYAML',
        'pexpect',
        'Pyro4'
    ],
    entry_points={
        'console_scripts': [
            'bee-launcher = bee_launcher.__main__:main',
            'bee-orchestrator = bee_orchestrator.__main__:main',
            'bee-internal = bee_internal.__main__:main',
            'bee-logging = bee_logging.__main__:main',
            'bee_monitor = bee_monitor.__main__:main'
        ]
    }
)
