# RDF-generator
Transforming structured (Tables) and semi-structured (Json & XML) data into RDF graphs.

The library takes in the following input:

* The input file path: this path points to the original data that needs to be converted to RDF graph
* The descriptor file path: path to the descriptor json file that contains the rules the library uses in order to convert the input to RDF graphs (the descriptor format is explained below)
* The output path: the output directory path used to save the generated RDF graphs. Since the library uses multiple threads to process the input, the output is saved to multiple graphs each one has maximum number of triples as defined in the GRAPH_MAX_SIZE variable

**Descriptor Format**

The transformation descriptor is the way you specify the rules that the transformer uses to convert the input data to the output RDF graphs. It is basically a json object that has the following hierarchy:

* ```prefixes```: json object whose keys are all the prefixes used in the conversion rules and the values are the prefix uris
* ```graph```: string value indicating the uri of the generated graph
* ```entities```: json object comprises all the entities to be generated from every input record. The keys are the entity names and the values are json objects that describes how each entity should be converted to RDF triples. Namely, how to build the entity's URI and assign different RDF properties to each property of this entity. The entity descriptor entry must have the following keys and values:

    * ```name```: the entity's assigned name (string).
    * ```uri_template```: the uri template used to build the entity's RDF URI. The uri template has one or more key paths that will be substituted from the input record.
    * ```type```: the RDF type that should be assigned to the generated entity. It could come in normal URI form (http://example.com/entity1) or in prefixed form (sioc:microblogPost) given the prefix is already listed in the prefixes section of the descriptor.
    * ```properties```: json object where each key/value pair represents an entity's property. The key is mainly a key path within the input record that is mapped to a list of potential RDF predicates that could be used to describe this property. The predicate itself is a json object that holds some information about this candidate RDF predicate:
        * ```predicate```: the RDF predicate URI either in normal form (http://example.com/predicate1) or prefixed form (sioc:id)
        * ```score```: float value ranges from 0 -> 1 that reflects how good the semantic of this candidate predicate in representing this property.
        * ```data_type```: if the matched value of this predicate (object) is RDF Literal, what should be the RDF data type assigned to it (for example xsd:string).
        * ```object_type```: the type of the object in this property that could be either "entity", "literal" or "blank node" (not supported yet).
        * ```apply_function```: some transformation function defined in a separate module to be applied on literal objects before storing them in the rdf graph
            * ```module```: python module name as string points to where the function is defined. For example 'utils.convenience'
            * ```name```: the function name. For example 'convert_to_rdf_datetime'
            * ```parameters```: dictionary of parameters to pass to the function in addition to the object value. For example the conversion format

Note: in case of referencing list objects with key paths, there are two options either to select a particular item in the list with the [index] or all items in the list with [*]. For example, to include all hashtags in a tweet, we reference it with property key path '/entities/hashtags/\[*\]'. iIf only one tweet is needed, it can be referenced with '/entities/hashtags/\[0\]'

Sample descriptor that is used to transform twitter json data into RDF graphs:
```
{
	"prefixes":{
		"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
		"sioc": "http://sioc.com/#",
		"sioct": "http://rdfs.org/sioc/types#",
		"to": "http://twitter.com/ontology/",
		"dcterms": "http://purl.org/dc/terms/",
		"xsd": "http://www.example.org/",
		"foaf": "http://xmlns.com/foaf/0.1/",
		"twitter": "http://twitter.com/"
	},
	"graph": "http://twitter.com",
	"entities": {
		"tweep": {
			"name": "tweep",
			"uri_template": "http://twitter.com/{/user/screen_name}",
			"type": "sioc:UserAccount",
			"path": "/user/",
			"properties": {
				"/user/id_str": [{"predicate": "sioc:id", "score": 1.0, "data_type": "xsd:ID", "object_type": "literal"}],
				"/user/screen_name": [{"predicate": "sioc:name", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/user/name": [{"predicate": "foaf:name", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/user/created_at": [{"predicate": "dcterms:created", "score": 1.0, "data_type": "xsd:dateTime", "object_type": "literal", "apply_function": {"name": "convert_to_rdf_datetime", "module": "utils.convenience"}}],
				"/user/description": [{"predicate": "sioc:description", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/user/profile_image_url": [{"predicate": "sioc:avatar", "score": 1.0, "data_type": "xsd:URI", "object_type": "literal"}],
				"/user/lang": [{"predicate": "dcterms:language", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/user/location": [{"predicate": "to:locatedin", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/user/verified": [{"predicate": "to:verified", "score": 1.0, "data_type": "xsd:Boolean", "object_type": "literal"}],
				"/user/protected": [{"predicate": "to:protected", "score": 1.0, "data_type": "xsd:Boolean", "object_type": "literal"}],
				"/user/followers_count": [{"predicate": "to:numfollowers", "score": 1.0, "data_type": "xsd:nonNegativeInteger", "object_type": "literal"}],
				"/quoted_status/user": [{"predicate": "to:quoted", "score": 1.0, "data_type": "sioc:UserAccount", "object_type": "entity", "substitutions": {"/user/screen_name": "/quoted_status/user/screen_name", "/id_str": "/quoted_status/user/id_str"}}]
			}
		},
		"tweet": {
			"name": "tweet",
			"uri_template": "http://twitter.com/{/user/screen_name}/status/{/id_str}",
			"type": "sioct:microblogPost",
			"path": "/",
			"properties": {
				"/id_str": [{"predicate": "sioc:id", "score": 1.0, "data_type": "xsd:ID", "object_type": "literal"}],
				"/user/": [{"predicate": "sioc:has_creator", "score": 1.0, "data_type": "sioc:UserAccount", "object_type": "entity", "substitutions": {"/user/screen_name": ""}}],
				"/created_at": [{"predicate": "dcterms:created", "score": 1.0, "data_type": "xsd:dateTime", "object_type": "literal", "apply_function": {"name": "convert_to_rdf_datetime", "module": "utils.convenience"}}],
				"/text": [{"predicate": "sioc:content", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/lang": [{"predicate": "dcterms:language", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/place/": [{"predicate": "to:locatedin", "score": 1.0, "data_type": "to:Location", "object_type": "entity", "substitutions": {"/place/id": ""}}],
				"/source": [{"predicate": "to:device", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/entities/hashtags/[*]": [{"predicate": "to:hashashtag", "score": 1.0, "data_type": "to:Hashtag", "object_type": "entity", "substitutions": {"/entities/hashtags/[*]text": ""}}],
				"/entities/user_mentions/[*]": [{"predicate": "sioc:mentions", "score": 1.0, "data_type": "sioc:UserAccount", "object_type": "entity", "substitutions": {"/user/screen_name": "/entities/user_mentions/[*]/screen_name"}}],
				"/entities/media/[*]": [{"predicate": "to:hasmedia", "score": 1.0, "data_type": "to:Multimedia", "object_type": "entity", "substitutions": {"/entities/media/[*]/expanded_url": ""}}],
				"/extended_entities/media/[*]": [{"predicate": "to:hasmedia", "score": 1.0, "data_type": "to:Multimedia", "object_type": "entity", "substitutions": {"/entities/media/[*]/expanded_url": "/extended_entities/media/[*]/expanded_url"}}],
				"/entities/urls/[*]": [{"predicate": "sioc:links_to", "score": 1.0, "data_type": "xsd:anyURI", "object_type": "literal"}],
				"/": [{"predicate": "to:isreplyto", "score": 1.0, "data_type": "sioct:microblogPost", "object_type": "entity", "substitutions": {"/user/screen_name": "/in_reply_to_screen_name", "/id_str": "/in_reply_to_status_id_str"}}],
				"/quoted_status": [{"predicate": "to:isquotedfrom", "score": 1.0, "data_type": "sioct:microblogPost", "object_type": "entity", "substitutions": {"/user/screen_name": "/quoted_status/user/screen_name", "/id_str": "/quoted_status/user/id_str"}}],
				"/retweeted_status": [{"predicate": "to:isretweetof", "score": 1.0, "data_type": "sioct:microblogPost", "object_type": "entity", "substitutions": {"/user/screen_name": "/retweeted_status/user/screen_name", "/id_str": "/retweeted_status/id_str"}}]
			}
		},
		"hashtag": {
			"name": "hashtag",
			"uri_template": "http://twitter.com/hashtag#{/entities/hashtags/[*]text}",
			"type": "to:Hashtag", 
			"path": "/entities/hashtags/[*]",
			"properties": {
				"/entities/hashtags/[*]/text": [{"predicate": "to:hastext", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}]			
			}
		},
		"mmresource": {
			"name": "mmresource",
			"uri_template": "{/entities/media/[*]/expanded_url}",
			"type": "to:Multimedia",
			"path": ["/entities/media/[*]", "/extended_entities/media/[*]"],
			"properties": {
				"/entities/media/[*]/type": [{"predicate": "to:multimediatype", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/entities/media/[*]/id": [{"predicate": "sioc:id", "score": 1.0, "data_type": "xsd:ID", "object_type": "literal"}],
				"/entities/media/[*]/media_url_https": [{"predicate": "sioc:link", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}]
			}
		},
		"location": {
			"name": "location",
			"uri_template": "http://twitter.com/location#{/place/id}",
			"type": "to:Location",
			"path": "/place/id",
			"properties": {
				"/place/full_name": [{"predicate": "to:full_name", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/place/url": [{"predicate": "to:url", "score": 1.0, "data_type": "xsd:anyURI", "object_type": "literal"}],
				"/place/country": [{"predicate": "to:country", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/place/place_type": [{"predicate": "to:place_type", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/place/country_code": [{"predicate": "to:country_code", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/place/id": [{"predicate": "to:id", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}],
				"/place/name": [{"predicate": "to:name", "score": 1.0, "data_type": "xsd:string", "object_type": "literal"}]
			}
		}
	}
}
```

**Using RDF-generator library:**

First, install the required python packages

```
pip install -r requirements.txt
```

Then, run the library

```
python run.py graph_identifier input_path output_path descriptor_path export_format number_of_threads inline_exporters buffer_size
```

*Parameters description:*

    * graph_identifier: the graph uri assigned to the generated RDF graph
    * input_path: path to the input data file
    * output_path: path to the output directory where the generated file will be placed
    * descriptor_path: path to the descriptor file (must be json in the format mentioned above)
    * export format: the exportation format. It should be one of the following formats [Turtle, XML, PRETTYXML, N3, NT, TRIG, TRIX, NQUADS]
    * number_of_threads: to leverage multicore host machines, this parameter is to tell the transformer how many parallel threads to use in order to process the input data
    * inline_exporters: False to create a separate thread for the export modules (good when processing large data in order not to block the transformation threads)
    * buffer_size: the size of the buffer used to batch sending records and triples between the data importer, the transformer and exporter processes (tune to gain performance boost)


For example to transform twitter data to turtle:
```
python run.py http://twitter.com/graph path/to/input/file.json path/to/output/file.ttl path/to/descriptor.json turtle 8 False 1000
```

Happy transformation!
