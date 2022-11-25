# Dr Panik's Wacky Extractors (datalad-wackyextra)

This DataLad extension contains additional metadata extractors.

## Installation
...

## Extractors
The following metadata extractors are made available for `datalad meta-extract`:
- `we_ris` for RIS files; uses `rispy` package
- `we_nbib` for .nbib (MEDLINE®/PubMed®) files; uses `nbib` package
- `we_cff` for CFF files

## Translators
Translators translate extracted metadata into datalad-catalog format.
Translators are available for all the wacky extractors:
- `we_ris`,
- `we_nbib`,
- `we_cff`,
and, additionally, for the following metalad extractors:
- `metalad_core`,
- `metalad_studyminimeta`,
and datalad-catalog extractors:
- `datacite_gin`.

## Commands
- `wacky-translate`: read a json lines file with metadata entries and apply available translators to produce
  a json lines file with translated output, for usage with datalad-catalog
