"""Metadata extractor for citation files"""

from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from uuid import UUID

import nbib
import rispy

from datalad_metalad.extractors.base import (
    DataOutputCategory, ExtractorResult, DatasetMetadataExtractor)


class RisExtractor(DatasetMetadataExtractor):

    def get_id(self) -> UUID:
        return UUID("81076796-4e6e-428b-b5c2-79ba9f3e6a05")

    def get_version(self) -> str:
        return version('rispy')

    def get_data_output_category(self) -> DataOutputCategory:
        return DataOutputCategory.IMMEDIATE

    def get_required_content(self) -> bool:
        files = list(self.dataset.repo.call_git_items_(["ls-files", "*.ris"]))
        if len(files) == 0:
            # this is fine, leave an empty list for our extractor, return true
            self._cite_files = []
            return True
        get_items = self.dataset.get(
            # note: get([]) would get everything, hence conditional above
            files,
            result_renderer="disabled",
            return_type="iterator",
        )
        # todo: proper error handling
        self._cite_files = [Path(res["path"]) for res in get_items]
        return True

    def _read_files(self) -> list[dict]:
        refs = []
        for f in self._cite_files:
            refs.extend(rispy.load(f, encoding="utf-8"))
        return refs

    def extract(self, _=None) -> ExtractorResult:
        return ExtractorResult(
            extractor_version=self.get_version(),
            extraction_parameter=self.parameter or {},
            extraction_success=True,
            datalad_result_dict={
                "type": "dataset",
                "status": "ok",
            },
            immediate_data={
                "id": self.dataset.id,
                "refcommit": self.dataset.repo.get_hexsha(),
                "refs": self._read_files(),
            }
        )


class NbibExtractor(DatasetMetadataExtractor):

    def get_id(self) -> UUID:
        return UUID("4b898c36-3ff0-4d65-b858-765a3ca83376")

    def get_version(self) -> UUID:
        return version("nbib")

    def get_data_output_category(self) -> DataOutputCategory:
        return DataOutputCategory.IMMEDIATE

    def get_required_content(self) -> bool:
        files = list(self.dataset.repo.call_git_items_(["ls-files", "*.nbib"]))
        if len(files) == 0:
            # this is fine, leave an empty list for our extractor, return true
            self._cite_files = []
            return True
        get_items = self.dataset.get(
            files,
            result_renderer="disabled",
            return_type="iterator",
        )
        self._cite_files = [Path(res["path"]) for res in get_items]
        return True

    @staticmethod
    def _coerce_types(ref) -> dict:
        cref = ref.copy()
        # Convert datetime to iso-formatted strings to make them json-serializable
        for k,v in ref.items():
            if type(v) is datetime:
                cref[k] = v.isoformat()
        return cref

    def _read_files(self) -> list[dict]:
        refs = []
        for f in self._cite_files:
            for ref in nbib.read_file(f):
                refs.append(self._coerce_types(ref))
        return refs

    def extract(self, _=None) -> ExtractorResult:
        return ExtractorResult(
            extractor_version=self.get_version(),
            extraction_parameter=self.parameter or {},
            extraction_success=True,
            datalad_result_dict={
                "type": "dataset",
                "status": "ok",
            },
            immediate_data={
                "id": self.dataset.id,
                "refcommit": self.dataset.repo.get_hexsha(),
                "refs": self._read_files(),
            }
        )
