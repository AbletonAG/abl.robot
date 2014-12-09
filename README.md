# abl.robot

Provides configuration management and error reporting infrastructure
for cronjobs and asynchronous services.

## Running tests

Tests can be run via nose (`pip install nose`):

    nosetests

## How to release a new version

This package uses versioneer to manage version numbers.

When you are developing on your branch, running sdist will create
tarballs with versions like:

    2.2.15-3-g123456

When you actually want a new real, actual, numbered version, do this:

* Make sure all tests pass
* Make a pull request, get it reviewed, and merged back to master
* checkout master and pull so you are looking at the HEAD of master
* `git tag <your_new_version_number>`
* `git push --tags`

Now when you run sdist the version number will be whatever you
specified.

**Running `git push --tags` is super important. If you don't, nobody
else will be able to figure out where your version came from,
version numbers will get weird, and we will be sad.**

## License

abl.robot is distributed under the MIT license (see LICENSE).
