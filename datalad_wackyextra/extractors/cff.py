"""Metadata extractor for citation file format"""

import datetime
import json
from pathlib import Path
from uuid import UUID

import yaml

from datalad_metalad.extractors.base import (
    DataOutputCategory, ExtractorResult, DatasetMetadataExtractor
)


class CffExtractor(DatasetMetadataExtractor):
    def get_id(self) -> UUID:
        return UUID("b7089877-25f8-4f51-a4d0-de54da0f8ac3")

    def get_version(self) -> str:
        return "0.0.1"

    def get_data_output_category(self) -> DataOutputCategory:
        return DataOutputCategory.IMMEDIATE

    def get_required_content(self) -> bool:
        result = self.dataset.get("CITATION.cff", result_renderer="disabled")
        return result[0]["status"] in ("ok", "notneeded")

    def extract(self, _=None) -> ExtractorResult:
        # Returns citation file content as metadata, altering only date

        with open(Path(self.dataset.path) / "CITATION.cff") as f:
            yamlContent = yaml.safe_load(f)

        # Ensure data is json-serialisable by converting dates to iso-formatted strings
        yamlContent = json.loads(json.dumps(yamlContent, cls=IsoDateEncoder))

        return ExtractorResult(
            extractor_version=self.get_version(),
            extraction_parameter=self.parameter or {},
            extraction_success=True,
            datalad_result_dict={
                "type": "dataset",
                "status": "ok",
            },
            immediate_data=yamlContent,
        )


class IsoDateEncoder(json.JSONEncoder):
    """Extension of json encoder which converts dates to iso-format strings"""
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
