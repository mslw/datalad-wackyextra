import jq

class DataciteTranslator:
    """Translator for datacite_gin

    Uses jq programs written by jsheunis for datalad-catalog workflow
    to translate some fields. Will not include empty values in its output.
    """

    def __init__(self, metadata_record):
        self.metadata_record = metadata_record
        self.extracted_metadata = self.metadata_record["extracted_metadata"]

    def get_name(self):
        return self.extracted_metadata.get("title", "")

    def get_description(self):
        return self.extracted_metadata.get("description")

    def get_license(self):
        program = ".license | { \"name\": .name, \"url\": .url}"
        result = jq.first(program, self.extracted_metadata)
        # todo check for license info missing
        return result if len(result) > 0 else None

    def get_authors(self):
        program = (
            "[.authors[]? | "
            "{\"name\":\"\", \"givenName\":.firstname, \"familyName\":.lastname"
            ", \"email\":\"\", \"honorificSuffix\":\"\"} "
            "+ if has(\"id\") then {\"identifiers\":[ "
            "{\"type\":(.id | tostring | split(\":\") | .[0]),"
            " \"identifier\":(.id | tostring | split(\":\") | .[1])}]} "
            "else null end]"
        )
        result = jq.first(program, self.extracted_metadata)
        return result if len(result) > 0 else None

    def get_keywords(self):
        return self.extracted_metadata.get("keywords")

    def get_funding(self):
        program = (
            "[.funding[]? as $element | "
            "{\"name\": $element, \"identifier\": \"\", \"description\": \"\"}]"
        )
        result = jq.first(program, self.extracted_metadata)
        return result

    def get_publications(self):
        program = (
            "[.references[]? as $pubin | "
            "{\"type\":\"\", "
            "\"title\":$pubin[\"citation\"], "
            "\"doi\":"
            "($pubin[\"id\"] | sub(\"(?i)doi:\"; \"https://doi.org/\")), "
            "\"datePublished\":\"\", "
            "\"publicationOutlet\":\"\", "
            "\"authors\": []}]"
        )
        result = jq.first(program, self.extracted_metadata)
        return result

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
            "description": self.get_description(),
            "authors": self.get_authors(),
            "keywords": self.get_keywords(),
            "funding": self.get_funding(),
            "publications": self.get_publications(),
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
            if j["extractor_name"] == "datacite_gin":
                t = DataciteTranslator(j).translate()
                print(json.dumps(t))
