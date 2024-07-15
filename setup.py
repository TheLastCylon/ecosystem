from setuptools import setup, find_packages

setup(
    name                          = "ecosystem",
    version                       = "0.9.9",
    url                           = "https://github.com/TheLastCylon/ecosystem",
    author                        = "Dirk Botha",
    author_email                  = "bothadj@gmail.com",
    description                   = "A Python framework for creating message-based, distributed systems. Allowing for TCP, UDP and UDS communications. Using JSON as the communications protocol.",
    long_description              = open('README.md').read(),
    packages                      = find_packages(include=['ecosystem*']),
    long_description_content_type = 'text/markdown',
    install_requires              = ["sqlalchemy>=2.0.31", "pydantic>=2.8.2"],
    python_requires               = ">=3.11.4",
    license                       = "BSD-3-Clause",
    classifiers                   = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.11',
    ]
)
