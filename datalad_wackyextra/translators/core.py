import jq

class MetaladCoreTranslator:
    """Translator for metalad_core

    Uses jq programs written by jsheunis for datalad-catalog workflow
    to translate some fields, but wraps them in a more verbose python logic.
    """
    def __init__(self, metadata_record):
        self.metadata_record = metadata_record
        self.extracted_metadata = self.metadata_record["extracted_metadata"]
        self.graph = self.extracted_metadata["@graph"]

    def get_name(self):
        """Return an empty string as name

        Name is not a property of a DataLad dataset, but it is required
        by the catalog. We return an empty string to satisfy validation.
        """
        return ""

    def get_url(self):
        program = (
            ".[]? | select(.[\"@type\"] == \"Dataset\") | "
            "[.distribution[]? | select(has(\"url\")) | .url]"
        )
        return jq.first(program, self.graph)

    def get_authors(self):
        program = (
            "[.[]? | select(.[\"@type\"]==\"agent\")] | "
            "map(del(.[\"@id\"], .[\"@type\"]))"
        )
        return jq.first(program, self.graph)

    def get_subdatasets(self):
        program = (
            ".[]? | select(.[\"@type\"] == \"Dataset\") | "
            "[.hasPart[]? | "
            "{\"dataset_id\": (.[\"identifier\"] // \"\" | "
            "sub(\"^datalad:\"; \"\")), \"dataset_version\": (.[\"@id\"] | "
            "sub(\"^datalad:\"; \"\")), \"dataset_path\": .[\"name\"], "
            "\"dirs_from_path\": []}]"
        )
        result = jq.first(program, self.graph)
        return result if len(result) > 0 else None

    def get_extractors_used(self):
        keys = [
            "extractor_name", "extractor_version",
            "extraction_parameter", "extraction_time",
            "agent_name", "agent_email",
        ]
        return [{k: self.metadata_record[k] for k in keys}]

    def translate(self):
        translated_record = {
            "type": self.metadata_record["type"],
            "dataset_id": self.metadata_record["dataset_id"],
            "dataset_version": self.metadata_record["dataset_version"],
            "name": self.get_name(),
            "url": self.get_url(),
            "authors": self.get_authors(),
            "subdatasets": self.get_subdatasets(),
            "extractors_used": self.get_extractors_used(),
        }
        return {k: v for k, v in translated_record.items() if v is not None}

if __name__ == "__main__":
    import json
    import sys
    
    fname = sys.argv[1]
    with open(fname) as jf:
        for line in jf:
            j = json.loads(line)
            if j["extractor_name"] == "metalad_core":  # & type==dataset
                t = MetaladCoreTranslator(j).translate()
                print(json.dumps(t))
