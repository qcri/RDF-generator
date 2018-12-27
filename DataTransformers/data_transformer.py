import rdflib as rdf
import multiprocessing as mp
import pickle
from triples import *


class DataTransformer:
    """
    takes one data record and transforms it to a list of triples
    """
    def __init__(self, descriptor, out_queue=None, buffer_size=1000):
        self.descriptor = descriptor
        self.in_queue = mp.Queue()
        self.out_queue = out_queue
        self.buffer_size = buffer_size
        self.records_buffer = []
        self.runner = mp.Process(target=self.run, args=(self.in_queue, ))

    def run(self, in_queue):
        while True:
            msg = in_queue.get()
            message = pickle.loads(msg)

            if type(message) is EndMessage:
                self.out_queue.put(msg)
                break
            else:
                message = message if type(message) is list else [message]
                self.records_buffer += message

    def transform_records_if_needed(self):
        if len(self.records_buffer) >= self.buffer_size:
            triples = []
            for record in self.records_buffer:
                triple = self.transform(record)
                triples.append(triple)

            self.records_buffer = []
            self.forward_created_triples(triples)

    def transform(self, record):
        pass

    def forward_created_triples(self, triples):
        if len(triples) > 0:
            self.out_queue.put(pickle.dumps(triples))

    def start(self):
        self.runner.start()

    def connect_to_exporter(self, exporter):
        self.out_queue = exporter.input_queue

    def send_me_message(self, record):
        if record is not None:
            self.in_queue.put(pickle.dumps(record))

    def return_rdf_triples(self, triples):
        self.out_queue.put(pickle.dumps(triples))
