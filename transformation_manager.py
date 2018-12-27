"""
connects the transformation pipeline stages together
"""
from DataImporters.json_data_importer import JsonDataImporter, ImportFormats
from DataTransformers.data_transformer import DataTransformer
from DataExporters.data_exporter import DataExporter, RDFExportFormats
from descriptor import Descriptor
from triples import EndMessage
import sys, os


class TransformationManager:
    """
    the orchestrator that builds different transformation modules, connects them and initiates the transformation
    """

    def __init__(self, graph_identifier, input_file, output_file, descriptor_file, export_format=None,
                 parallelism=None):
        """
        initializing the transformation manager with all the information needed to perform the whole transformation
        process
        :param graph_identifier: unique indentifier for the graph under processing
        :param input_file: the input file path
        :param output_file: the output file path
        :param descriptor_file: the descriptor json file
        :param export_format: the format used to export the generated graph. Default turtle
        :param parallelism: the number of transformation worker threads (Degree of parallelism)
        """
        self.graph_identifier = graph_identifier
        self.input_file = input_file
        self.output_file = output_file
        self.descriptor = Descriptor(descriptor_file)
        self.export_format = export_format if export_format is not None else self.__guess_export_format()
        self.importer = None
        self.transformers = []
        self.exporters = []
        self.parallelism = parallelism if parallelism is not None else max(os.cpu_count() - 1, 1)

        self.build_transformation_pipeline()

    def build_transformation_pipeline(self):
        self.importer = self.__create_importer()

        map(self.transformers.append(DataTransformer(self.descriptor)), range(self.parallelism))
        map(self.exporters.append(DataExporter(graph_iden=self.graph_identifier, filepath=self.output_file,
                                               export_format=self.export_format)),
            range(self.parallelism))
        map(lambda i, transformer: transformer.connect_to_exporter(self.exporters[i]), enumerate(self.transformers))

    def bootstrap_pipeline(self):
        map(lambda i: self.transformers[i].start(), range(self.parallelism))
        map(lambda i: self.exporters[i].start(), range(self.parallelism))

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
                chunck_start = i * chunck_size
                chunck_end = (i + 1) * chunck_size
                chunck = records_list[chunck_start: chunck_end]

                self.transformers[i].send_me_message(chunck)

        map(lambda transformer: transformer.send_me_message(EndMessage('END')), self.transformers)

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

    def __guess_export_format(self):
        ex_format = TransformationManager.__guess_format(self.output_file)
        return ex_format if ex_format is not None else RDFExportFormats.Turtle

    def __guess_input_format(self):
        ip_format = TransformationManager.__guess_format(self.input_file)
        return ip_format if ip_format is not None else ImportFormats.Json

    @staticmethod
    def __guess_format(filename):
        filename_components = filename.split('.')

        if len(filename) > 1:
            return filename_components[-1]
