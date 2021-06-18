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
    install_requires = ['mne_bids'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)


    #   entry_points                   = {'console_scripts': ['bidscoin         = bidscoin.bidscoin:main',
    #                                                         'bidseditor       = bidscoin.bidseditor:main',
    #                                                         'bidsmapper       = bidscoin.bidsmapper:main',
    #                                                         'bidscoiner       = bidscoin.bidscoiner:main',
    #                                                         'rawmapper        = bidscoin.rawmapper:main',
    #                                                         'dicomsort        = bidscoin.dicomsort:main',
    #                                                         'echocombine      = bidscoin.echocombine:main',
    #                                                         'deface           = bidscoin.deface:main',
    #                                                         'bidsparticipants = bidscoin.bidsparticipants:main',
    #                                                         'physio2tsv       = bidscoin.physio2tsv:main',
    #                                                         'plotphysio       = bidscoin.plotphysio:main']},
