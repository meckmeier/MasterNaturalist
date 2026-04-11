from csv_importer import CSVImporter


def run_raw_import(upload, mapping):
    importer = CSVImporter(upload, mapping=mapping)

    importer.read()
    importer.normalize()
    importer.validate()

    return importer