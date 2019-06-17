import setuptools

with open("README.md", "r") as fi:
    long_description = fi.read()

setuptools.setup(
    name="bee",
    version="0.0.1",
    author="Timothy Randles",
    author_email="trandles@lanl.gov",
    description="BEE is a software package for containerizing HPC applications and managing job workflow",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lanl/BEE",
    py_modules=["bee"],
    install_requires=[
        "pyro4",
        "termcolor",
        "tabulate",
        "pexpect",
        "python-openstacklient",
        "python-heatclient",
        "python-neutronclient"
    ],
    classifiers=[
        "Environment :: Console",
        "Environment :: OpenStack",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Clustering",
        "Topic :: System :: Database",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring"
    ]
)
