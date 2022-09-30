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
Translators are provided to translate the metadata produced by the extractors above into datalad-catalog format.

## Commands
- `wacky-translate`: read a json lines file with metadata entries and apply available translators to produce
  a json lines file with translated output, for usage with datalad-catalog
