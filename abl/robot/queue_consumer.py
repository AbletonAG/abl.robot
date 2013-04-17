# encoding: utf-8

import json
import logging
import os
from textwrap import dedent
from signal import (
    SIGTERM,
    signal,
    )
import sys

from pika import (
    BasicProperties,
    BlockingConnection,
    ConnectionParameters,
    PlainCredentials,
    )
from raven.handlers.logging import SentryHandler

from .base import Robot


class QueueConsumerMeta(type):
    """
    Meta class to ease the creation of Robots that are rabbitmq consumers.
    The metaclass will create the class attributes for the robot that
    are dependend from the actual Robot name such as configuration names, etc.
    This will reduce boilerplate code in the actual Robot code.
    """

    def __new__(mcs, clsname, bases, clsdict):
        if clsname != 'QueueConsumer':
            lowername = clsname.lower()
            clsdict['NAME'] = clsname
            clsdict['CONFIG_NAME'] = '{}.conf'.format(lowername)
            clsdict['CONFIGSPECS'] = {
                lowername:dedent("""
                [{name}]
                rabbitmq_user = string(default=)
                rabbitmq_pw = string(default=)
                rabbitmq_host = string(default=localhost)
                rabbitmq_port = integer(default=5672)
                queue_name = string(default={name})
                sentry_dsn = string(default=)
                """.format(name=lowername)),
                'logging':dedent("""
                [logging]
                level= string(default=INFO)
                """),
            }


        return type.__new__(mcs, clsname, bases, clsdict)


class QueueConsumer(Robot):
    """
    A QueueConsumer is the baseclass for rabbitmq consumer robots.
    The consumer class need to provide an 'action' method that will act on a message.
    By default, the robot will listen on a queue who's name equals the lowercase classname.
    For example, RustyRupert will listen to a queue with the name 'rustyrupert'.
    If this is not what is needed, the configuration file needs an entry for the
    'queue_name'.
    It is assumed that the message is an JSON encoded dictionary.
    This dict is unpacked and given to an 'action' method.
    Example:

    from .queue_consumer import QueueConsumer

    class RustyRupert(QueueConsumer):

        def action(self, **kwargs):
            print kwargs


    is a fully working QueueConsumer Robot that will just work.

    The working model is the following:
    if the 'action' method raises an exception, the message is rejected and
    not requeued. If this is not what is desired, don't use this baseclass.
    """

    __metaclass__ = QueueConsumerMeta

    NEEDS_CONFIG = False
    EXCEPTION_MAILING = 'webteam@ableton.com'
    RAISE_EXCEPTIONS = True
    AUTHOR = 'webteam@ableton.com'


    def __init__(self, *args, **kwargs):
        super(QueueConsumer, self).__init__(*args, **kwargs)
        opts = self.merge_config_and_opts()

        self.is_processing = False
        self.stop_processing = False
        signal(SIGTERM, self.handle_sigterm)

        self.logger.info("Opening Queue with args: {}".format(opts))
        self.queue = RabbitQueue(queue_name=opts.queue_name,
                                 host=opts.rabbitmq_host,
                                 port=opts.rabbitmq_port,
                                 user=opts.rabbitmq_user,
                                 pw=opts.rabbitmq_pw,
                                 )
        if opts.sentry_dsn:
            handler = SentryHandler(opts.sentry_dsn)
            handler.setLevel(logging.ERROR)
            self.logger.addHandler(handler)


    def configure(self):
        """
        Do anything necessary before beginning the consumer loop
        """
        pass


    def work(self):
        self.logger.info("{} starting up.".format(self.NAME))
        self.configure()
        self.logger.info("{} ready to consume messages.".format(self.NAME))
        self.queue.start_consuming(self.consume)


    def consume(self, msg_body, ack):
        self.is_processing = True
        accepted = False
        try:
            msg = json.loads(msg_body)
            self.action(**msg)
        except KeyboardInterrupt:
            raise
        except Exception:
            self.logger.error("Error processing '%s'", msg_body, exc_info=True)
        else:
            accepted = True
        ack(accepted, disconnect_after_ack=self.stop_processing)
        if not accepted:
            sys.exit(1)
        self.is_processing = False

        if self.stop_processing:
            sys.exit(0)


    def action(self, **kwargs):
        raise NotImplementedError()


    def handle_sigterm(self, signum, frame):
        if self.is_processing:
            self.stop_processing = True
        else:
            sys.exit(0)



class DummyQueue(object):

    def __init__(self, initial_messages=None):
        if initial_messages is None:
            self.initial_messages = []
        else:
            self.initial_messages = initial_messages
        self.last_message = None
        self.acks = [False] * len(self.initial_messages)
        self.context_depth = 0


    def connect(self):
        pass


    def disconnect(self):
        pass


    def __enter__(self):
        if self.context_depth == 0:
            self.connect()
        self.context_depth += 1


    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.context_depth -= 1
        if self.context_depth == 0:
            self.disconnect()
        return False


    def push(self, data):
        self.last_message = data


    def start_consuming(self, callback):
        for idx, msg in enumerate(self.initial_messages):
            def ack():
                self.acks[idx] = True
            callback(msg, ack)


class RabbitQueue(DummyQueue):

    def __init__(self, queue_name=None, host='localhost', port=5672, user=None, pw=None):
        super(RabbitQueue, self).__init__()
        self.connection = None
        self.channel = None
        self.host = host
        self.port = port
        self.user = user
        self.pw = pw
        self.queue_name = queue_name


    def start_consuming(self, callback):
        """
        Callbacks receive two args, like so::

            def callback(body, ack):
                # Handle the message body.
                ... stuff ...

                # Call ack as a function to acknowledge the message:
                ack()

        """
        def amq_callback(channel, method, _header, body):
            def ack(accepted=True, disconnect_after_ack=False):
                if disconnect_after_ack:
                    channel.stop_consuming()
                if accepted:
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    channel.basic_reject(delivery_tag=method.delivery_tag,
                                         requeue=False)
            callback(body, ack)

        if not self.connection:
            self.connect()

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(amq_callback,
                                   queue=self.queue_name,
                                   no_ack=False)
        self.channel.start_consuming()


    def connect(self):
        credentials = PlainCredentials(
            self.user,
            self.pw,
            )
        params = ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            )
        self.connection = BlockingConnection(params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            )


    def disconnect(self):
        self.connection.close()
        self.connection.disconnect()
        self.connection = None


    def push(self, data):
        super(RabbitQueue, self).push(data)
        with self:
            # persistent message
            properties=BasicProperties(delivery_mode=2)
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=data,
                properties=properties,
                )
