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
        ds_path = Path(self.dataset.path)
        matching = ds_path.glob('**/*.ris')
        """
        Note: this glob is suboptimal for many reasons
        - not sure if would do the right thing on Windows && probably would go through the git annex object tree
        - chain 2 globs, one *.ris, other for all top-level directories
        - Path objects have a method iterdir which would exclude hidden directories
        - or look at git ls-files or rather ls-tree (ls-tree HEAD)
        - ds.repo.call_git_items(...) -> to get a list
        """
        cite_files = [Path(res["path"]) for res in self.dataset.get(matching, result_renderer="disabled")]
        self._cite_files = cite_files

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
        ds_path = Path(self.dataset.path)
        matching = ds_path.glob("**/*.nbib")
        cite_files = [Path(res["path"]) for res in self.dataset.get(matching, result_renderer="disabled")]
        self._cite_files = cite_files

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
