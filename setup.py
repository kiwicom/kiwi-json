from setuptools import find_packages, setup

with open("requirements.txt") as f:
    REQUIREMENTS = f.read().splitlines()

with open("test-requirements.txt") as f:
    TEST_REQUIREMENTS = f.read().splitlines()

setup(
    name="kiwi-json",
    version="0.9.0",
    url="https://github.com/kiwicom/kiwi-json",
    author="Kiwi.com platform team",
    author_email="platform@kiwi.com",
    packages=find_packages(exclude=["test*"]),
    install_requires=REQUIREMENTS,
    tests_require=TEST_REQUIREMENTS,
    description="DRY JSON encoder.",
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
    ],
)
