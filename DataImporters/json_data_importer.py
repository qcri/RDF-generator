from json_object import JsonReader


class ImportFormats:
    Json = 'json'
    XML = 'xml'


class JsonDataImporter:
    """
    This class imports a list of json data into the transformation pipeline
    """
    def __init__(self, filepath):
        self.filepath = filepath
        self.is_streamed = JsonReader.should_be_streamed(filepath)

    def get_records(self):
        """
        retrieve the json data from an input file
        :return: if streamed a records generator, if not a list of all records
        """
        if self.is_streamed:
            return JsonReader.get_as_dict_streamed(self.filepath)
        else:
            return JsonReader.get_as_object(self.filepath)
