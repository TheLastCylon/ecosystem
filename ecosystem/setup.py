from setuptools import setup, find_packages

setup(
    name             = "ecosystem",
    version          = "0.0.1",
    url              = "https://github.com/TheLastCylon/ecosystem",
    author           = "Dirk Botha",
    author_email     = "bothadj@gmail.com",
    description      = "A Python framework for back-end development. Allowing for TCP, UDP and UDS connections. Using JSON as the communications protocol.",
    packages         = find_packages(),
    install_requires = ["sqlalchemy>=2.0.17", "pydantic>=2.7.4"],
)
