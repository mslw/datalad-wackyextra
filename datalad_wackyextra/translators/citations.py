import json
from packaging import version
import re
from urllib.parse import urlparse

from datalad_catalog.translate import TranslatorBase

class CitationTranslator:
    """Base class for translators dealing with publications metadata

    Derived classes should implement the get_* methods to provide values
    in accordance with the datalad-catalog schema.
    """

    def __init__(self):
        self.metadata_record = None

    @staticmethod
    def _getOneOf(d, *args):
        """Helper to get first matching key with content from dict"""
        for key in args:
            val = d.get(key)
            if val is not None:
                break
        return val

    def get_type(self, ref):
        pass

    def get_title(self, ref):
        pass

    def get_doi(self, ref):
        pass

    def get_date_published(self, ref):
        pass

    def get_authors(self, ref):
        pass

    def get_publication_outlet(self, ref):
        pass

    def get_extractors_used(self):
        keys = [
            "extractor_name", "extractor_version",
            "extraction_parameter", "extraction_time",
            "agent_name", "agent_email",
        ]
        return [{k: self.metadata_record[k] for k in keys}]

    def get_metadata_source(self):
        result = {
            "key_source_map": {},
            "sources": [
                {
                    "source_name": self.metadata_record["extractor_name"],
                    "source_version": self.metadata_record["extractor_version"],
                    "source_parameter": self.metadata_record["extraction_parameter"],
                    "source_time": self.metadata_record["extraction_time"],
                    "agent_email": self.metadata_record["agent_email"],
                    "agent_name": self.metadata_record["agent_name"],
                }
            ],
        }
        return result

    def translate(self, metadata):
        self.metadata_record = metadata
        refs = self.metadata_record["extracted_metadata"]["refs"]
        publications = []
        for ref in refs:
            translated = {
                "type": self.get_type(ref),
                "title": self.get_title(ref),
                "doi": self.get_doi(ref),
                "datePublished": self.get_date_published(ref),
                "authors": self.get_authors(ref),
                "publicationOutlet": self.get_publication_outlet(ref),
            }
            publications.append(
                {k: v for k, v in translated.items() if v is not None}
            )
        translated_record = {
            "type": self.metadata_record["type"],
            "dataset_id": self.metadata_record["dataset_id"],
            "dataset_version": self.metadata_record["dataset_version"],
            "name": "",
            "publications": publications,
            "metadata_sources": self.get_metadata_source(),
        }
        return translated_record


class RisTranslator(CitationTranslator, TranslatorBase):

    @classmethod
    def match(cls, source_name, source_version, source_id=None):
        if source_id is not None:
            if source_id != "81076796-4e6e-428b-b5c2-79ba9f3e6a05":
                return False
        elif source_name != "we_ris":
            return False

        cat_schema = version.parse(cls.get_current_schema_version())
        if not(version.parse("1.1") > cat_schema >= version.parse("1.0")):
            return False

        # extractor version == rispy version, accept all
        return True


    def get_type(self, ref):
        type_map = {
            "JOUR": "Journal Article",
            "CHAP": "Book Section",
            "THES": "Thesis",
            "COMP": "Computer program",
            "GEN" : "Generic",
        }
        ris_abbrev = ref["type_of_reference"]
        return type_map.get(ris_abbrev, "Other ({})".format(ris_abbrev))

    def get_title(self, ref):
        return self._getOneOf(ref, "title", "primary_title")

    def get_doi(self, ref):
        doi = ref.get("doi")
        if doi is None:
            return ""
        prefix = "" if doi.startswith("http") else "https://doi.org/"
        return prefix + doi


    def get_date_published(self, ref):
        return self._getOneOf(ref, "year", "publication_year")

    def get_authors(self, ref):
        return [{"name": x} for x in self._getOneOf(ref, "authors", "first_authors")]

    def get_publication_outlet(self, ref):
        return self._getOneOf(ref, "journal_name", "secondary_title")


class NbibTranslator(CitationTranslator, TranslatorBase):

    @classmethod
    def match(cls, source_name, source_version, source_id=None):
        if source_id is not None:
            if source_id != "4b898c36-3ff0-4d65-b858-765a3ca83376":
                return False
        elif source_name != "we_nbib":
            return False

        cat_schema = version.parse(cls.get_current_schema_version())
        if not(version.parse("1.1") > cat_schema >= version.parse("1.0")):
            return False

        # extractor version == nbib version, accept all
        return True


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

    def get_publication_outlet(self, ref):
        return ref.get("journal")


class CrossrefTranslator(CitationTranslator, TranslatorBase):

    @classmethod
    def match(cls, source_name, source_version, source_id=None):
        if source_id is not None:
            if source_id != "579e1483-47e7-4ed6-a06c-179418e1a12e":
                return False
        elif source_name != "we_crossref":
            return False

        cat_schema = version.parse(cls.get_current_schema_version())
        if not(version.parse("1.1") > cat_schema >= version.parse("1.0")):
            return False

        return version.parse(source_version) < version.parse("0.1")

    @staticmethod
    def _fixup_title(title):
        # title may contain several different html tags like <i>...</i>
        # the regex will match <foo> and </bar> but not <>, <foo bar> or <<foo>>
        title = re.sub(r"<(?!<)[^> ]+>(?!>)", "", title)
        # no newlines
        title = re.sub(r"\n", " ", title)
        # more than 2 spaces are probably accidental
        title = re.sub(r" {3,}", " ", title)
        return title

    def get_type(self, ref):
        cr_type = ref.get("type")
        type_map = {"journal-article": "Journal Article"}
        return type_map.get(cr_type, cr_type)

    def get_title(self, ref):
        title = ref.get("title")[0]
        return self._fixup_title(title)

    def get_doi(self, ref):
        doi = ref.get("DOI")
        return "https://doi.org/" + doi if doi is not None else ""

    def get_date_published(self, ref):
        published = self._getOneOf(ref, "published", "published-print", "published-online")
        if published is not None:
            published = published["date-parts"][0][0]
        return published

    def get_authors(self, ref):
        authors = []
        for author in ref.get("author"):
            a = {
                "givenName": author.get("given", ""),
                "familyName": author.get("family", ""),
                "name": " ".join([author.get(x, "") for x in ("given", "family")]),
            }
            if (orcid := author.get("ORCID")) is not None:
                a["identifiers"] = [
                    {
                        "type": "ORCID",
                        "identifier": urlparse(orcid).path.lstrip("/"),
                    }
                ]
            authors.append(a)
        return authors

    def get_publication_outlet(self, ref):
        title = ref.get("container-title")
        return title[0] if title is not None else None
