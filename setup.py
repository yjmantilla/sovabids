import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sovabids",
    version="0.0.1",
    author="Yorguin Mantilla",
    description="Automated eeg2bids conversion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires = ['mne_bids','requests','pybv'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points = {'console_scripts':['sovapply = sovabids.apply_rules:main']}
)
