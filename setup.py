from setuptools import setup, find_packages


setup(
    name="dj-nexmo",
    version="0.0.1",
    author="Nexmo Developer Relations",
    author_email="devrel@nexmo.com",
    url="https://developer.nexmo.com/",
    description="Utilities for Django developers using Nexmo's APIs",

    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",

    packages=find_packages("src"),
    package_dir={"": "src"},
    zip_safe=True,
    entry_points={
        "console_scripts": ["dj = django.core.management:execute_from_command_line"]
    },
    install_requires=[
        "nexmo          >= 2.0.0,<2.1",
        "django         >= 2.0.0",
        "attrs          ~= 17.4.0",
        "marshmallow    == 3.0.0b11",
        "phonenumbers   ~= 8.9.4",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Communications :: Telephony",
    ],
)
