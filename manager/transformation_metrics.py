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
    def __init__(self, exporters_count):
        self.stats_queue = mp.Queue()
        self.timestamps_msg_buffer = []
        self.info_msg_buffer = []
        self.exporters_msg_buffer = []
        self.exporters_count = exporters_count
        self.finished_exporters = 0

    def run(self):
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
                self.info_msg_buffer.append(msg)
            elif type(msg) is ExportationBatchInfo:
                self.exporters_msg_buffer.append(msg)
            else:
                pass

    def get_runtime(self, thread_type=None, thread_no=None):

        def time_sel_fn(ts_msg, type, default=sys.maxsize):
            if (thread_no is None or thread_no == ts_msg.thread_no) and \
               (thread_type is None or ts_msg.thread_type == thread_type) and \
               ts_msg.type == type:
                return ts_msg.time
            return default

        start_time = min(self.timestamps_msg_buffer, key=lambda ts_msg: time_sel_fn(ts_msg, 'start'))
        end_time = max(self.timestamps_msg_buffer, key=lambda ts_msg: time_sel_fn(ts_msg, 'end', -sys.maxsize-1))

        return end_time - start_time

    def get_transformation_stats(self, batch_no=None, thread_no=None):

        return TransformationMetrics.__get_stats(self.info_msg_buffer, batch_no, thread_no)

    def get_exportation_stats(self, batch_no=None, thread_no=None):
        return TransformationMetrics.__get_stats(self.exporters_msg_buffer, batch_no, thread_no)

    @staticmethod
    def __get_stats(buffer, batch_no=None, thread_no=None):
        stats_msg = [info for info in buffer if TransformationMetrics.__filter_stats(info,
                                                                                     batch_no,
                                                                                     thread_no)]

        return sum([info[0] for info in stats_msg]), sum([info[1] for info in stats_msg])

    @staticmethod
    def __filter_stats(info, batch_no, thread_no):
        if (batch_no is None or info.thread_type == batch_no) and \
                (thread_no is None or info.thread_no == thread_no):
            return True
        return False

