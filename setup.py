import versioneer

from setuptools import setup, find_packages

versioneer.versionfile_source = "abl/robot/_version.py"
versioneer.versionfile_build = versioneer.versionfile_source
versioneer.tag_prefix = ""
versioneer.parentdir_prefix = "abl.robot"


TEST_REQUIREMENTS = ["nose"]

setup(
    name = "abl.robot",
    version = versioneer.get_version(),
    cmdclass = versioneer.get_cmdclass(),
    author = "Diez B. Roggisch",
    author_email = "diez.roggisch@ableton.com",
    description = "The Ableton Robot Framework, for writing daemons or commandline tools, with powerful features for error handling and logging.",
    license="MIT",
    packages=find_packages(exclude=['tests']),
    install_requires = [
        "abl.util",
        "abl.vpath",
        "abl.errorreporter",
        "TurboMail >= 3.0",
        "ConfigObj",
        ],
    extras_require = dict(
        testing=TEST_REQUIREMENTS,
        ),
    tests_require=TEST_REQUIREMENTS,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
    ],
    zip_safe=True,
)

