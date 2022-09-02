import json

class RisTranslator:
    def __init__(self, metadata_record):
        self.metadata_record = metadata_record

    @staticmethod
    def _getOneOf(d, *args):
        for key in args:
            val = d.get(key)
            if val is not None:
                break
        return val

    def get_type(self, ref):
        type_map = {
            "JOUR": "Journal Article",
            "CHAP": "Book Section",
            "THES": "Thesis",
        }
        ris_abbrev = ref["type_of_reference"]
        return type_map.get(ris_abbrev, "Other ({})".format(ris_abbrev))

    def get_title(self, ref):
        return self._getOneOf(ref, "title", "primary_title")

    def get_doi(self, ref):
        doi = ref.get("doi")
        return "https://doi.org/" + doi if doi is not None else ""

    def get_date_published(self, ref):
        return self._getOneOf(ref, "year", "publication_year")

    def get_authors(self, ref):
        return [{"name": x} for x in self._getOneOf(ref, "authors", "first_authors")]

    def translate(self):
        refs = self.metadata_record["extracted_metadata"]["refs"]
        publications = []
        for ref in refs:
            publications.append(
                {
                    "type": self.get_type(ref),
                    "title": self.get_title(ref),
                    "doi": self.get_doi(ref),
                    "datePublished": self.get_date_published(ref),
                    "authors": self.get_authors(ref),
                }
            )
        translated_record = {
            "type": self.metadata_record["type"],
            "dataset_id": self.metadata_record["dataset_id"],
            "dataset_version": self.metadata_record["dataset_version"],
            "name": "",
            "publications": publications,
        }
        return translated_record


class NbibTranslator:
    def __init__(self, metadata_record):
        self.metadata_record = metadata_record

    def get_type(self, ref):
        """ Returns publication type.
        Note: MEDLINE/PubMed format allows several types, listed alphabetically
        (e.g. Journal Article; Research Support, Non-U.S. Gov't; Review)
        and nbib puts them in a list preserving order. PubMed's docs say that
        99% of citations contain one of the following: Journal Article,
        Letter, Editorial, News.
        """
        publication_types = ref.get("publication_types")
        common_types = ["Journal Article", "Letter", "Editorial", "News"]
        for t in common_types:
            if t in publication_types:
                return t
        return "Other ({})".format("; ".join(publication_types))

    def get_title(self, ref):
        return ref.get("title")

    def get_doi(self, ref):
        doi = ref.get("doi")
        return "https://doi.org/" + doi if doi is not None else ""

    def get_date_published(self, ref):
        dp = ref.get("publication_date")
        if dp is not None:
            # four-digit year should be first
            dp = dp.split(' ')[0]
        return dp

    def get_authors(self, ref):
        authors = []
        for author in ref.get("authors"):
            a = {"name": author.get("author")}
            try:
                names = {
                    "givenName": author["first_name"],
                    "familyName": author["last_name"],
                }
                a.update(names)
            except KeyError:
                pass
            # todo: try to add orcid
            authors.append(a)
        return authors

    def translate(self):
        refs = self.metadata_record["extracted_metadata"]["refs"]
        publications = []
        for ref in refs:
            publications.append(
                {
                    "type": self.get_type(ref),
                    "title": self.get_title(ref),
                    "doi": self.get_doi(ref),
                    "datePublished": self.get_date_published(ref),
                    "authors": self.get_authors(ref),
                }
            )
        translated_record = {
            "type": self.metadata_record["type"],
            "dataset_id": self.metadata_record["dataset_id"],
            "dataset_version": self.metadata_record["dataset_version"],
            "name": "",
            "publications": publications,
        }
        return translated_record


if __name__ == "__main__":
    import sys
    fname = sys.argv[1]
    with open(fname) as jf:
        for line in jf:
            j = json.loads(line)
            if j["extractor_name"] == "we_ris":
                t = RisTranslator(j).translate()
            elif j["extractor_name"] == "we_nbib":
                t = NbibTranslator(j).translate()
            print(json.dumps(t))
