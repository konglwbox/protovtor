# coding: utf-8
from setuptools import setup, find_packages

setup(
    name="protovtor",
    version="1.0.1",
    url="https://github.com/konglwbox/protovtor",
    keywords=["protovtor", "json", "conversion", "validation"],
    description="Simple data conversion and validation library",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=2.7",
    license="MIT",

    author="konglw",
    author_email="konglwbox@foxmail.com"
)
