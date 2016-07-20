# -*- coding: utf-8 -*-
#******************************************************************************
# (C) 2008 Ableton AG
#******************************************************************************
from __future__ import with_statement

__docformat__ = "restructuredtext en"

import os
import tempfile
from logging import DEBUG,  Handler
from textwrap import dedent

import shutil

from abl.robot import Robot
from abl.robot.test import RobotTestCase


class BasicRobotTests(RobotTestCase):


    def test_exception_mailing(self):

        class FailHandler(Handler):
            def __init__(self, *args, **kwargs):
                super(FailHandler, self).__init__(*args, **kwargs)
                self.records = []

            def emit(self, record):
                self.records.append(record)


        class FailBot(Robot):

            AUTHOR = "robot@example.com"
            EXCEPTION_MAILING = "robot@example.com"

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
                raise_exceptions=False
                )

            messages = self.get_messages()
            assert messages
            assert url in messages[0]
            assert os.listdir(error_log)

            self.clear_messages()
            shutil.rmtree(error_log)

            some_email = "nobody@ableton.invalid"
            config["error_handler"]["error.rcpt"] = some_email

            robot = self.start_robot(config=config,
                                     robot_class=FailBot,
                                     raise_exceptions=False,
                                     norun=True,
                                    )
            hdlr = FailHandler()
            robot.logger.addHandler(hdlr)
            robot.run()

            messages = self.get_messages()
            assert messages
            assert some_email in messages[0]
            self.assertEqual(hdlr.records[0].msg, 'An unhandled exception occured.')

        finally:
            shutil.rmtree(error_log)



    def test_exception_raising(self):

        class Foo(Exception): pass

        class RaiseBot(Robot):

            AUTHOR = "robot@example.com"
            EXCEPTION_MAILING = "robot@example.com"

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

            AUTHOR = "robot@example.com"
            EXCEPTION_MAILING = "robot@example.com"

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
