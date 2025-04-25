from frontend.ASTweave import *
from Weave.WeaveIR import *


class WeaveCodeGen:

    def __init__(self, inline_code=False):
        self._inline_code = inline_code

    def traverse(self, root) -> WeaveIRmodule:
        WeaveIRbase.setInlineCode(self._inline_code)
        debugMsg(5, "Starting codegen")
        return root.data.generate(None)
