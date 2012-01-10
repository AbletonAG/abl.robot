import unittest
import tempfile

from configobj import ConfigObj
from turbomail.control import interface

#-------------------------------------------------------------------------------


class RobotTestCase(unittest.TestCase):
    """
    Special baseclass to test Robots.
    """

    ROBOT_CLASS = None
    """
    The class to instantiate. Override in subclasses.
    """


    @classmethod
    def get_messages(cls):
        if interface and interface.manager and interface.manager.transport: #@UndefinedVariable
            # transport is only available after at least one mail has been sent
            return interface.manager.transport.get_sent_mails() #@UndefinedVariable
        else:
            return []

    @classmethod
    def clear_messages(cls):
        if interface and interface.manager and interface.manager.transport: #@UndefinedVariable
            interface.manager.transport._sent_mails = []


    def start_robot(self,
                    opts={},
                    threaded=False,
                    nomail=False,
                    norun=False,
                    config=None,
                    commands=None,
                    robot_class=None
                    ):
        """
        Create a robot-instance.

        :param opts: a dictionary of options. Will be transformed to
                     commandline arguments. Each key is made to an option,
                     where a length of 1 makes a short option, and longer
                     a long one.

                     If a value is None, the option becomes a switch. Otherwise
                     the value is rendered.

                     Values can be lists.
        :type opts: dict

        :param threaded: if True, start the robot in threaded mode.
        :type threaded: bool

        :param nomail: if True, clear the `Robot.EXCEPTION_MAILING` before starting.
        :type nomail: boolean

        :param norun: if True, don't invoke run (either threaded or directly)
        :type norun: bool

        :param config: if given as dictionary, it will be written out as
                       `ConfigObj` and the resulting file passed as
                       --config-option.
        :type config: None|dict

        :param commands: list of callables; each function will be called
                         with the instanciated robot as argument.
        :type commands: None|[callable]

        :param robot_class: if given as a robot_class, take this instead
                            of ROBOT_CLASS class attribute

        :type robot_class: None|class
        """

        cm_opts = []

        if config is None:
            config = dict(mail=dict(transport="debug"))

        if config is not None:
            if not "mail" in config:
                config["mail"] = dict(transport="debug")
            cf = ConfigObj()
            cf.filename = tempfile.mktemp("robottestconfig")
            for key, value in config.iteritems():
                cf[key] = value
            cf.write()
            cm_opts.append("--config=%s" % cf.filename)
        for key, value in opts.iteritems():
            if len(key) == 1:
                name = "-" + key
            else:
                name = "--" + key
            name = name.replace("_", "-")
            # no-arg options
            if value is None:
                cm_opts.append(name)
            # arg options
            else:
                if isinstance(value, basestring):
                    value = [value]

                for v in value:
                    if isinstance(v, unicode):
                        v = v.encode("UTF-8")
                    if name.startswith("--"):
                        cm_opts.append("%s=%s" % (name, v))
                    else:
                        cm_opts.extend([name, v])


        robot_class = robot_class or self.ROBOT_CLASS
        robot = robot_class(argv=cm_opts)
        if commands is not None:
            for cmd in commands:
                cmd(robot)


        def _locking_context():
            @contextlib.contextmanager
            def nop():
                yield
            return nop()

        robot._locking_context = _locking_context
        if nomail:
            robot.EXCEPTION_MAILING = None
        if not norun:
            if threaded:
                t = threading.Thread(target=robot.run)
                t.setDaemon(True)
                t.start()
            else:
                robot.run()
        # FIXME-dir: remove this
        self.robot = robot
        return robot
