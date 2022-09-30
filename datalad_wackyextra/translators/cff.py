from collections import UserDict

class NoNoneDict(UserDict):
    """A dictionary which ignores setting when value is None

    The underlying "regular" dict can be obtained as `.data` attribute.
    """
    def __setitem__(self, key, item):
        if item is not None:
            super().__setitem__(key, item)


class CffTranslator:
    def __init__(self, metadata_record):
        self.metadata_record = metadata_record
        self.extracted_metadata = self.metadata_record["extracted_metadata"]

    def get_name(self):
        return self.extracted_metadata.get("title", "")  # obligatory, must be string

    def get_description(self):
        return self.extracted_metadata.get("abstract")

    def get_doi(self):
        """Get a single DOI for the dataset

        Note: CFF allows one or several DOIs stored in "identifiers" array,
        or a top-level "doi" field as a shorthand when there is just one.
        """
        # first, try the top-level doi
        if self.extracted_metadata.get("doi") is not None:
            return "https://doi.org/" + self.extracted_metadata.get("doi")
        
        # go through identifiers, stopping at the first doi
        identifiers = self.extracted_metadata.get("identifiers")
        if identifiers is not None:
            for identifier in identifiers:
                if identifier["type"] == "doi":
                    return "https://doi.org/" + identifier["value"]

        # finally, give up
        return None

    def get_license(self):
        """Get a license name and URL as expected by the catalog

        Note: CFF allows a string or list of spdx.org identifiers,
        and urls are expected only for non-standard licenses.

        TODO: We could include the spdx data as a json file
        for maximum correctness with names and urls.
        """
        cff_license = self.extracted_metadata.get("license")
        cff_url = self.extracted_metadata.get("license-url")
        if cff_license is None:
            cat_license = None
        elif isinstance(cff_license, str):
            # single license
            if cff_url is None:
                # generate a spdx.org url
                cff_url = "https://spdx.org/licenses/{}.html".format(cff_license)
            cat_license = {
                "name": cff_license,
                "url": cff_url
            }
        elif isinstance(cff_license, list):
            # multiple licenses
            cat_license = {
                "name": " OR ".join(cff_license),
                "url": cff_url if cff_url is not None else "",
            }
        return cat_license

    def get_authors(self):
        cat_authors = []
        for cff_author in self.extracted_metadata.get("authors"):
            author = NoNoneDict()  # include only properties actually present
            author["name"] = cff_author.get("name")  # in cff, defined for entity, not person
            author["givenName"] = cff_author.get("given-names")
            author["familyName"] = cff_author.get("family-names")
            author["email"] = cff_author.get("email")
            # note that we currently ignore name particle and name suffix from cff
            if cff_author.get("orcid") is not None:
                orcid = {"type": "ORCID", "identifier": cff_author.get("orcid")}
                # may need to strip the https://orcid.org part
                author["identifiers"] = [orcid]
            cat_authors.append(author.data)
        return cat_authors

    def get_keywords(self):
        return self.extracted_metadata.get("keywords")

    def get_publications(self):
        # TODO: get the content from the references field
        pass

    def get_extractors_used(self):
        mandatory_keys = [
            "extractor_name", "extractor_version",
            "extraction_parameter", "extraction_time",
        ]
        return [{k: self.metadata_record[k] for k in mandatory_keys}]

    def translate(self):
        
        translated_record = {
            "type": self.metadata_record["type"],
            "dataset_id": self.metadata_record["dataset_id"],
            "dataset_version": self.metadata_record["dataset_version"],
            "name": self.get_name(),
            "description": self.get_description(),
            "doi": self.get_doi(),
            "license": self.get_license(),
            "authors": self.get_authors(),
            "keywords": self.get_keywords(),
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
            if j["extractor_name"] == "we_cff":
                t = CffTranslator(j).translate()
                print(json.dumps(t))
