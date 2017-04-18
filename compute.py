import os
import time
import random

import six
from six.moves import _thread

import txaio
txaio.use_twisted()

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread

from autobahn.util import utcnow
from autobahn.wamp.types import RegisterOptions
from autobahn.wamp.types import ComponentConfig
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError

import argparse
import itertools

import networkx as nx

from neurokernel.tools.logging import setup_logger
import neurokernel.core_gpu as core

from neurokernel.LPU.LPU import LPU

from neurokernel.LPU.InputProcessors.StepInputProcessor import StepInputProcessor
from neurokernel.LPU.InputProcessors.FileInputProcessor import FileInputProcessor
from neurokernel.LPU.OutputProcessors.FileOutputProcessor import FileOutputProcessor

import argparse
import time
import txaio

txaio.use_twisted()

import neurokernel.mpi_relaunch

def do_compute(call_no, user):#delay,user,network_graph,network_input):
    started = utcnow()
    process_id = os.getpid()
    thread_id = _thread.get_ident()

    # TODO: move this to Config
    dt = 1e-4
    dur = 1.0
    steps = int(dur/dt)

    file_name = '%(user)s_%(process).log' % {'user':user,'process':process_id}

    screen = True # TODO: Remove
    logger = setup_logger(file_name=file_name, screen=screen)

    man = core.Manager()

    # TODO: Pass in network graph
    (comp_dict, conns) = LPU.lpu_parser('./data/generic_lpu.gexf.gz')

    # TODO: Set output for user and Job
    fl_input_processor = FileInputProcessor('./data/generic_input.h5')

    # TODO: Config input, spiking output or trace
    fl_output_processor = FileOutputProcessor([('V',None),('spike_state',None)], 'new_output.h5', sample_interval=1)

    man.add(LPU, 'ge', dt, comp_dict, conns,
        device=0, input_processors = [fl_input_processor],
        output_processors = [fl_output_processor], debug=args.debug)

    man.spawn()
    man.start(steps=steps)
    man.wait()
    time.sleep(5)

    ended = utcnow()

    # TODO: Remove Graph
    # TODO: Remove Input
    # TODO: Read in output

    result = {
        u'call_no': call_no,
        u'started': started,
        u'ended': ended,
        u'process': process_id,
        u'thread': thread_id
    }

    return result




class ComputeKernel(ApplicationSession):

    @inlineCallbacks
    def onJoin(self, details):
        self._max_concurrency = 1#self.config.extra[u'concurrency']
        self._current_concurrency = 0
        self._invocations_served = 0

        # adjust the background thread pool size
        reactor.suggestThreadPoolSize(self._max_concurrency)

        yield self.register(self.compute,
                            u'ffbo.sharc.compute',
                            options=RegisterOptions(invoke=u'roundrobin',
                                                    concurrency=self._max_concurrency))

        self.log.info('ComputeKernel ready with concurrency {}!'.format(self._max_concurrency))

    @inlineCallbacks
    def compute(self, call_no, delay):
        self._invocations_served += 1
        self._current_concurrency += 1
        self.log.info('starting compute() on background thread (current concurrency {current_concurrency} of max {max_concurrency}) ..', current_concurrency=self._current_concurrency, max_concurrency=self._max_concurrency)

        # now run our compute kernel on a background thread from the default Twisted reactor thread pool ..
        res = yield deferToThread(do_compute, call_no, delay)

        self._current_concurrency -= 1
        self.log.info('compute() ended from background thread ({invocations} invocations, current concurrency {current_concurrency} of max {max_concurrency})', invocations=self._invocations_served, current_concurrency=self._current_concurrency, max_concurrency=self._max_concurrency)

        returnValue(res)

    # Publish a Max and Current Conncurrency and Current Queue Size



if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output.')
    parser.add_argument('--router', type=six.text_type, default=u'ws://143.167.54.127:8080/ws', help='WAMP router URL.')
    parser.add_argument('--realm', type=six.text_type, default=u'realm1', help='WAMP router realm.')

    args = parser.parse_args()

    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    config = ComponentConfig(args.realm, extra={})

    session = ComputeKernel(config)

    runner = ApplicationRunner(args.router, args.realm)

    runner.run(session, auto_reconnect=True)
