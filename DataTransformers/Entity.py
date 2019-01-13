import rdflib
from rdflib.namespace import RDF


class Message:
    def __init__(self, msg):
        self.message = msg


class PredicateFunction:
    def __init__(self, func_key, func, parameters):
        self.key = func_key
        self.func = func
        self.parameters = parameters

    def __repr__(self):
        return '{}({})'.format(self.key, str(self.parameters))


RDFTriples = list   # list of RDFTriple objects


class RDFTriple:
    """
    Class that wraps the components of an RDF triple (subject, predicate, object) because rdflib uses tuples
    """
    def __init__(self, subj, pred, obj):
        self.subject = subj
        self.predicate = pred
        self.object = obj

    def to_tuple(self):
        return self.subject, self.predicate, self.object

    def __repr__(self):
        return '{} {} {}.'.format(self.subject, self.predicate, self.object)


class EndMessage(Message):
    """
    used to signal that a process finished its work and shouting "I am done my business" :)
    """
    pass


class Entity:
    """
    Represents an entity created from an input record. It encapsulates all its properties and triples
    """
    def __init__(self, name, uri, en_type, descriptor):
        """
        Initializes the entity object by it's URI, name and rdf:type
        :param name: the entity given name in the descriptor
        :param uri: the entity's URI
        :param en_type: rdf:type of the entity
        :param descriptor: the descriptor used for the transformation process. It's needed to retrieve the uris of
        the prefixes used in the transformation process
        """
        self.name = name
        self.uri = uri
        self.subj = self.__get_as_rdflib_node(uri)
        self.type = en_type
        self.descriptor = descriptor
        self.triples = []
        self.add_property(RDF.type, en_type)

    def __repr__(self):
        return '{} {} {} {}.'.format(self.name, self.uri, self.type, len(self.triples))

    def add_triple(self, triple):
        self.triples.append(triple)

    def add_property(self, predicate, object, object_type=None, object_data_type=None, function=None):
        """
        add property to the entity. a property is defined in the descriptor under the 'properties' collection in the
        entity's object
        :param predicate: the rdf predicate used to represent this property. It could be prefixed or uri
        :param object: the object pointed to by the predicate. It could be literal or another entity
        :param object_type: 'entity' or 'literal'
        :param object_data_type: the data type of the object if the object is literal
        :param function: if the object is literal, apply the passed  PredicateFunction on it before creating
        its value in the rdflib node
        :return:
        """
        subj = self.subj
        pred = self.__get_as_rdflib_node(predicate)
        obj = self.__get_as_rdflib_node(object, object_type, object_data_type, function)
        if all([x is not None for x in [subj, pred, obj]]):
            triple = RDFTriple(subj, pred, obj)
            self.add_triple(triple)

    def __get_as_rdflib_node(self, term, object_type=None, data_type=None, function=None):
        """
        wraps the passed term in rdflib node
        :param term: uri or prefixed
        :param object_type: 'entity' or None to distinguish between uri nodes and literal nodes
        :param data_type: the data type of literal terms
        :param function: transformation function applied on literal objects before creating its rdflib node
        :return: rdflib node
        """
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
                if function is not None:
                    try:
                        if function.parameters is not None:
                            term = function.func(term, function.parameters)
                        else:
                            term = function.func(term)
                    except Exception as ex:
                        print('failed to convert {} to RDF format using {} with error {}'.format(term,
                                                                                                 str(function),
                                                                                                 str(ex)))

                return rdflib.Literal(term, datatype=data_type)

    @staticmethod
    def __is_prefixed(term):
        """
        checks if the passed uri is in prefixed format or a normal URI
        :param term: the term to check if prefixed
        :return: True if in prefix format or False if a normal URI
        """
        return ':' in term and not (term.startswith('http:') or term.startswith('https:'))

    @staticmethod
    def __get_term_components(term):
        """
        if the term is prefixed, this method returns a tuple (prefix, term_name) else returns the same URI
        :param term: the uri to decompose into prefix and term name if prefixed
        :return: tuple(prefix, term_name) if prefixed else term which is a normal URI
        """
        if Entity.__is_prefixed(term):
            comps = term.split(':')
            return comps[0], comps[1]
        else:
            return term
