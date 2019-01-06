import rdflib
from rdflib.namespace import RDF


class Message:
    def __init__(self, msg):
        self.message = msg


RDFTriples = list   # list of RDFTriple objects


class RDFTriple:
    def __init__(self, subj, pred, obj):
        self.subject = subj
        self.predicate = pred
        self.object = obj

    def to_tuple(self):
        return self.subject, self.predicate, self.object

    def __repr__(self):
        return '{} {} {}.'.format(self.subject, self.predicate, self.object)


class EndMessage(Message):
    pass


class Entity:
    def __init__(self, name, uri, en_type, descriptor):
        self.name = name
        self.uri = uri
        self.subj = self.__get_as_rdflib_node(uri)
        self.type = en_type
        self.descriptor = descriptor
        self.triples = []
        self.add_feature(RDF.type, en_type)

    def __repr__(self):
        return '{} {} {} {}.'.format(self.name, self.uri, self.type, len(self.triples))

    def add_triple(self, triple):
        self.triples.append(triple)

    def add_feature(self, predicate, object, object_type=None, object_data_type=None):
        subj = self.subj
        pred = self.__get_as_rdflib_node(predicate)
        obj = self.__get_as_rdflib_node(object, object_type, object_data_type)
        if all([x is not None for x in [subj, pred, obj]]):
            triple = RDFTriple(subj, pred, obj)
            self.add_triple(triple)

    def __get_as_rdflib_node(self, term, object_type=None, data_type=None):
        if term is not None:
            if object_type is None or object_type == 'entity':
                if Entity.__is_prefixed(term):
                    prefix, iden = Entity.__get_term_components(term)
                    ns = self.descriptor.get_namespace(prefix)
                    if ns is not None:
                        return ns[iden]
                else:
                    return rdflib.URIRef(term)
            else:   # in case of literals
                return rdflib.Literal(term, datatype=data_type)

    @staticmethod
    def __is_prefixed(term):
        return ':' in term and not (term.startswith('http:') or term.startswith('https:'))

    @staticmethod
    def __get_term_components(term):
        if Entity.__is_prefixed(term):
            comps = term.split(':')
            return comps[0], comps[1]
        else:
            return term