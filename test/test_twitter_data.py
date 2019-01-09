from manager.transformation_manager import TransformationManager


def test_transform_twitter_data():
    # trans_mngr = TransformationManager(graph_identifier='http://twitter.com/',
    #                                    input_file='/Users/ghanemabdo/Work/DS/arabic-knowledge-base/rdf-generator/data/tbh-small-fixed.json',
    #                                    output_file='/Users/ghanemabdo/Work/DS/arabic-knowledge-base/rdf-generator/data/tbh-small.ttl',
    #                                    descriptor_file='/Users/ghanemabdo/Work/DS/arabic-knowledge-base/rdf-generator/descriptor.json',
    #                                    inline_exporters=False)
    trans_mngr = TransformationManager(graph_identifier='http://twitter.com/',
                                       input_file='/Users/ghanemabdo/Work/DS/arabic-knowledge-base/rdf-generator/data/tbh.json',
                                       output_file='/Users/ghanemabdo/Work/DS/arabic-knowledge-base/rdf-generator/data/tbh.ttl',
                                       descriptor_file='/Users/ghanemabdo/Work/DS/arabic-knowledge-base/rdf-generator/descriptor.json',
                                       inline_exporters=True)
    trans_mngr.run()

if __name__ == '__main__':
    test_transform_twitter_data()
