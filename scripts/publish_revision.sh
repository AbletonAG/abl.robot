#!/usr/bin/env python2.7
import sys
import subprocess
import shutil
import os

if os.path.exists("dist"):
    shutil.rmtree("dist")

subprocess.call([sys.executable, "setup.py", "sdist"])

distname = os.listdir("dist")[0]

p = subprocess.Popen(
    ["ssh", "git-user@galaxy", "find", "/packages/", "-name", distname],
    stdout=subprocess.PIPE,
    )

out, _ = p.communicate()

out = out.strip()

if out:
    sys.stderr.write("""There seems to be a release of '%s' already!
I won't publish this revision.

Please update abl/relman/release_version.py, and dependent packages
such as abl.downloads.
""" % distname)
    sys.exit(1)


scp_cmd = ["scp", "dist/%s" % distname, "git-user@galaxy:/packages"]

print " ".join(scp_cmd)

subprocess.call(
    scp_cmd
    )
