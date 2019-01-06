"""
Handles tasks related to file formats. For ex. guessing import and export format from file extension
"""
from DataExporters.data_exporter import RDFExportFormats
from DataImporters.json_data_importer import ImportFormats


class FileFormatManager:

    ext_to_format = {
        'ttl': 'turtle',
        'xml': 'xml',
        'json': 'json'
    }

    @staticmethod
    def guess_export_format(ex_f_name):
        ex_format = FileFormatManager.__guess_format(ex_f_name)

        if ex_format is not None and ex_format in FileFormatManager.ext_to_format:
            return FileFormatManager.ext_to_format[ex_format]
        else:
            return RDFExportFormats.Turtle

    @staticmethod
    def __guess_input_format(im_f_name):
        ip_format = FileFormatManager.__guess_format(im_f_name)

        if ip_format is not None and ip_format in FileFormatManager.ext_to_format:
            return FileFormatManager.ext_to_format[ip_format]
        else:
            return ImportFormats.Json

    @staticmethod
    def __guess_format(filename):
        filename_components = filename.split('.')

        if len(filename) > 1:
            return filename_components[-1]
