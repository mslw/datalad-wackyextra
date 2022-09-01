"""Metadata extractor for citation files"""

from importlib.metadata import version
from pathlib import Path
from uuid import UUID

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
        cite_files = []
        for m in matching:
            res = self.dataset.get(m)
            cite_files.append(m)
        #cite_files = [Path(res["path"]) for res in self.dataset.get(matching)]
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