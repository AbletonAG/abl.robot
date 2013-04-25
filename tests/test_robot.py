# -*- coding: utf-8 -*-
#******************************************************************************
# (C) 2008 Ableton AG
#******************************************************************************
from __future__ import with_statement

__docformat__ = "restructuredtext en"

import os
import sys
import time
import threading
import logging
from functools import partial
import unittest
import contextlib
import tempfile
import subprocess
from textwrap import dedent

import shutil
from urllib import urlencode

from abl.robot import Robot
from abl.robot.test import RobotTestCase


from abl.vpath.base import URI


class BasicRobotTests(RobotTestCase):


    def test_exception_mailing(self):

        class FailBot(Robot):

            AUTHOR = "dir@ableton.com"
            EXCEPTION_MAILING = "dir@ableton.com"

            def work(self):
                raise Exception("Oh lord forgive me, I'm such an epic fail!")


        url = "http://view/that/error"

        error_log = tempfile.mkdtemp()
        try:
            config = dict(
                mail=dict(
                    transport="debug",
                    ),
                error_handler={
                    "error.viewer_url" : url,
                    "error.xml_dir" : error_log,
                    "mail.on" : "true",
                    }
                )

            self.clear_messages()
            self.start_robot(
                config=config,
                robot_class=FailBot,
                )

            messages = self.get_messages()
            assert messages
            assert url in messages[0]
            assert os.listdir(error_log)

            self.clear_messages()

            some_email = "nobody@ableton.invalid"
            config["error_handler"]["error.rcpt"] = some_email

            self.start_robot(config=config,
                             robot_class=FailBot,
                             )

            messages = self.get_messages()
            assert messages
            assert some_email in messages[0]
        finally:
            shutil.rmtree(error_log)



    def test_exception_raising(self):

        class Foo(Exception): pass

        class RaiseBot(Robot):

            AUTHOR = "dir@ableton.com"
            EXCEPTION_MAILING = "dir@ableton.com"

            def work(self):
                raise Foo

        config = dict(
            mail=dict(
                transport="debug",
                ),
            error_handler={
                "error.viewer_url" : "url",
                "error.xml_dir" : "error_log",
                "mail.on" : "true",
                },
            )
        self.clear_messages()
        self.failUnlessRaises(
            Foo,
            self.start_robot,
            config=config,
            robot_class=RaiseBot,
            argv=["--raise-exceptions"]
            )

    def test_configspec_matters(self):

        the_configs = []

        class ConfigBot(Robot):

            AUTHOR = "dir@ableton.com"
            EXCEPTION_MAILING = "dir@ableton.com"

            NEEDS_CONFIG = True

            CONFIGSPECS = dict(
                configbot=dedent("""
                [configbot]
                a=string(default=foo)
                b=integer(default=100)
                c=integer
                """
                                 )
                )

            def work(self):
                the_configs.append(self.config)

        config = dict(
            configbot=dict(
                c="100",
                )
            )

        self.start_robot(
            config=config,
            robot_class=ConfigBot,
        )
        assert the_configs
        config = the_configs[0]
        config = config["configbot"]
        self.assertEqual(config["a"], "foo")
        self.assertEqual(config["b"], 100)
        self.assertEqual(config["c"], 100)
