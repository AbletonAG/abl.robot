from setuptools import setup, find_packages


TEST_REQUIREMENTS = ["nose"]

setup(
    name = "abl.robot",
    version = "0.1.2",
    author = "Diez B. Roggisch",
    author_email = "diez.roggisch@ableton.com",
    description = "The Ableton Robot Framework, for writing daemons or commandline tools, with powerful features for error handling and logging.",
    license="MIT",
    packages=find_packages(exclude=['tests']),
    namespace_packages = ["abl"],
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

