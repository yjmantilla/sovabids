import setuptools
import versioneer

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]


# Give setuptools a hint to complain if it's too old a version
# 30.3.0 allows us to put most metadata in setup.cfg
# 38.3.0 contains most setup.cfg bugfixes
# Should match pyproject.toml
SETUP_REQUIRES = ["setuptools >= 38.3.0"]


setuptools.setup(
    setup_requires=SETUP_REQUIRES,
    install_requires = REQUIREMENTS,
    entry_points = {'console_scripts':[
        'sovapply = sovabids.rules:sovapply',
        'sovaconvert = sovabids.convert:sovaconvert'
        ]},
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
)
