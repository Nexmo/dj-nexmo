from setuptools import setup, find_packages


setup(
    name="dj-nexmo",
    version="0.0.1-dev",
    packages=find_packages("src"),
    package_dir={"": "src"},
    zip_safe=True,
    entry_points={
        "console_scripts": ["dj = django.core.management:execute_from_command_line"]
    },
    install_requires=[
        "nexmo          ~= 2.0.0",
        "django         ~= 2.0.0",
        "attrs          ~= 17.4.0",
        "marshmallow    ~= 3.0.0b8",
        "phonenumbers   ~= 8.9.4",
    ],
)
