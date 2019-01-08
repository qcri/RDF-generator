import json, os

FILE_SIZE_STREAMING_THRESHOLD = 20 * 1024.0 * 1024.0


class JsonReader:

    def __init__(self, filepath):
        self.filepath = filepath

    @staticmethod
    def get_as_object(filepath):
        object_type = 0     #0 => wrong input, 1 => dictionary, 2 => list
        with open(filepath) as f:
            for line in f:
                line = line.strip()

                if len(line) > 0:
                    if line.startswith('{'):
                        object_type = 1
                    elif line.startswith('['):
                        object_type = 2
                    break
        if object_type == 1:
            return JsonReader.get_as_dict(filepath)
        elif object_type == 2:
            return JsonReader.get_as_list(filepath)
        else:
            return None

    @staticmethod
    def get_as_dict(filepath):
        with open(filepath, 'r') as f:
            try:
                return json.load(f)
            except Exception as ex:
                print(str(ex))

    @staticmethod
    def get_as_list(filepath):
        with open(filepath, 'r') as f:
            try:
                return json.load(f)
            except Exception as ex:
                print(str(ex))

    @staticmethod
    def get_as_dict_streamed(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        yield json.loads(line)
                except Exception as ex:
                    print(str(ex))

    @staticmethod
    def get_as_str(filepath):
        with open(filepath, 'r') as f:
            return f.read()

    @staticmethod
    def get_as_str_streamed(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('{') and line.endswith('}'):
                    yield line

    @staticmethod
    def should_be_streamed(filepath):
        return os.path.getsize(filepath) > FILE_SIZE_STREAMING_THRESHOLD
