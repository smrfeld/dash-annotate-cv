from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dash_annotate_cv",
    version="0.1.5",
    author="Oliver K. Ernst",
    description="A Python library for computer vision annotation tasks using Dash",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/smrfeld/dash-annotate-cv",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "dash",
        "scikit_image",
        "plotly",
        "dash_bootstrap_components",
        "dataclasses",
        "mashumaro",
        "pandas",
        "Pillow",
        "pyyaml",
        "scikit-image"
    ],
    python_requires=">=3.6",
    scripts=['bin/dacv']
)
