__docformat__ = 'restructuredtext'

import json

from datalad.interface.base import Interface
from datalad.interface.base import build_doc
from datalad.support.param import Parameter
from datalad.distribution.dataset import datasetmethod
from datalad.interface.utils import eval_results
from datalad.interface.results import get_status_dict

from .translators.citations import RisTranslator, NbibTranslator
from .translators.cff import CffTranslator

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
        with open(infile, "rt") as jf:
            for line in jf:
                j = json.loads(line)
                if j["extractor_name"] == "we_ris":
                    t = RisTranslator(j)
                elif j["extractor_name"] == "we_nbib":
                    t = NbibTranslator(j)
                elif j["extractor_name"] == "we_cff":
                    t = CffTranslator(j)
                else:
                    # TODO: what to do (incomplete results)
                    pass
                translated_entries.append(t.translate())
                
        with open(outfile, "at") as jf:
            for entry in translated_entries:
                json.dump(entry, jf)

        # TODO yield proper result
        yield get_status_dict(
            action="translate",
            status="ok"
        )
