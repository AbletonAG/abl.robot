# encoding: utf-8

from unittest import TestCase

from abl.robot.queue_consumer import DummyQueue


def my_callback(body, ack):
    ack()


class DummyQueueTests(TestCase):
    def test_can_ack_in_callback(self):
        queue = DummyQueue([1, 2, 3])
        queue.start_consuming(my_callback)
        self.assertTrue(all(queue.acks))
