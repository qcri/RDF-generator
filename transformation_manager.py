"""
connects the transformation pipeline stages together
"""
from DataImporters.json_data_importer import JsonDataImporter
from DataTransformers.data_transformer import DataTransformer
from DataExporters.data_exporter import DataExporter
from utils.file_format_manager import FileFormatManager
from descriptor import Descriptor
from triples import EndMessage
import sys, os, math


class TransformationManager:
    """
    the orchestrator that builds different transformation modules, connects them and initiates the transformation
    """

    def __init__(self, graph_identifier, input_file, output_file, descriptor_file, export_format=None,
                 parallelism=None, inline_exporters=False, buffer_size=1000):
        """
        initializing the transformation manager with all the information needed to perform the whole transformation
        process
        :param graph_identifier: unique indentifier for the graph under processing
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
        self.exporters = []
        self.parallelism = parallelism if parallelism is not None else max(os.cpu_count() - 1, 1)

        self.build_transformation_pipeline()

    def build_transformation_pipeline(self):
        self.importer = self.__create_importer()

        self.transformers = [DataTransformer(self) for _ in range(self.parallelism)]

        if self.inline_exporters:
            exporter = DataExporter(self)
            self.exporters.append(exporter)
            map(lambda transformer: transformer.connect_to_exporter(exporter), self.transformers)
        else:
            self.exporters = [DataExporter(self, i) for i in range(self.parallelism)]
            for i, transformer in enumerate(self.transformers):
                transformer.connect_to_exporter(self.exporters[i])

    def bootstrap_pipeline(self):
        for i in range(self.parallelism):
            self.transformers[i].start()
            self.exporters[i].start()

    def run(self):
        self.bootstrap_pipeline()

        if self.importer.is_streamed:
            thread_turn = 0

            for record in self.importer.get_records():
                self.__process_record(thread_turn, record)
                thread_turn += 1

        else:
            records_list = self.importer.get_records()
            chunck_size = len(records_list) / len(self.transformers)

            for i in range(len(self.transformers)):
                chunck_start = int(i * chunck_size)
                chunck_end = int(math.ceil((i + 1) * chunck_size))
                chunck = records_list[chunck_start: chunck_end]
                print('chunck {} starts at {} ends at {}'.format(i, chunck_start, chunck_end))

                self.transformers[i].send_me_message(chunck)

        for transformer in self.transformers:
            transformer.send_me_message(EndMessage('END'))

    def __process_record(self, turn, record):
        """
        in round robin turn, send records to transformer processes
        :param turn: the turn counter to choose which process to send this record to
        :param record: the record to process
        :return: None
        """
        transformer_idx = turn % len(self.transformers)
        self.transformers[transformer_idx].send_me_message(record)

    def __create_importer(self):
        ip_file_type = self.input_file.split('.')[-1]
        # TODO: create and return other importers types here
        if ip_file_type == 'json':
            return JsonDataImporter(self.input_file)
