"""
record different metrics in the transformation pipeline
"""
import multiprocessing as mp
import pickle
import os, sys
from triples import EndMessage


class TimeStampMessage:

    def __init__(self, thread_no, thread_type, ts_type, msg_time):
        self.thread_no = thread_no
        self.thread_type = thread_type
        self.type = ts_type
        self.time = msg_time


class TransformationBatchInfo:

    def __init__(self, trans_no, batch_no, records_count, triples_count):
        self.thread_no = trans_no
        self.batch_no = batch_no
        self.records_count = records_count
        self.triples_count = triples_count


class ExportationBatchInfo:

    def __init__(self, ex_no, batch_no, triples_count):
        self.thread_no = ex_no
        self.batch_no = batch_no
        self.triples_count = triples_count


class TransformationMetrics:
    """
    tracks and stores various transformation parameters such as start and end times, number of transformed records ... etc
    """
    def __init__(self, manager):
        """
        Initializing the metrics object with parameters from the transformation manager such as the number of
        transformer and exporter threads. It also creates the queue where all statistics message are passed to
        :param manager: TransformationManager object
        """
        self.stats_queue = mp.Queue()
        self.timestamps_msg_buffer = []
        self.transformers_msg_buffer = []
        self.exporters_msg_buffer = []
        self.manager = manager
        self.exporters_count = 1 if self.manager.inline_exporters else self.manager.parallelism
        self.finished_exporters = 0

    def run(self):
        """
        starts reading and processing the statistics messages from the queue and stores them in one of three buffers.
        Timestamps buffer: where all start and end signals are stored
        Transformation buffer: where all transformation statistics are stored
        Exportation buffer: where all exportation statistics are stored
        :return:
        """
        while True:
            msg = self.stats_queue.get()
            msg = pickle.loads(msg)

            if type(msg) is EndMessage:
                self.finished_exporters += 1
                if self.finished_exporters == self.exporters_count:
                    break
            elif type(msg) is TimeStampMessage:
                self.timestamps_msg_buffer.append(msg)
            elif type(msg) is TransformationBatchInfo:
                self.transformers_msg_buffer.append(msg)
            elif type(msg) is ExportationBatchInfo:
                self.exporters_msg_buffer.append(msg)
            else:
                pass

    def get_runtime(self, thread_type=None, thread_no=None):
        """
        returns the partial or overall runtime of the whole transformation process given some filtering criteria:
        thread_type: "transformer" for transformer threads only, "exporter" for exporter threads only, or None for overall
        thread_no: since the rdf generator is multithreaded, this returns the runtime for a particular thread
        :param thread_type: "transformer", "exporter", or None for overall
        :param thread_no: integer represents the index of the thread to retrieve the statistics for
        :return: the runtime as float
        """
        def time_sel_fn(ts_msg, type, default=sys.maxsize):
            if (thread_no is None or thread_no == ts_msg.thread_no) and \
               (thread_type is None or ts_msg.thread_type == thread_type) and \
               ts_msg.type == type:
                return ts_msg.time
            return default

        start_time = min(self.timestamps_msg_buffer, key=lambda ts_msg: time_sel_fn(ts_msg, 'start'))
        end_time = max(self.timestamps_msg_buffer, key=lambda ts_msg: time_sel_fn(ts_msg, 'end', -sys.maxsize-1))

        return end_time.time - start_time.time

    def get_transformation_stats(self, batch_no=None, thread_no=None):
        """
        returns the number of records consumed and triples generated by a particular thread and for a particular batch no
        or overall number of records and triples if None
        :param batch_no: the batch of records processed by a thread
        :param thread_no: the thread index
        :return: tuple(records count, triples count)
        """
        stats_msg = [info for info in self.transformers_msg_buffer if TransformationMetrics.__filter_stats(info, batch_no,
                                                                                                           thread_no)]

        return sum([info.records_count for info in stats_msg]), sum([info.triples_count for info in stats_msg])

    def get_exportation_stats(self, batch_no=None, thread_no=None):
        """
        returns the number of triples generated by a particular thread and for a particular batch no
        or overall number of triples if None
        :param batch_no: the batch of records processed by a thread
        :param thread_no: the thread index
        :return: triples count as int
        """
        stats_msg = [info for info in self.exporters_msg_buffer if TransformationMetrics.__filter_stats(info, batch_no,
                                                                                                        thread_no)]

        return sum([info.triples_count for info in stats_msg])

    def print_metrics(self):
        """
        print the run metrics to the console
        :return:
        """
        records_processed, triples_generated = self.get_transformation_stats()
        print('''
            Run metrics:
            ============
                total runtime: {} seconds
                transformation time: {} seconds
                exportation time: {} seconds
                total records processed: {}
                total triples generated: {}
                number of transformer threads: {}
                number of exporter threads: {}
                '''.format(self.get_runtime(),
                           self.get_runtime(thread_type='transformer'),
                           self.get_runtime(thread_type='exporter'),
                           records_processed,
                           triples_generated,
                           len(self.manager.transformers),
                           self.exporters_count))

    @staticmethod
    def __filter_stats(info, batch_no, thread_no):
        if (batch_no is None or info.thread_type == batch_no) and \
                (thread_no is None or info.thread_no == thread_no):
            return True
        return False

