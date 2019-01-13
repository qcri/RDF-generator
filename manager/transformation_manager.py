"""
connects the transformation pipeline stages together
"""
import math
import os
import pickle
import time

from DataExporters.data_exporter import DataExporter
from DataImporters.json_data_importer import JsonDataImporter
from DataTransformers.data_transformer import DataTransformer
from DataTransformers.Entity import EndMessage
from descriptor import Descriptor
from manager.transformation_metrics import TransformationMetrics, TimeStampMessage
from utils.file_format_manager import FileFormatManager


class TransformationManager:
    """
    the orchestrator that builds different transformation modules, connects them and initiates the transformation
    """

    def __init__(self, graph_identifier, input_file, output_file, descriptor_file, export_format=None,
                 parallelism=None, inline_exporters=False, buffer_size=1000):
        """
        initializing the transformation manager with all the information needed to perform the whole transformation
        process
        :param graph_identifier: unique identifier for the graph under processing
        :param input_file: the input file path
        :param output_file: the output file path
        :param descriptor_file: the descriptor json file
        :param export_format: the format used to export the generated graph. Default turtle
        :param parallelism: the number of transformation worker threads (Degree of parallelism)
        :param inline_exporters: whether to create exporters in a different process
        :param buffer_size: records buffer size before processing or passing over
        """
        self.graph_identifier = graph_identifier
        self.input_file = input_file
        self.output_file = output_file
        self.descriptor = Descriptor(descriptor_file)
        self.export_format = export_format if export_format is not None \
            else FileFormatManager.guess_export_format(self.output_file)
        self.inline_exporters = inline_exporters
        self.buffer_size = buffer_size
        self.importer = None
        self.transformers = []
        self.transformers_queues = []
        self.exporters = []
        self.parallelism = parallelism if parallelism is not None else max(os.cpu_count() - 1, 1)
        self.metrics_manager = TransformationMetrics(self)

        self.build_transformation_pipeline()

    def build_transformation_pipeline(self):
        """
        Builds the transformers and exporters objects and connects them together considering if the inline_exporters flag
        is set or not. If set, all transformers will have a copy of the exporter and no separate exporter process will
        be spawned. If not set, the exporters will be spawned in a separate process and triples are passed to them from
        transformers via multiprocessing.Queue
        :return:
        """
        self.importer = self.__create_importer()

        if self.inline_exporters:
            exporter = DataExporter(self, self.metrics_manager.stats_queue)
            self.exporters = exporter

        self.transformers = [DataTransformer(self, self.metrics_manager.stats_queue) for _ in range(self.parallelism)]
        self.transformers_queues = [[] for _ in range(self.parallelism)]

        if not self.inline_exporters:
            self.exporters = [DataExporter(self, self.metrics_manager.stats_queue) for i in range(self.parallelism)]
            for i, transformer in enumerate(self.transformers):
                transformer.connect_to_exporter(self.exporters[i])

    def bootstrap_pipeline(self):
        """
        starts the transformers and exporters processes
        :return:
        """
        for i in range(self.parallelism):
            self.transformers[i].start()
            if not self.inline_exporters:
                self.exporters[i].start()

    def run(self):
        """
        the entry point to run the whole pipeline logic starting by reading the records and then passing it to
        transformers in a round robin fashion
        :return:
        """
        self.metrics_manager.stats_queue.put(pickle.dumps(TimeStampMessage(0, None, 'start', time.time())))
        self.bootstrap_pipeline()

        if self.importer.is_streamed:
            thread_turn = 0

            for record in self.importer.get_records():
                self.__buffer_record(thread_turn, record)
                thread_turn += 1

        else:
            records_list = self.importer.get_records()
            chunck_size = len(records_list) / len(self.transformers)

            chunck_end = 0
            for i in range(len(self.transformers)):
                chunck_start = chunck_end
                chunck_end = int(math.ceil((i + 1) * chunck_size))
                chunck = records_list[chunck_start: chunck_end]
                print('chunck {} starts at {} ends at {}'.format(i, chunck_start, chunck_end - 1))

                self.transformers[i].send_me_message(chunck)

        for i, transformer in enumerate(self.transformers):
            self.__send_records(i)
            transformer.send_me_message(EndMessage('END'))

        self.metrics_manager.stats_queue.put(pickle.dumps(TimeStampMessage(0, None, 'end', time.time())))
        self.metrics_manager.run()
        self.metrics_manager.print_metrics()

    def __buffer_record(self, turn, record):
        """
        in round robin turn, buffer records to transformer queues
        :param turn: the turn counter to choose which process to send this record to
        :param record: the record to process
        :return: None
        """
        transformer_idx = turn % len(self.transformers)
        self.transformers_queues[transformer_idx].append(record)

        if len(self.transformers_queues[transformer_idx]) > self.buffer_size:
            self.__send_records(transformer_idx)

    def __send_records(self, trans_idx):
        if len(self.transformers_queues[trans_idx]) > 0:
            self.transformers[trans_idx].send_me_message(self.transformers_queues[trans_idx])
            self.transformers_queues[trans_idx] = []

    def __create_importer(self):
        """
        based on the input file extension, the corresponding importer is created and used to import the records
        :return:
        """
        ip_file_type = self.input_file.split('.')[-1]
        # TODO: create and return other importers types here
        if ip_file_type == 'json':
            return JsonDataImporter(self.input_file)
