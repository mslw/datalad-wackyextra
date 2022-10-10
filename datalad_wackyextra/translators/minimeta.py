import json

import jq

class MinimetaTranslator:
    """Translator for metalad_studyminimeta

    Uses jq programs written by jsheunis for datalad-catalog workflow
    to translate some fields, but introduces additional condition checks.
    Will not include empty values in its output.
    """
    def __init__(self, metadata_record):
        self.metadata_record = metadata_record
        self.extracted_metadata = self.metadata_record["extracted_metadata"]

        self.graph = self.extracted_metadata["@graph"]
        self.type_dataset = jq.first(
            ".[] | select(.[\"@type\"] == \"Dataset\")",
            self.graph,
        )
        self.combinedpersonsids = self._jq_first_or_none(
            program=(
                "{\"authordetails\": .[] | "
                "select(.[\"@id\"] == \"#personList\") | "
                ".[\"@list\"], \"authorids\": .[] | "
                "select(.[\"@type\"] == \"Dataset\") | .author}"
            ),
            entry=self.graph
        )
        self.combinedpersonspubs = self._jq_first_or_none(
            program=(
                "{\"authordetails\": .[] | "
                "select(.[\"@id\"] == \"#personList\") | "
                ".[\"@list\"], \"publications\": .[] | "
                "select(.[\"@id\"] == \"#publicationList\") | .[\"@list\"]}"
            ),
            entry=self.graph,
        )

    def _jq_first_or_none(self, program, entry):
        try:
            result = jq.first(program, entry)
        except StopIteration:
            result = None
        return result

    def get_name(self):
        return self.type_dataset.get("name", "")

    def get_description(self):
        return self.type_dataset.get("description")

    def get_url(self):
        return self.type_dataset.get("url")

    def get_keywords(self):
        return self.type_dataset.get("keywords")

    def get_authors(self):
        if self.combinedpersonsids is not None:
            program=(
                ". as $parent | [.authorids[][\"@id\"] as $idin | "
                "($parent.authordetails[] | select(.[\"@id\"] == $idin))]"
            )
            return jq.first(program, self.combinedpersonsids)
        return None

    def get_funding(self):
        program = (
            ".[] | select(.[\"@type\"] == \"Dataset\") | [.funder[]? | "
            "{\"name\": .name, \"identifier\": \"\", \"description\": \"\"}]"
        )
        result = jq.first(program, self.graph) #  [] if nothing found
        return result if len(result) > 0 else None


    def get_publications(self):
        if self.combinedpersonspubs is not None:
            program = (
                ". as $parent | [.publications[] as $pubin | "
                "{\"type\":$pubin[\"@type\"], "
                "\"title\":$pubin[\"headline\"], "
                "\"doi\":$pubin[\"sameAs\"], "
                "\"datePublished\":$pubin[\"datePublished\"], "
                "\"publicationOutlet\":$pubin[\"publication\"][\"name\"], "
                "\"authors\": ([$pubin.author[][\"@id\"] as $idin | "
                "($parent.authordetails[] | select(.[\"@id\"] == $idin))])}]"
            )
            return jq.first(program, self.combinedpersonspubs)
        else:
            return None

    def get_subdatasets(self):
        program = (
            ".[]? | select(.[\"@type\"] == \"Dataset\") | [.hasPart[]? | "
            "{\"dataset_id\": (.identifier | sub(\"^datalad:\"; \"\")), "
            "\"dataset_version\": (.[\"@id\"] | sub(\"^datalad:\"; \"\")), "
            "\"dataset_path\": .name, \"dirs_from_path\": []}]"
        )
        result = jq.first(program, self.graph) #  [] if nothing found
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
            "description": self.get_description(),
            "url": self.get_url(),
            "authors": self.get_authors(),
            "keywords": self.get_keywords(),
            "funding": self.get_funding(),
            "publications": self.get_publications(),
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
            if j["extractor_name"] == "metalad_studyminimeta":
                t = MinimetaTranslator(j).translate()
                print(json.dumps(t))
