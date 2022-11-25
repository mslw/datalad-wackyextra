__docformat__ = 'restructuredtext'

import jsonlines

from datalad.interface.base import Interface
from datalad.interface.base import build_doc
from datalad.support.param import Parameter
from datalad.distribution.dataset import datasetmethod
from datalad.interface.utils import eval_results
from datalad.interface.results import get_status_dict

from .translators.citations import RisTranslator, NbibTranslator
from .translators.cff import CffTranslator
from .translators.core import MetaladCoreTranslator
from .translators.minimeta import MinimetaTranslator
from .translators.datacite import DataciteTranslator

@build_doc
class Translate(Interface):
    """Translate metadata records into catalog format

    Translate metadata records produced (or recognised) by this
    extension to match datalad-catalog schema
    """

    _params_ = dict(
        infile=Parameter(
            args=("-i", "--infile"),
            doc="""Input file with json lines (jsonl)""",
        ),
        outfile=Parameter(
            args=("-o", "--outfile"),
            doc="""Output file; will be opened in append mode""",
        ),
    )

    @staticmethod
    @datasetmethod(name="wacky_translate")
    @eval_results
    def __call__(infile, outfile=None):
        translated_entries = []
        with jsonlines.open(infile, "r") as jf:
            for j in jf:
                # iterates over json objects (lines) in the file
                if j["extractor_name"] == "we_ris":
                    t = RisTranslator(j)
                elif j["extractor_name"] == "we_nbib":
                    t = NbibTranslator(j)
                elif j["extractor_name"] == "we_cff":
                    t = CffTranslator(j)
                elif j["extractor_name"] == "metalad_core" and j["type"] == "dataset":
                    t = MetaladCoreTranslator(j)
                elif j["extractor_name"] == "metalad_studyminimeta":
                    t = MinimetaTranslator(j)
                elif j["extractor_name"] == "datacite_gin":
                    t = DataciteTranslator(j)
                else:
                    # TODO: what to do (incomplete results)
                    pass
                translated_entries.append(t.translate())
                
        with jsonlines.open(outfile, "a") as jf:
            jf.write_all(translated_entries)

        # TODO yield proper result
        yield get_status_dict(
            action="translate",
            status="ok"
        )
