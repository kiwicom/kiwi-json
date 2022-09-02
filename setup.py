from setuptools import find_packages, setup

with open("requirements.txt") as f:
    REQUIREMENTS = f.read().splitlines()

with open("test-requirements.txt") as f:
    TEST_REQUIREMENTS = f.read().splitlines()

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="kiwi-json",
    version="0.10.0",
    url="https://github.com/kiwicom/kiwi-json",
    author="Kiwi.com platform team",
    author_email="platform@kiwi.com",
    packages=find_packages(exclude=["test*"]),
    install_requires=REQUIREMENTS,
    tests_require=TEST_REQUIREMENTS,
    description="DRY JSON encoder.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
