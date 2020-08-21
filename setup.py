from setuptools import setup, find_packages

setup(
    name="TSICam",
    version="0.1",
    description="ARTIQ support for Thorlabs Scientific Imaging cameras.",
    author="OregonIons",
    url="https://github.com/ARTIQ-Controllers/TSICam",
    download_url="https://github.com/ARTIQ-Controllers/TSICam",
    install_requires=["sipyco", "numpy", "thorlabs-tsi-sdk"],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "aqctl_TSICam = TSICam.aqctl_TSICam:main",
        ],
    },
)