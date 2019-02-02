import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="slothtest",
    version="0.0.4",
    author="Paul Kovtun",
    author_email="trademet@gmail.com",
    description="Sloth Test: An Automatic Unit Test Generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elegantwist/slothtest",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
            "joblib",
        ],
)