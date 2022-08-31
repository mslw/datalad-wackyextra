import json

def translate_ris(metadata_record):
    refs = metadata_record["extracted_metadata"]["refs"]
    publications = []
    for ref in refs:
        publications.append(
            {
                "type": get_type(ref),
                "title": get_title(ref),
                "doi": get_doi(ref),
                "datePublished": get_date_published(ref),
                "authors": get_authors(ref),
            }
        )
    translated_record = {
        "type": metadata_record["type"],
        "dataset_id": metadata_record["dataset_id"],
        "dataset_version": metadata_record["dataset_version"],
        "name": "",
        "publications": publications,
    }
    return translated_record


def _getOneOf(d, *args):
    for key in args:
        val = d.get(key)
        if val is not None:
            break
    return val


def get_type(ref):
    type_map = {
        "JOUR": "Journal Article",
        "CHAP": "Book Section",
        "THES": "Thesis",
    }
    ris_abbrev = ref["type_of_reference"]
    return type_map.get(ris_abbrev, "Other ({})".format(ris_abbrev))


def get_title(ref):
    return _getOneOf(ref, "title", "primary_title")
    

def get_doi(ref):
    return ref.get("doi", "N/A")


def get_date_published(ref):
    return _getOneOf(ref, "year", "publication_year")


def get_authors(ref):
    return [{"name": x} for x in _getOneOf(ref, "authors", "first_authors")]


if __name__ == "__main__":
    with open("/home/mszczepanik/Documents/test-bib/output.json") as jf:
        j = json.load(jf)
        t = translate_ris(j)
        print(json.dumps(t))
