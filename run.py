import sys
from DataExporters.data_exporter import RDFExportFormats
from manager.transformation_manager import TransformationManager

if __name__ == "__main__":
    graph_iden = sys.argv[1] if len(sys.argv) > 1 else ""
    input_path = sys.argv[2] if len(sys.argv) > 2 else ""
    output_path = sys.argv[3] if len(sys.argv) > 3 else ""
    descriptor_path = sys.argv[4] if len(sys.argv) > 4 else ""
    export_format = sys.argv[5] if len(sys.argv) > 5 and RDFExportFormats.is_recognized_format(sys.argv[5]) else None
    parallelism = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].isdigit() else None
    inline_exporters = True if len(sys.argv) > 7 and sys.argv[7].lower() == 'true' else False
    buffer_size = int(sys.argv[8]) if len(sys.argv) > 8 and sys.argv[8].isdigit() else 1000

    trans_mngr = TransformationManager(graph_identifier=graph_iden,
                                       input_file=input_path,
                                       output_file=output_path,
                                       descriptor_file=descriptor_path,
                                       export_format=export_format,
                                       parallelism=parallelism,
                                       inline_exporters=True,
                                       buffer_size=buffer_size)
    trans_mngr.run()
