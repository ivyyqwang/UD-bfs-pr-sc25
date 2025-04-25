"""Abstract Syntax Tree for weaveUD

This is the file that represents the abstract syntax tree for 
UDweave. 

Notice that the types and qualifiers here are different
to that used in the IR representation. In particular, 
while pointer is a qualifier here, it will be converted to a
type in weaveIR
"""

import treelib as tl
from Weave import helper
from Weave.WeaveIR import *
import Weave.WeaveIRenums as WIRinst
from Weave.fileLocation import FileLocation, FileManager, FileContent
import copy

from typing import Union
from typing import Optional

from frontend.ASTweaveEnums import (
    WeaveTypeQualifier,
    WeaveBinaryOps,
    WeaveDeclTypes,
    WeaveDataTypes,
    WeaveDataTypesPrimitives,
    WeaveUnaryOps,
    WeaveASTTypes,
)


class WeaveNode(ABC):
    _userDefinedDataTypes = dict()

    def __init__(self, dataType: WeaveDataTypes = None):
        self.type = None
        self.nodeName = None
        self.fileLocation = None
        self._dataType = dataType

    @abstractmethod
    def to_string(self):
        pass

    @property
    def as_string(self):
        return self.to_string()

    @property
    def dataType(self):
        if self._dataType.type == WeaveDataTypesPrimitives.UserDefined:
            return self.findDataType(self._dataType)
        return self._dataType

    @property
    def inline_code(self):
        return self._inline_code

    def setInlineCode(self, inline_code: bool):
        self._inline_code = inline_code

    def resetUserDefinedDataTypes(self):
        self._userDefinedDataTypes = dict()

    def setUserDefinedDataTypes(self, types: dict):
        self._userDefinedDataTypes = types

    def addDataType(self, name: str, fields: list):
        self._userDefinedDataTypes[name] = fields

    def findDataType(self, dataType: WeaveDataTypes):
        return (
            self._userDefinedDataTypes[dataType.getName()]
            if dataType.getName() in self._userDefinedDataTypes
            else dataType
        )

    def strToDataType(self, dataTypeName: str):
        return (
            self._userDefinedDataTypes[dataTypeName]
            if dataTypeName in self._userDefinedDataTypes
            else None
        )

    def __str__(self):
        return self.to_string()

    @abstractmethod
    def generate(self, ctx):
        pass


class WeaveProgram(WeaveNode):
    def __init__(self):
        super().__init__()
        self.name = "TBD"
        self.type = WeaveASTTypes.Root
        self.program_sections = None

    def to_string(self):
        return f"{str(self.type)} <>"

    def setName(self, name):
        self.name = name

    def setProgramSections(self, sections: list):
        self.program_sections = sections

    def generate(self, ctx):
        debugMsg(
            5,
            f"Generating program {self.name} with {len(self.program_sections)} program statements",
        )
        program = WeaveIRmodule(self.name)
        program.setFileLocation(self.fileLocation)

        # Add all events symbols to the program such that
        # they can be referenced later on and use during lowering
        for ps in self.program_sections:
            if isinstance(ps.data, WeaveScope):
                for section in ps.data.body:
                    # Resolve external symbols
                    if isinstance(section.data, WeaveEvent):
                        if not section.data.isExternal:
                            errorMsg(
                                f"Event {section.data.nodeName} is not external but is defined at the top level",
                                section.data.fileLocation,
                            )
                        namespace = (
                            section.data.namespace if section.data.namespace is not None else ""
                        )
                        syms = program.findSymbolDecl(namespace, section.data.nodeName)
                        if len(syms) > 0:
                            errorMsg(
                                f"Event {section.data.nodeName} already defined.",
                                section.data.fileLocation,
                            )
                        program.addSymbolDecl(
                            section.data.namespace if section.data.namespace is not None else "",
                            section.data.nodeName,
                            True,
                        )

                    # Resolve thread symbols
                    if isinstance(section.data, WeaveThread) and not section.data.isTemplate:
                        for tSection in section.data.thread_sections:
                            if isinstance(tSection.data, WeaveScope):
                                for scopedSection in tSection.data.body:
                                    if isinstance(scopedSection.data, WeaveEvent):
                                        syms = program.findSymbolDecl(
                                            section.data.nodeName
                                            if not section.data.isAnonymous
                                            else "",
                                            scopedSection.data.nodeName,
                                        )
                                        if len(syms) > 0:
                                            anonThread = (
                                                (
                                                    "This event is defined inside an anonymous thread,"
                                                    " maybe confirm that it has not been previously "
                                                    "defined in another anonymous thread or as an external event"
                                                )
                                                if section.data.isAnonymous
                                                else ""
                                            )
                                            errorMsg(
                                                f"Event {scopedSection.data.nodeName} already defined. {anonThread}",
                                                scopedSection.data.fileLocation,
                                            )
                                        program.addSymbolDecl(
                                            section.data.nodeName
                                            if not section.data.isAnonymous
                                            else "",
                                            scopedSection.data.nodeName,
                                        )

                    if (
                            isinstance(ps.data, WeaveDeclarationStatement)
                            and not ps.data.isGlobalConstant
                    ):
                        # A declaration statement at this level implies a static variable
                        ps.data.addQual(WeaveTypeQualifier.Static)

        for s in self.program_sections:
            s.data.generate(program)
        return program


class WeaveScope(WeaveNode):
    depth = -1

    def __init__(self, body: list, parent: WeaveNode, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.Scope
        self.parent = parent
        self.body = body
        self.fileLocation = loc

    def to_string(self):
        return f"{str(self.type)} at {str(self.fileLocation)}"

    def generate(self, ctx: WeaveIRbase):
        WeaveScope.depth += 1
        oldParent = ctx.ctx_scope
        debugMsg(5, f"Generating scope, depth={WeaveScope.depth}")

        scope = WeaveIRscope(ctx, WeaveScope.depth, oldParent)
        scope.setFileLocation(self.fileLocation)

        if oldParent is None:
            ctx.ctx_program.addScope(scope)

        ctx.ctx_scope = scope

        # code gen
        inst = []
        for b in self.body:
            if isinstance(b, WeaveThread):
                inst.append(b.generate(ctx))
            else:
                inst.append(b.data.generate(ctx))

        debugMsg(5, f"Leaving scope, depth={WeaveScope.depth}")
        WeaveScope.depth -= 1
        ctx.ctx_scope = oldParent
        return inst


class WeaveThread(WeaveNode):
    # List of templates for evaluation. This is a static
    # variable that is shared across all threads
    ThreadTemplates = dict()

    def __init__(
            self, name: str, thread_sections: list, inherit_list: list, loc: FileLocation
    ):
        super().__init__()
        self.type = WeaveASTTypes.Thread
        self.nodeName = name
        self.thread_sections = thread_sections
        self.fileLocation = loc
        self._isAnonymous = False
        # This is a list of tuples (threadName, params)
        self._inheritanceList = inherit_list
        self._isTemplate = False
        self._template_params = None

    def to_string(self):
        return f"{str(self.type)} <> name = {str(self.nodeName)} at {str(self.fileLocation)}"

    def setIsAnonymous(self, isAnon: bool):
        self._isAnonymous = isAnon

    def setIsTemplate(self, templ: bool):
        self._isTemplate = templ

    def setTemplateParams(self, params: list):
        self._template_params = params

    def addResolvedTemplateParams(self, params: list, ctx: WeaveIRbase):
        if params is None:
            return
        if len(params) != len(self._template_params):
            errorMsg(
                f"Template {self.nodeName} instantiated with wrong number of parameters",
                self.fileLocation,
            )
        for tempType, resolvedType in zip(self._template_params, params):
            if tempType[0] == "typename":
                self.addDataType(tempType[1], resolvedType.get_name())
            elif tempType[0] == "eventname":
                name = resolvedType.get_name()
                ns = name.split("::")[0:-1]
                ns = "::".join(ns)
                name = name.split("::")[-1]
                if len(ns) == 0:
                    ns = ctx.name
                else:
                    ns = resolvedType.nameSpace
                # Create an event symbol
                ctx.ctx_program.addSymbolDecl(ns, name)

    @property
    def isAnonymous(self):
        return self._isAnonymous

    @property
    def inheritanceList(self):
        return self._inheritanceList

    @property
    def isTemplate(self):
        return self._isTemplate

    @property
    def templateParams(self):
        return self._template_params

    def _hasInterfaceEvent(self):
        debugMsg(5, "Checking if thread has interface event " + self.nodeName)
        for e in self.thread_sections:
            if isinstance(e.data, WeaveScope):
                for s in e.data.body:
                    if isinstance(s.data, WeaveEvent) and s.data.isInterface:
                        return True

    def _getEvents(self):
        events = []
        for e in self.thread_sections:
            if isinstance(e.data, WeaveScope):
                for s in e.data.body:
                    if isinstance(s.data, WeaveEvent):
                        events.append(s.data)
        return events

    def getInterfaceEvents(self):
        events = []
        for e in self.thread_sections:
            if isinstance(e.data, WeaveScope):
                for s in e.data.body:
                    if isinstance(s.data, WeaveEvent) and s.data.isInterface:
                        events.append(s.data)
        return events

    def _checkTemplateParams(self):
        debugMsg(7, f"Checking template params for thread {self.nodeName}")
        for inherit in self.inheritanceList:
            debugMsg(10, f"Checking inheritance from {inherit[0]}")
            inhThread = self.ThreadTemplates[inherit[0]]
            if inhThread.templateParams is not None:
                if inherit[1] is None:
                    errorMsg(
                        f"Thread {self.nodeName} inherits from {inherit[0]} but no template parameters are provided",
                        self.fileLocation,
                    )
                if len(inhThread.templateParams) != len(inherit[1]):
                    errorMsg(
                        f"Thread {self.nodeName} inherits from {inherit[0]} with wrong number of template parameters",
                        self.fileLocation,
                    )
                # Check there are no None types in templateParams
                if any([t is None for t in inherit[1]]):
                    errorMsg(
                        f"Thread {self.nodeName} inherits from {inherit[0]} with None template parameters",
                        self.fileLocation,
                    )

    def _checkResolveAllInterfaces(self):
        debugMsg(
            7, f"Checking that all interfaces are implemented in thread {self.nodeName}"
        )
        for inher in self.inheritanceList:
            debugMsg(10, f"Checking inheritance from {inher[0]}")
            inhThread = self.ThreadTemplates[inher[0]]
            for intEvent in inhThread.getInterfaceEvents():
                debugMsg(10, f"Checking interface {intEvent.nodeName}")

                if intEvent.nodeName not in [e.nodeName for e in self._getEvents()]:
                    errorMsg(
                        f"Thread {self.nodeName} does not implement interface event {intEvent.nodeName}",
                        self.fileLocation,
                    )

    def addEventSymbols(self, ctx: WeaveIRbase, thread: "WeaveThread"):
        for s in thread.thread_sections:
            if isinstance(s.data, WeaveScope):
                for e in s.data.body:
                    if isinstance(e.data, WeaveEvent) and not e.data.isInterface:
                        syms = ctx.ctx_program.findSymbolDecl(
                            self.nodeName,
                            e.data.nodeName,
                        )
                        if len(syms) > 0:
                            errorMsg(
                                f"Event {e.data.nodeName} already defined in thread {self.nodeName}",
                                e.data.fileLocation,
                            )
                        debugMsg(
                            3,
                            "Adding event symbol "
                            + e.data.nodeName
                            + " to thread "
                            + self.nodeName,
                        )
                        ctx.ctx_program.addSymbolDecl(
                            self.nodeName,
                            e.data.nodeName,
                        )

    def generate(self, ctx):
        self.ThreadTemplates[self.nodeName] = self
        if self.isTemplate:
            # This type of thread is not generated until it is instantiated
            debugMsg(5, f"Generating template event {self.nodeName}")
            return

        if self._hasInterfaceEvent() and not self.isTemplate:
            # Event interfaces can only be used in template threads
            errorMsg(
                f"Thread {self.nodeName} has at least one event interface event but is not a template",
                self.fileLocation,
            )

        thread = WeaveIRthread(ctx)
        thread.setFileLocation(self.fileLocation)
        thread.setAnonymous(self._isAnonymous)
        thread.name = self.nodeName

        ctx.ctx_scope.addBody(thread)

        self._checkTemplateParams()
        self._checkResolveAllInterfaces()

        decls = []
        for inheritance in self.inheritanceList:
            debugMsg(
                5,
                f"Generating inheritance for thread {self.nodeName} from {inheritance[0]}",
            )
            inhThread = self.ThreadTemplates[inheritance[0]]
            # We do this to support typedefs in the future
            oldTemplateParams = copy.copy(inhThread.templateParams)
            inhThread.addResolvedTemplateParams(inheritance[1], thread)
            self.addEventSymbols(ctx, inhThread)
            decls.append(inhThread.generateLogic(thread))
            inhThread.setTemplateParams(oldTemplateParams)
        decls.append(self.generateLogic(thread))
        return decls

    def generateLogic(self, thread: WeaveIRthread = None):
        debugMsg(5, f"Generating thread {self.nodeName}")

        # Generate declarations
        decls = []
        for d in self.thread_sections:
            decls.append(d.data.generate(thread))
        return decls


class WeaveEvent(WeaveNode):
    def __init__(self, name: str, params: list, statements: list, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.Event
        self.nodeName = name
        self.params = params
        self.body = statements
        self.fileLocation = loc
        self._isExternal = False
        self._namespace = None
        self._isInterface = None

    def setBody(self, body: list):
        self.body = body

    def setIsExternal(self, ext: bool):
        self._isExternal = ext

    def setNamespace(self, ns: str):
        self._namespace = ns

    def setIsInterface(self, isInterface: bool):
        # An interface is an event that must be implemented by the inheriting thread
        self._isInterface = isInterface

    @property
    def isExternal(self):
        return self._isExternal

    @property
    def namespace(self) -> Union[str, None]:
        return self._namespace

    @property
    def isInterface(self):
        return self._isInterface

    def to_string(self):
        namespace = f" namespace = {self._namespace} -" if self._namespace else ""
        extern = f"external -{namespace}" if self._isExternal else ""
        return f"{str(self.type)} <> {extern} name = {str(self.nodeName)} at {str(self.fileLocation)}"

    def generate(self, ctx):
        if self.isInterface:
            return
        if self._isExternal:
            event = WeaveIRevent(ctx, self.nodeName, True)
            event.setFileLocation(self.fileLocation)

            event.setIsExternal(True)

            ctx.ctx_program.addExternal(event)

        else:
            # Internal events must be inside a thread. Also, they cannot have a namespace

            if not ctx.ctx_thread:
                errorMsg(
                    f"An event {self.nodeName} must be defined inside a thread",
                    self.fileLocation,
                )
            if self._namespace:
                errorMsg(
                    f"An event {self.nodeName} that is defined inside a thread "
                    "cannot have a namespace in the name",
                    self.fileLocation,
                )

            debugMsg(
                5,
                f"Generating event {self.nodeName} within {ctx.ctx_thread.name} thread",
            )
            # Create empty basic block
            event = WeaveIRevent(ctx, self.nodeName)
            event.setFileLocation(self.fileLocation)

            ctx.ctx_thread.addEvent(event)

            # Deal with params.
            for p in self.params:
                # Generate a regular declarator, but overwrite the number and type
                p.data.generate(event)

            # Iterate over statements and generate
            for s in self.body:
                s.data.generate(event)

            event.addImplicitYield()


class WeaveEmpty(WeaveNode):
    def __init__(self):
        super().__init__()
        self.type = WeaveASTTypes.Empty

    def to_string(self):
        return f"{str(self.type)} <>"

    def generate(self, ctx):
        pass


class WeaveLiteral(WeaveNode):
    def __init__(self, dataType: WeaveDataTypes, value, loc: FileLocation):
        super().__init__(dataType)
        self.type = WeaveASTTypes.Literal
        self.value = value
        self.fileLocation = loc

    def to_string(self):
        return f"{str(self.type)} <{str(self.dataType)}> value = {str(self.value)} at {str(self.fileLocation)}"

    def generate(self, ctx):
        debugMsg(
            5,
            f"Generating WeaveIRimmediate for {self.value} ({self.dataType.getName()}) in location {str(self.fileLocation)}",
        )

        # The front end uses a list for strings that are concatenated. We need to join them
        if self.dataType.type == WeaveDataTypesPrimitives.String:
            self.value = "".join(self.value)

        lit = WeaveIRimmediate(ctx, val=self.value, dataType=None, quals=None,
                               inLoop=ctx.inLoop())  # derive the data type from the instruction
        lit.setFileLocation(self.fileLocation)

        return lit


class WeaveIdentifier(WeaveNode):
    def __init__(
            self, dataType: WeaveDataTypes, quals: list, name: str, loc: FileLocation
    ):
        super().__init__(dataType)
        self.type = WeaveASTTypes.Identifier
        self.nodeName = name
        self.nameSpace = ""
        self.quals = quals
        self.fileLocation = loc
        self._isReserved = False

    def to_string(self):
        name = (
            self.nameSpace + "::" + str(self.nodeName)
            if len(self.nameSpace) != 0
            else str(self.nodeName)
        )
        return (f"{str(self.type)} <{str(self.dataType)}> name = {name} quals = {str(self.quals)} at "
                f"{str(self.fileLocation)}")

    # Reserved identifiers allow to use keywords as identifiers that are used in different lowering
    # contexts. For example, a datatype may be passed to the sizeof() method. Which will result in a constant
    # being generated
    def setIsReserved(self, isReserved: bool):
        self._isReserved = isReserved

    @property
    def isReserved(self):
        return self._isReserved

    def get_name(self):
        return self.nodeName

    def generate(self, ctx):
        debugMsg(
            5,
            f"Finding declaration for Identifier {self.nodeName} in location {str(self.fileLocation)}",
        )
        # Check if it is an intrinsic variable. If so, generate it
        intrinVar = ctx.ctx_program.getIntrinsicVars(self.nodeName)
        if len(intrinVar) > 0:
            intrRes = intrinVar[0].generateWeaveIR(ctx)
            return intrRes

        if isinstance(self.nodeName, WeaveDataTypes):
            dataType = WeaveIRsymPtr(ctx, None, self.nodeName.getName())
            dataType.setFileLocation(self.fileLocation)
            dataType.setType(WIRinst.convertASTtype(self.nodeName))
            return dataType

        # Check if the name is a data type
        dt = self.strToDataType(self.nodeName)
        if dt is not None:
            if isinstance(ctx, WeaveIRcall):
                dataType = WeaveIRsymPtr(ctx, None, self.nodeName)
                dataType.setFileLocation(self.fileLocation)
                dataType.setType(WIRinst.convertASTtype(dt))
                return dataType
            else:
                errorMsg(
                    f"Using a data type {self.nodeName} as an identifier",
                    self.fileLocation,
                )

        def _findSymbolDecl():
            # Check event_based namespace
            def_ns = (
                ctx.ctx_thread.name + "::" + ctx.ctx_event.name
                if ctx.ctx_event
                else ctx.ctx_thread.name
            )
            ns = self.nameSpace if len(self.nameSpace) > 0 else def_ns
            sym = ctx.ctx_program.findSymbolDecl(ns, self.nodeName)
            if len(sym) == 0:
                ns = self.nameSpace if len(self.nameSpace) > 0 else ctx.ctx_thread.name
                sym = ctx.ctx_program.findSymbolDecl(ns, self.nodeName)
                if len(sym) == 0:
                    # Try without namespace for external symbols
                    sym = ctx.ctx_program.findSymbolDecl("", self.nodeName)
                    if len(sym) == 0:
                        errorMsg(
                            f"Using an identifier {self.nodeName} that has not been previously defined",
                            self.fileLocation,
                        )
            return sym[0]

        # Previously defined. Check if exist in context
        ident = ctx.ctx_scope.findDecl(self.nodeName)
        if ident is None:
            # Check if it is an event
            return _findSymbolDecl()

        if ident.isConstant and ident.isAssigned:
            debugMsg(
                5,
                f"Found constant variable {self.nodeName} in location {str(self.fileLocation)}. curReg = {ident.curReg}",
            )
            return ident.getAssigned()

        if ident.isStatic:
            debugMsg(
                5,
                f"Found static variable {self.nodeName} in location {str(self.fileLocation)}. curReg = {ident.curReg}",
            )

            # This is a static variable, hence there must be a symbolDecl
            sym = _findSymbolDecl()
            # Emit a load instruction for getting the address from the static variable
            load = WeaveIRmemory(
                ctx=ctx,
                dataType=WIRinst.WeaveIRtypes.ptr,
                opType=WIRinst.WeaveIRmemoryTypes.LOAD,
                ops=[sym],
            )
            load.setFileLocation(self.fileLocation)

            load.setRetOp(
                WeaveIRregister(
                    load,
                    ident,
                    ctx.ctx_scope.getNextRegisterNumber(),
                    WIRinst.WeaveIRregTypes.gpr,
                    WIRinst.WeaveIRtypes.ptr,
                    [],
                )
            )
            ctx.ctx_event.addInstruction(load)

            # Emit a load instruction from the memory holding the static var
            load = WeaveIRmemory(
                ctx=ctx,
                dataType=ident.dtype,
                opType=WIRinst.WeaveIRmemoryTypes.LOADLOCAL,
                ops=[
                    load.getAsOperand(),
                    WeaveIRimmediate(ctx, 0, ident.dtype),
                ],
            )
            load.setFileLocation(self.fileLocation)

            load.setRetOp(
                WeaveIRregister(
                    load,
                    ident,
                    ctx.ctx_scope.getNextRegisterNumber(),
                    WIRinst.WeaveIRregTypes.gpr,
                    ident.dataType,
                    [],
                )
            )
            ctx.ctx_event.addInstruction(load)
            return load

        return ident


class WeaveStruct(WeaveNode):
    def __init__(self, name: str, fields: list, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.Struct
        self.nodeName = name
        self.fields = fields
        self.fileLocation = loc

    @property
    def name(self):
        return self.nodeName

    def to_string(self):
        fields = f"[{', '.join([str(f.data.get_name()) for f in self.fields])}]"
        return f"{str(self.type)} <{str(self.nodeName)}> fields = {str(fields)} at {str(self.fileLocation)}"

    def generate(self, ctx):
        debugMsg(5, f"Generating struct {self.nodeName}")
        types = []
        newStruct = WeaveIRstructDecl(ctx, self.nodeName)
        newStruct.setFileLocation(self.fileLocation)

        for f in self.fields:
            debugMsg(6, f"Generating field {f.data.get_name()}")
            ty = f.data.generate(newStruct)
            # if len(types) != 0 and ty.getSize(self.fileLocation) % 8 != 0:
            #     # Add padding
            #     padSize = 8 - (ty.getSize(self.fileLocation) % 8)
            #     pad = WeaveIRpadding(ctx, padSize)
            #     pad.setFileLocation(self.fileLocation)
            #     types.append(pad)
            types.append(ty)

        newStruct.setFields(types)
        ctx.ctx_program.addDataTypeDecl(newStruct)


class WeaveUnion(WeaveNode):
    def __init__(self, name: str, fields: list, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.Union
        self.nodeName = name
        self.fields = fields
        self.fileLocation = loc

    @property
    def name(self):
        return self.nodeName

    def to_string(self):
        fields = f"[{', '.join([str(f.data.get_name()) for f in self.fields])}]"
        return f"{str(self.type)} <{str(self.nodeName)}> fields = {str(fields)} at {str(self.fileLocation)}"

    def generate(self, ctx):
        debugMsg(5, f"Generating union {self.nodeName}")
        types = []
        newUnion = WeaveIRunionDecl(ctx, self.nodeName)
        newUnion.setFileLocation(self.fileLocation)

        for f in self.fields:
            debugMsg(6, f"Generating field {f.data.get_name()}")
            ty = f.data.generate(newUnion)
            types.append(ty)

        newUnion.setFields(types)
        ctx.ctx_program.addDataTypeDecl(newUnion)


class WeaveBinaryOperator(WeaveNode):
    def __init__(
            self, opType: WeaveBinaryOps, left: tl.Node, right: tl.Node, loc: FileLocation
    ):
        super().__init__()
        self.type = WeaveASTTypes.BinaryOperator
        self.opType = opType
        self.fileLocation = loc
        self.left = left
        self.right = right

    def to_string(self):
        return f"{str(self.type)} <{str(self.opType)}> at {str(self.fileLocation)}"

    def isTerminalNode(self, node):
        return isinstance(node, WeaveLiteral) or isinstance(node, WeaveIdentifier)

    def attempt_folding(self, ctx, l, r, op):
        ops_map = {
            WeaveBinaryOps.PLUS: lambda x, y: x + y,
            WeaveBinaryOps.MINUS: lambda x, y: x - y,
            WeaveBinaryOps.TIMES: lambda x, y: x * y,
            WeaveBinaryOps.DIVIDE: lambda x, y: x / y,
            WeaveBinaryOps.MODULO: lambda x, y: x % y,
            WeaveBinaryOps.SHFTLFT: lambda x, y: x << y,
            WeaveBinaryOps.SHFTRGT: lambda x, y: x >> y,
            WeaveBinaryOps.LESSTHAN: lambda x, y: int(x < y),
            WeaveBinaryOps.LESSEQTO: lambda x, y: int(x <= y),
            WeaveBinaryOps.GREATERTHAN: lambda x, y: int(x > y),
            WeaveBinaryOps.GREATEREQTO: lambda x, y: int(x >= y),
            WeaveBinaryOps.AND: lambda x, y: int(x and y),
            WeaveBinaryOps.OR: lambda x, y: int(x or y),
            WeaveBinaryOps.BWOR: lambda x, y: x | y,
            WeaveBinaryOps.BWAND: lambda x, y: x & y,
            WeaveBinaryOps.BWXOR: lambda x, y: x ^ y,
            WeaveBinaryOps.EQUAL: lambda x, y: int(x == y),
            WeaveBinaryOps.DIFFERENT: lambda x, y: int(x != y),
        }
        if isinstance(l, WeaveIRimmediate) and isinstance(r, WeaveIRimmediate):
            result = ops_map[op](l.getValue(), r.getValue())
            if l.dtype.isFloatingPoint or r.dtype.isFloatingPoint:
                result = float(result)
                result_type = l.dtype if l.dtype.isFloatingPoint else r.dtype
            else:
                result = int(result)
                # assume the data type. i32 for 32 bit values, i64 otherwise
                result_type = (WIRinst.WeaveIRtypes.i32 if result.bit_length() < 32 else WIRinst.WeaveIRtypes.i64)

            newImm = WeaveIRimmediate(ctx, result, dataType=result_type)
            newImm.setFileLocation(self.fileLocation)
            debugMsg(5, f"Folding {l.getValue()} {op.name} {r.getValue()} into {newImm.getValue()}")
            return newImm
        return None

    def castValues(self, ctx, l, r) -> WeaveIRinstruction:
        if (
                self.opType != WeaveBinaryOps.MEMORY_DERREF
                and self.opType != WeaveBinaryOps.STRUCT_ELEMENT_ACCESS
                and l.dtype and l.dtype != WIRinst.WeaveIRtypes.ptr
                and r.dtype and r.dtype != WIRinst.WeaveIRtypes.ptr
                and l.dtype != r.dtype
        ):
            if isinstance(l, WeaveIRimmediate) and r.dtype != WIRinst.WeaveIRtypes.unknown:
                debugMsg(3, f"Changing type for right immediate from default {l.dtype} to {r.dtype}")
                # No need to insert cast, let's just re-interpret the value
                l.setType(r.dtype)
            elif isinstance(r, WeaveIRimmediate) and l.dtype != WIRinst.WeaveIRtypes.unknown:
                debugMsg(3, f"Changing type for left immediate from default {r.dtype} to {l.dtype}")
                # No need to insert cast, let's just re-interpret the value
                r.setType(l.dtype)
            else:
                debugMsg(
                    3,
                    f"Inserting casting for operand {r.getAsOperand().name} from {r.dtype} to {l.dtype} during "
                    f"lowering",
                )
                r = WeaveIRcast(ctx=ctx, out_type=l.dtype, inReg=r.getAsOperand())
                r.setFileLocation(self.fileLocation)

                tempDecl = ctx.ctx_scope.getTempDeclaration(r.dtype, r.quals)
                r.setRetOp(tempDecl.curReg)
                ctx.ctx_event.addInstruction(r)
        return r

    def checkCommutativity(self, ctx, l):
        """If the type is still unknown, we have an instruction that is not commutative and the left side
        is an immediate. For instance:
            a = 1 - b
        In this case, we have to create a temporary register first to store the 1, which is b then subtracted
        from."""
        if (
                isinstance(l, WeaveIRimmediate) and not self.opType.isCommutative() and not
                # the division is special. If you have 0 / n, the quotient is 0. Hence, we do not have to
                # create a temporary register to store the 0. The optimizer will yeet the division
                (self.opType == WeaveBinaryOps.DIVIDE and l.getOriginalValue() == 0 and not l.dtype.isFloatingPoint)
        ):
            ctx.ctx_scope.startScope()
            tempDecl = ctx.ctx_scope.getTempDeclaration(l.dtype, l.quals)
            tempDecl.setFileLocation(self.fileLocation)

            immediateMove = WeaveIRmemory(ctx, l.dtype, WIRinst.WeaveIRmemoryTypes.LOAD, [l])
            immediateMove.setRetOp(tempDecl.curReg)
            immediateMove.setFileLocation(self.fileLocation)
            ctx.ctx_event.addInstruction(immediateMove)
            ctx.ctx_scope.endScope()

            return immediateMove
        return l

    def getLogicalOpShortCircuit(
            self,
            ctx: WeaveIRevent,
            l: WeaveIRinstruction,
            r: WeaveIRinstruction,
            cond: WIRinst.WeaveIRBranchTypes,
            logicalOp: WIRinst.WeaveIRbitwiseTypes,
    ) -> tuple:
        """
        Generate a logical operation (AND or OR). This method support short circuitry. For instance, a() || b()
        If a() evaluates to True, b() is not executed (including its side effects). However, in UDW, we do not
        allow statements with side effects in the condition, like assignments or function calls. The latter one we
        do not have in the first place. Hence, we do not need short-circuiting. However, we still support it for
        future uses.
            ctx: WeaveIRevent
            l: The left side of the boolean instruction
            r: The right side of the boolean instruction
            cond: The condition to branch on
            logicalOp: The logical operation to perform (AND or OR)
            @param ctx:
            @type ctx: WeaveIRevent
            @param l: the LHS
            @type l: WeaveIRinstruction
            @param r: the RHS
            @type r: WeaveIRinstruction
            @param cond: The type of the branching: (un)conditional
            @type cond: IRinst.WeaveIRBranchTypes
            @param logicalOp: The and/or operation connecting the RHS and LHS
            @type logicalOp: WIRinst.WeaveIRbitwiseTypes
            @return: Rge last instruction of the short-circuiting and the LHS
            @rtype: tuple[WeaveIRbitwise, any]
        """
        true_label = ctx.getLabel("if", "true")
        post_label = ctx.getLabel("if", "post")
        trueBB = WeaveIRbasicBlock(ctx, true_label)
        postBB = WeaveIRbasicBlock(ctx, post_label)
        trueBB.setFileLocation(self.fileLocation)
        postBB.setFileLocation(self.fileLocation)
        condBB = ctx.ctx_event.curBB

        # Logical AND or OR needs short circuiting: For instance, a() || b()
        # If a() evaluates to True, b() is not executed (including its side effects)
        # Therefore, here the following steps are executed:
        #
        # 1.   lValue = l.generate()
        # 2.   rValue = 0
        # 3.   if(!lValue) { // for OR
        # 3.   if(lValue) {  // for AND
        # 4.     rValue = r.generate()
        #      }
        # 5.   return lValue | rValue

        # 1.   lValue = l.generate()
        rValueDecl = ctx.ctx_scope.getTempDeclaration(WIRinst.WeaveIRtypes.i64)
        rValueDecl.setFileLocation(self.fileLocation)

        # 2.   rValue = 0
        immediateMove = WeaveIRmemory(
            ctx, rValueDecl.curReg.dtype, WIRinst.WeaveIRmemoryTypes.LOAD,
            [WeaveIRimmediate(ctx, 0, WIRinst.WeaveIRtypes.i64)]
        )
        immediateMove.setRetOp(rValueDecl.curReg)
        immediateMove.setFileLocation(self.fileLocation)
        ctx.ctx_event.addInstruction(immediateMove)

        # 2.   lValue = l.generate()
        l = l.generate(ctx)
        l.setFileLocation(self.fileLocation)

        # 3.   if(!lValue) {
        branch_instruction = WeaveIRbranch(
            ctx,
            cond,
            postBB,
            l.getAsOperand(),
            WeaveIRimmediate(ctx, 0, l.dataType),
        )
        branch_instruction.setFileLocation(self.fileLocation)
        # DO NOT OPTIMIZE THIS TO A SINGLE CMP/BR INSTRUCTION!
        # We need the result of the compare for the boolean instruction. If we use conditional branch here,
        # this result is lost.
        # if isinstance(l, WeaveIRcompare):
        #     l.addBranchInstr(branch_instruction)
        # else:
        #     ctx.ctx_event.addInstruction(branch_instruction)
        ctx.ctx_event.addInstruction(branch_instruction)
        ctx.ctx_event.addBasicBlock(trueBB)

        for e in condBB.out_edges:
            postBB.addOutEdge(e)
        condBB.resetOutEdges()
        condBB.addOutEdge(trueBB)
        trueBB.addInEdge(condBB)

        # 4.     rValue = r.generate()
        r = r.generate(ctx)
        r.setFileLocation(self.fileLocation)
        r.setRetOp(immediateMove.getAsOperand())

        ctx.ctx_event.addBasicBlock(postBB)
        condBB.addOutEdge(postBB)
        postBB.addInEdge(condBB)
        trueBB.addOutEdge(postBB)
        postBB.addInEdge(trueBB)

        # 5.   return lValue XX rValue, where XX = {|, &}
        inst = WeaveIRbitwise(
            ctx,
            dataType=l.dtype,
            opType=logicalOp,
            left=l.getAsOperand(),
            right=immediateMove.getAsOperand(),
        )
        inst.setFileLocation(self.fileLocation)
        return inst, l

    def generate(self, ctx):
        """Generate for arithmetic operations
        This is a recursive generator for complex arithmetic.
        Left and right are either terminal nodes (i.e. an identifier (variables a, b)
        or a literal (numbers 3 or 3.5), or it is a recursively generated param that calls
        this function again.
        The recursion should return a WeaveIR instruction that contains a dataType parameter
        This is (arith, compare, ... that inherits from WeaveIR instruction).

        Returns:
            WeaveIRinstruction: The instruction added to the basic block
        """
        debugMsg(
            5,
            f"Generating arithmetic operation {self.opType.name} in location {str(self.fileLocation)}",
        )
        l = self.left.data
        r = self.right.data

        ctx.ctx_instruction = self
        l = l.generate(ctx)
        l.setFileLocation(self.fileLocation)

        if self.opType != WeaveBinaryOps.STRUCT_ELEMENT_ACCESS:
            r = r.generate(ctx)
            r.setFileLocation(self.fileLocation)
            ctx.ctx_instruction = None

        # check, if the value needs to be cast. If that is the case, set the right value to the cast instead.
        r = self.castValues(ctx, l, r)
        self.right.data = r

        folding = self.attempt_folding(ctx, l, r, self.opType)
        if folding:
            return folding

        inst = None
        # Different operands
        if (
                self.opType == WeaveBinaryOps.PLUS
                or self.opType == WeaveBinaryOps.MINUS
                or self.opType == WeaveBinaryOps.TIMES
                or self.opType == WeaveBinaryOps.DIVIDE
                or self.opType == WeaveBinaryOps.MODULO
        ):
            IRtype = WIRinst.convertASTarithOp(self.opType, l.dtype)
            if IRtype == WIRinst.WeaveIRarithTypes.UNKNOWN:
                errorMsg(
                    "Unknown arithmetic operation when trying to operate "
                    f"{self.opType.name} on a {l.dtype.name} type",
                    self.fileLocation,
                )

            leftOp = self.checkCommutativity(ctx, l)

            inst = WeaveIRarith(
                ctx=ctx,
                dataType=leftOp.dtype,
                opType=IRtype,
                left=leftOp.getAsOperand(),
                right=r.getAsOperand(),
            )
            inst.setFileLocation(self.fileLocation)
            if l != leftOp:
                ctx.ctx_scope.endScope()
                l = leftOp

        elif (
                self.opType == WeaveBinaryOps.SHFTLFT
                or self.opType == WeaveBinaryOps.SHFTRGT
                or self.opType == WeaveBinaryOps.BWOR
                or self.opType == WeaveBinaryOps.BWAND
                or self.opType == WeaveBinaryOps.BWXOR
                or self.opType == WeaveBinaryOps.AND
                or self.opType == WeaveBinaryOps.OR
        ):
            IRtype = WIRinst.convertASTbitwiseOp(self.opType, l.quals)
            if IRtype == WIRinst.WeaveIRbitwiseTypes.UNKNOWN:
                errorMsg(
                    "Unknown bitwise operation when trying to operate"
                    f"{self.opType.name} on a {l.quals} qualifiers",
                    self.fileLocation,
                )

            leftOp = self.checkCommutativity(ctx, l)
            inst = WeaveIRbitwise(
                ctx=ctx,
                dataType=l.dtype,
                opType=IRtype,
                left=leftOp.getAsOperand(),
                right=r.getAsOperand(),
            )
            inst.setFileLocation(self.fileLocation)
            if l != leftOp:
                ctx.ctx_scope.endScope()
        elif (
                self.opType == WeaveBinaryOps.LESSTHAN
                or self.opType == WeaveBinaryOps.LESSEQTO
                or self.opType == WeaveBinaryOps.GREATERTHAN
                or self.opType == WeaveBinaryOps.GREATEREQTO
                or self.opType == WeaveBinaryOps.EQUAL
                or self.opType == WeaveBinaryOps.DIFFERENT
        ):
            IRtype = WIRinst.convertASTcompareOp(self.opType, l.quals)
            if IRtype == WIRinst.WeaveIRbitwiseTypes.UNKNOWN:
                errorMsg(
                    "Unknown bitwise operation when trying to operate"
                    f"{self.opType.name} on a {l.quals} qualifiers",
                    self.fileLocation,
                )
            leftOp = self.checkCommutativity(ctx, l)
            inst = WeaveIRcompare(
                ctx=ctx,
                dataType=l.dtype,
                opType=IRtype,
                left=leftOp,
                right=r,
            )
            inst.setFileLocation(self.fileLocation)
            if l != leftOp:
                ctx.ctx_scope.endScope()
                l = leftOp
        elif self.opType == WeaveBinaryOps.MEMORY_DERREF:
            if not l.isPointer:
                errorMsg(
                    "Trying to dereference a variable that is not a pointer",
                    self.fileLocation,
                )
            if not l.isLocalPointer:
                errorMsg(
                    "Trying to dereference a global pointer. Only local pointers allowed",
                    self.fileLocation,
                )

            offset = r
            if isinstance(offset, WeaveIRDecl) or isinstance(offset, WeaveIRbinaryOps):
                offsetReg = offset.getAsOperand()
            else:
                offsetReg = offset

            inst = WeaveIRmemory(
                ctx=ctx,
                dataType=l.getPointeeType(),
                opType=WIRinst.WeaveIRmemoryTypes.LOADLOCAL,
                ops=[l, l.getAsOperand(), offset, offsetReg],
            )
            inst.quals.extend(l.quals)
            inst.quals.remove(WIRinst.WeaveIRqualifiers.spmem)
            inst.setFileLocation(self.fileLocation)
        elif self.opType == WeaveBinaryOps.STRUCT_ELEMENT_ACCESS:
            if not (isinstance(l.dataType, WeaveIRstructDecl) or isinstance(l.dataType, WeaveIRunionDecl)):
                errorMsg(
                    f"Trying to access a struct element from a non-struct type {l.dtype.name}",
                    self.fileLocation,
                )
            if isinstance(l, WeaveIRDecl):
                unionStruct = l.dataType
                ident = unionStruct.getField(r.get_name())
                debugMsg(3, f"Found field {ident.name} of type {ident.dtype.name}")
                return ident
            if isinstance(l, WeaveIRmemory) and l.isLocal():
                debugMsg(3, f"Found local struct access, adding element offset operand")
                accessedField: WeaveIRDecl | None = l.dataType.getField(r.get_name())
                if accessedField is None:
                    errorMsg(
                        f"Field {r.get_name()} not found in struct/union {l.dataType.name}",
                        self.fileLocation,
                    )
                accessedField.ctx = ctx
                l.setFieldDecl(accessedField)

                # Overwrite the type and qualifier as a struct element is accessed.
                retReg = l.getAsOperand()
                retReg.setType(accessedField.dtype)
                retReg.setQuals(accessedField.quals.copy())
                return l

        if isinstance(r, WeaveIRDecl):
            r.addRef(inst)
            r.setIsRead()
        if isinstance(l, WeaveIRDecl):
            l.addRef(inst)
            l.setIsWritten()

        # determine the qualifiers of the instruction
        if isinstance(l, WeaveIRDecl) and (l.isPointer or l.isLocalPointer):
            l.addQualifier(WIRinst.WeaveIRqualifiers.unsigned)
        if isinstance(r, WeaveIRDecl) and (r.isPointer or r.isLocalPointer):
            r.addQualifier(WIRinst.WeaveIRqualifiers.unsigned)
        if l.isSigned() or r.isSigned():
            inst.addQualifier(WIRinst.WeaveIRqualifiers.signed)
        else:
            inst.addQualifier(WIRinst.WeaveIRqualifiers.unsigned)

        if inst:
            tempDecl = ctx.ctx_scope.getTempDeclaration(inst.dtype, inst.quals)
            inst.setRetOp(tempDecl.curReg)
            ctx.ctx_event.addInstruction(inst)
            return inst
        else:
            errorMsg(
                f"UNREACHABLE: Unsupported binary instruction {self.opType}",
                self.fileLocation,
            )


class WeaveUnaryOperator(WeaveNode):
    def __init__(self, opType: WeaveUnaryOps, operand: tl.Node, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.UnaryOperator
        self.opType = opType
        self.operand = operand
        self.fileLocation = loc

    def to_string(self):
        return f"{str(self.type)} <{str(self.opType)}> at {str(self.fileLocation)}"

    def generate(self, ctx):
        debugMsg(
            5,
            f"generating unary operation {self.opType.name} in location {str(self.fileLocation)}",
        )
        op = self.operand.data
        op = op.generate(ctx)
        op.setFileLocation(self.fileLocation)

        inst = None

        if self.opType == WeaveUnaryOps.DERREF:
            if not op.isPointer:
                errorMsg(
                    "Trying to dereference a variable that is not a pointer",
                    self.fileLocation,
                )
            if not op.isLocalPointer:
                errorMsg(
                    "Trying to dereference a global pointer. Only local pointers allowed",
                    self.fileLocation,
                )
            offset = WeaveIRimmediate(ctx, 0, op.getPointeeType())
            inst = WeaveIRmemory(
                ctx=ctx,
                dataType=op.getPointeeType(),
                opType=WIRinst.WeaveIRmemoryTypes.LOADLOCAL,
                ops=[op, op.getAsOperand(), offset, offset],
            )
            inst.setFileLocation(self.fileLocation)
        elif self.opType == WeaveUnaryOps.NEGATE:
            if isinstance(op, WeaveIRimmediate):
                val = op.getValue()
                # Negate the immediate value
                if isinstance(val, str):
                    if val[0] == "-" and val.isnumeric():
                        val = val[1:]
                    elif val.isnumeric():
                        val = "-" + val
                    else:
                        errorMsg(f"Cannot negate {val}", self.fileLocation)
                else:
                    val = -val
                return WeaveIRimmediate(ctx, val, op.dataType)
            else:
                opType = WIRinst.WeaveIRarithTypes.IMULT
                if op.dtype.isFloatingPoint:
                    opType = WIRinst.WeaveIRarithTypes.FMULT

                inst = WeaveIRarith(
                    ctx=ctx,
                    dataType=op.dtype,
                    opType=opType,
                    left=op.getAsOperand(),
                    right=WeaveIRimmediate(ctx, -1, op.dtype),
                )
                inst.setFileLocation(self.fileLocation)

        if inst:
            if isinstance(ctx.ctx_instruction, WeaveIRDecl):
                reg = WeaveIRregister(
                        inst,
                        ctx.ctx_instruction,
                        ctx.ctx_scope.getNextRegisterNumber(),
                        WIRinst.WeaveIRregTypes.gpr,
                        inst.dtype,
                        inst.quals,
                    )
                inst.setRetOp(reg)
            else:
                # If the currently handled instruction is not an assignment, create a temporary declaration
                # This is the case, if the user implements
                #    `if((*bucket_desc_lm_ptr).lock != 0) { ...`
                # In this case, the dereference is not assigned to a variable, but a temporary register. A virtual
                # register needs to be assigned to a declaration. However, in this case, there is no declaration that
                # refers to the field that is accessed. Hence, we create a temporary declaration.
                tempDecl = ctx.ctx_scope.getTempDeclaration(inst.dtype, inst.quals)
                inst.setRetOp(tempDecl.curReg)
            ctx.ctx_event.addInstruction(inst)
            return inst
        else:
            errorMsg(
                f"UNREACHABLE: Unsupported unary instruction {self.opType}",
                self.fileLocation,
            )


class WeaveDeclarationStatement(WeaveNode):
    def __init__(
            self,
            dataType: WeaveDataTypes,
            identifier: tl.Node,
            default_val,
            loc: FileLocation,
    ):
        super().__init__(dataType)
        self.type = WeaveASTTypes.DeclarationStatement
        self.identifier = identifier
        self.default = default_val
        # By default we assume event context
        self.declType = WeaveDeclTypes.Scope
        self.fileLocation = loc

    def setDeclType(self, declType: WeaveDeclTypes):
        self.declType = declType

    def addQual(self, qual: WeaveTypeQualifier):
        self.identifier.data.quals.append(qual)

    @property
    def isExternal(self) -> bool:
        return WeaveDeclTypes.Extern == self.declType

    @property
    def isStatic(self) -> bool:
        return WeaveTypeQualifier.Static in self.identifier.data.quals

    @property
    def isConstant(self) -> bool:
        return WeaveTypeQualifier.Constant in self.identifier.data.quals

    @property
    def isGlobalConstant(self) -> bool:
        return WeaveTypeQualifier.GlobalConstant in self.identifier.data.quals

    @property
    def isPrivate(self) -> bool:
        return WeaveTypeQualifier.Private in self.identifier.data.quals

    def to_string(self):
        return f"{str(self.type)} <{str(self.dataType)}> type = {self.declType.name} default = {str(self.default.data)} at {str(self.fileLocation)}"

    def get_default(self):
        return self.default

    def get_name(self):
        return self.identifier.data.get_name()

    def _getNameSpace(self, ctx) -> str:
        namespace = ""
        if ctx.ctx_thread:
            namespace = ctx.ctx_thread.name
        if ctx.ctx_event:
            namespace += "::" + ctx.ctx_event.name
        debugMsg(
            5,
            f"Adding variable {namespace}::{self.get_name()} to program",
        )
        # We add static variables as SymbolDecl
        syms = ctx.ctx_program.findSymbolDecl(namespace, self.get_name())
        if len(syms) > 0:
            # Symbol already exists
            errorMsg(
                f"Redefinition of variable {self.get_name()} in namespace {namespace}",
                self.fileLocation,
            )
        return namespace

    def generate(self, ctx):
        debugMsg(
            5,
            f"Generating declaration statement for variable type {self.declType.name} named "
            f"{self.dataType.getName()} {self.identifier.data.nodeName} in location {str(self.fileLocation)}",
        )
        q = filter(
            lambda x: x is not (WeaveTypeQualifier.Pointer or WeaveTypeQualifier.LocalPointer),
            self.identifier.data.quals,
        )
        q = [WIRinst.convertASTqual(qual) for qual in q]

        def toStructDecl(structName: str) -> WeaveIRstructDecl:
            """Helper function to find the declaration of a struct

            Args:
                structName (str): name of the struct

            Returns:
                WeaveIRstructDecl: Struct as defined previously in the program
            """
            baseDecl = ctx.ctx_program.findDataTypeDecl(structName)
            if len(baseDecl) > 0:
                # We have to create a copy of the declaration and its state. Otherwise, we keep manipulating the
                # same attributes of the declaration of the union/struct. In case, multiple unions/structs are
                # declared, the attributes of the first one are overwritten by the second one.
                structUnion = copy.copy(baseDecl[0])
                fields = baseDecl[0].getFields()
                newFields = []
                for f in fields:
                    # copy the fields and the assigned registers
                    f = copy.copy(f)
                    # create a new list to hold the registers.
                    f.resetVirtualRegs()
                    newFields.append(f)
                structUnion.setFields(newFields)
                return structUnion
            else:
                errorMsg(
                    f"Undefined data type {self.identifier.data.nodeName}",
                    self.fileLocation,
                )

        # determining the qualifiers and data types
        if self.dataType.type == WeaveDataTypesPrimitives.UserDefined:
            ty = toStructDecl(self.dataType.getName())
        else:
            ty = WIRinst.convertASTtype(self.dataType)
        pointee_ty = None
        if WeaveTypeQualifier.Pointer in self.identifier.data.quals:
            pointee_ty = ty
            ty = WIRinst.WeaveIRtypes.ptr
        elif WeaveTypeQualifier.LocalPointer in self.identifier.data.quals:
            pointee_ty = ty
            ty = WIRinst.WeaveIRtypes.ptr
            q.append(WIRinst.WeaveIRqualifiers.spmem)

        if self.declType != WeaveDeclTypes.Global and self.isExternal:
            errorMsg(
                f"External declaration {self.identifier.data.nodeName} is not allowed inside a thread or event",
                self.fileLocation,
            )

        decl = None
        if self.declType == WeaveDeclTypes.Struct or self.declType == WeaveDeclTypes.Union:
            # This refers to the definition of the struct, and not the definition
            # of a variable that is of a given struct type
            debugMsg(
                5,
                f"Generating {self.declType.name} parameter {ctx.name}",
            )
            decl = WeaveIRDecl(ctx, self.identifier.data.nodeName, ty, pointee_ty, q)
            decl.setFileLocation(self.fileLocation)
        elif self.declType == WeaveDeclTypes.Thread:
            # Declaration inside thread
            debugMsg(5, "Generating Thread Declaration")

            # Assertions
            if not isinstance(self.default.data, WeaveEmpty):
                errorMsg(
                    f"Error generating declaration for {self.identifier.data}"
                    f" in thread {ctx.ctx_thread.name}. Thread"
                    " declarations should not be initialized",
                    self.fileLocation,
                )

            if self.dataType.type == WeaveDataTypesPrimitives.UserDefined and not (
                    WeaveTypeQualifier.Pointer in self.identifier.data.quals
                    or WeaveTypeQualifier.LocalPointer in self.identifier.data.quals
            ):
                # Pointers to struct are just regular registers.
                # In pointers structures determine the size of the pointer

                ty.setFileLocation(self.fileLocation)
                ty.assignRegisters(ctx, self.fileLocation)
                decl = WeaveIRthreadDecl(ctx, self.identifier.data.nodeName, ty, pointee_ty, q)
            else:
                reg_num = ctx.ctx_scope.getNextRegisterNumber() if not self.isStatic else None
                decl = WeaveIRthreadDecl(ctx, self.identifier.data.nodeName, ty, pointee_ty, q, reg_num)
            decl.setFileLocation(self.fileLocation)

            decl.setStatic(self.isStatic)
            decl.setPrivate(self.isPrivate)
            ctx.ctx_thread.addThreadDecl(decl)
        elif self.declType == WeaveDeclTypes.Param:
            # TODO: Implement structs as part of the operands of the event
            if self.dataType.type == WeaveDataTypesPrimitives.UserDefined:
                errorMsg(
                    "Structs not yet supported as event parameters", self.fileLocation
                )

            debugMsg(5, "Generating Parameter Declaration for event")
            if not isinstance(self.default.data, WeaveEmpty):
                errorMsg(
                    f"Error generating declaration for {self.identifier}"
                    f" in thread {ctx.ctx_thread.name}. Event {ctx.ctx_event.name}."
                    "Parameters ijn event should not be initialized",
                    self.fileLocation,
                )

            if self.isStatic:
                errorMsg(
                    f"Static parameters are not allowed for parameter {self.get_name()}",
                    self.fileLocation,
                )

            op_number = ctx.ctx_event.getNextParamRegister()
            decl = WeaveIRParamDecl(ctx, self.get_name(), ty, pointee_ty, q, op_number)
            decl.setFileLocation(self.fileLocation)
            ctx.ctx_event.addParameter(decl)
        elif self.declType == WeaveDeclTypes.Scope:
            debugMsg(
                5,
                f"Generating event local declaration {self.get_name()} inside event {ctx.ctx_event.name} in thread {ctx.ctx_thread.name}",
            )
            if self.dataType.type == WeaveDataTypesPrimitives.UserDefined and not (
                    WeaveTypeQualifier.Pointer in self.identifier.data.quals
                    or WeaveTypeQualifier.LocalPointer in self.identifier.data.quals
            ):
                # Pointers to struct are just regular registers.
                # In pointers structures determine the size of the pointer

                ty = copy.copy(ty)
                ty.setFileLocation(self.fileLocation)
                ty.assignRegisters(ctx, self.fileLocation)
                decl = WeaveIRDecl(ctx, self.identifier.data.nodeName, ty, pointee_ty, q)
            else:
                reg_num = ctx.ctx_scope.getNextRegisterNumber() if not (self.isStatic or self.isConstant) else None
                decl = WeaveIRDecl(ctx, self.get_name(), ty, pointee_ty, q, reg_num)
            decl.setFileLocation(self.fileLocation)
            decl.setStatic(self.isStatic)
            decl.setPrivate(self.isPrivate)
            ctx.ctx_scope.addDeclaration(decl)

            if not isinstance(self.default.data, WeaveEmpty):
                self.default.data.generate(ctx)
        else:
            # Global, static variables and externals
            debugMsg(5, f"Generating Global Declaration {self.get_name()}")

            # Global variables are not an WeaveIRDecl like anything else, but a comment
            # that is inserted in the output file. This is because global variables
            # are used to generate an import file for the libraries. This import
            # contains then all declared global variables.
            # Hence, they are not part of the Intermediate Representation for CodeGen
            if WeaveTypeQualifier.GlobalConstant in self.identifier.data.quals:
                # Check, if the global expression has a value
                if isinstance(self.default.data, WeaveEmpty):
                    errorMsg(
                        f"The global variable {self.get_name()} (constexp) needs to be initialized!",
                        self.fileLocation,
                    )

                value = self.default.data.value.data
                if not isinstance(value, WeaveLiteral):
                    errorMsg(
                        f"The global variable {self.get_name()} (constexp) needs to be assign an immediate value!",
                        self.fileLocation,
                    )
                decl = WeaveIRGlobalDecl(ctx, self.get_name(), ty, q, value)
                ctx.ctx_program.addDecl(decl)
                decl.setFileLocation(self.fileLocation)
                ctx.ctx_program.addSymbolConstDecl(
                    self._getNameSpace(ctx), self.get_name(), self.default.data.value
                )

            if self.isStatic:
                # Static variables must be added as symbols to the program. This allows
                # to lower them later on at the beginning of the program
                namespace = self._getNameSpace(ctx)
                ctx.ctx_program.addSymbolDecl(
                    namespace, self.get_name(), self.isExternal
                )
        return decl


class WeaveAssignStatement(WeaveNode):
    def __init__(self, dest: tl.Node, val: tl.Node, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.AssignStatement
        self.destination = dest
        self.value = val
        self.fileLocation = loc

    def setDestination(self, dest):
        self.destination = dest

    def to_string(self):
        return f"{str(self.type)} <> at {str(self.fileLocation)}"

    def generate(self, ctx):
        debugMsg(5, f"Generating assigment statement for {self.destination.data}")
        # All the registers of the val are temp registers
        ctx.ctx_scope.startScope()
        ident = self.destination.data.generate(ctx)
        ident.setFileLocation(self.fileLocation)

        # Make the ident (especially its data type) available during the generation of val
        ctx.ctx_declaration = ident
        ctx.ctx_instruction = ident

        val = self.value.data.generate(ctx)
        val.setFileLocation(self.fileLocation)
        ctx.ctx_instruction = None
        ctx.ctx_declaration = None

        if isinstance(ident, WeaveIRDecl):
            ident.setIsWritten()
            ident.addRef(val)
        if isinstance(val, WeaveIRDecl):
            val.addRef(ident)
            val.setIsRead()

        # Check if we are assigning to a parameter which is illegal
        if isinstance(ident, WeaveIRParamDecl):
            errorMsg(
                "Trying to assign a value to an operand. Operands are read only.",
                self.fileLocation,
            )

        # Check if we are reassigning a value to a constant which is illegal
        if WIRinst.WeaveIRqualifiers.const in ident.quals:
            if ident.isAssigned:
                errorMsg(
                    "Trying to reassign a value to a constant. Constants are read only.",
                    self.fileLocation,
                )
            ident.setAssigned(val)
            ctx.ctx_scope.endScope()
            return

        if isinstance(val, WeaveIRsymConst):
            debugMsg(
                5,
                f"Creating an WeaveIRmemory for loading "
                f"{val.getAsOperand().data.value} into {self.destination.data} in "
                f"location {str(self.fileLocation)}",
            )
            val = WeaveIRmemory(
                ctx=ctx,
                dataType=ident.dtype,
                opType=WIRinst.WeaveIRmemoryTypes.LOAD,
                ops=[val],
            )
            val.setFileLocation(self.fileLocation)
            val.setRetOp(
                WeaveIRregister(
                    val,
                    ident,
                    ctx.ctx_scope.getNextRegisterNumber(),
                    WIRinst.WeaveIRregTypes.gpr,
                    ident.dtype,
                    ident.quals,
                )
            )
            ctx.ctx_event.addInstruction(val)

        # Check if we need to cast the value due to different types. There are a few exceptions to this in which we take
        # the values as is without casting them:
        #   1. If the ident is a pointer, even integers might represent a pointer.
        #      Example:
        #          long* local spmPtr = LMBASE;    // ident is a Ptr, but val is an integer
        #      Example in C:
        #          int *a = 0x1234
        #   2. If the value is a pointer, it might also be represented as an unsigned long integer.
        #      Example:
        #           long* local spmPtr = LMBASE;    // ident is a Ptr
        #           long* dramPtr;                  // val is a Ptr
        #           spmPtr[0] = dramPtr;            // assigning val (Ptr) to ident (Ptr)
        #      Example in C:
        #          int *a = (int *) 0x1234
        #   3. If the value is a pointer it should be possible to assign it to an integer
        #      Example:
        #           long* local spmPtr = LMBASE;    // ident is a Ptr
        #           unsigned long someInt = spmPtr;
        if (isinstance(ident, WeaveIRDecl) and
                (isinstance(val, WeaveIRDecl) or isinstance(val, WeaveIRmemory) or isinstance(val, WeaveIRarith))
                and not (
                    val.getAsOperand().dtype == ident.dtype or
                    ident.dtype.isPointer and val.getAsOperand().dtype.isInteger and not val.getAsOperand().isSigned()
                    or val.getAsOperand().dtype.isPointer and ident.dtype.isInteger and not ident.isSigned()
                )
        ):
            debugMsg(
                3,
                f"Inserting casting between operands during assignment "
                f"operation for {val.dtype} to {ident.dtype}",
            )

            if ident.dtype.isPointer or val.dtype.isPointer:
                # If we end up here, then we wanted to cast a ptr to a type other than unsigned long or vice versa.
                errorMsg(f"Casting from {val.dtype} ({val.quals}) to {ident.dtype} ({ident.quals}) is not allowed."
                         f" The LHS needs to be of type unsigned long.", self.fileLocation)

            # Casting an immediate is just changing the type
            if isinstance(val, WeaveIRimmediate):
                debugMsg(
                    3,
                    f"Changing type for immediate for assignment from default {val.dtype} to {ident.dtype}",
                )
                # No need to insert cast, let's just re-interpret the value
                val.setType(ident.dtype)
            else:
                tempDecl = ctx.ctx_scope.getTempDeclaration(ident.dtype, ident.quals)
                tempReg = tempDecl.curReg

                # Insert a new cast value that will now be giving the value
                # that needs to be assigned
                val = WeaveIRcast(
                    ctx=ctx,
                    out_type=ident.dtype,
                    inReg=val.getAsOperand(),
                )
                val.setFileLocation(self.fileLocation)
                val.setRetOp(tempReg)
                ctx.ctx_event.addInstruction(val)

        if isinstance(val, WeaveIRimmediate) or (
                not isinstance(ident, WeaveIRmemory) and isinstance(val, WeaveIRDecl)
        ):
            debugMsg(
                5,
                f"Creating an WeaveIRmemory for loading "
                f"{val.getAsOperand().name} into {self.destination.data} in "
                f"location {str(self.fileLocation)}",
            )
            newMemInstr = WeaveIRmemory(
                ctx=ctx,
                dataType=ident.dtype,
                opType=WIRinst.WeaveIRmemoryTypes.LOAD,
            )
            newMemInstr.setValueToStore(val.getAsOperand())
            val = newMemInstr
            val.setFileLocation(self.fileLocation)
            if isinstance(ident, WeaveIRDecl):
                reg = ctx.ctx_scope.getNextRegister(ident, ident.dtype, ident.quals)
                ident.addReg(reg)
                val.setRetOp(ident.curReg)
            else:
                decl = ctx.ctx_scope.getTempDeclaration(ident.dtype, ident.quals)
                val.setRetOp(decl.curReg)
            ctx.ctx_event.addInstruction(val)

        if isinstance(ident, WeaveIRmemory):
            if not ident.isLocal():
                errorMsg("Trying to store on a global pointer", self.fileLocation)
            debugMsg(5, f"Changing rhs operation to lhs operation for {ident}")
            ident.setInstType(WIRinst.WeaveIRmemoryTypes.STORELOCAL)
            ctx.ctx_scope.removeDeclaration(ident.getReturnReg().getDecl())
            ident.setRetOp(None)
            ident.setValueToStore(val.getAsOperand())

            # Relocate the dereferencing memory instruction to the end of the BB. Consider the following case, in which
            # the dereferencing happens on the LHS:
            #    a[0] = 3;
            # Once the dereferencing completed and the corresponding movrl instruction is generated, the RHS is
            # examined, which results in a loading of the immediate 3. Hence, the sequence is:
            #    movrl X- 0(a) 0 8
            #    movir Xd, 3
            # As you can see, we do not have the Xd ready by the time we dereference. Hence, the dereferencing needs to
            # be pushed down to after the movir:
            #    movir Xd, 3
            #    movrl Xd 0(a) 0 8
            # Since the RHS could be rather complex, we need to push the dereferencing to the end of the BB after the
            # generation of the RHS completed.
            ctx.ctx_event.addOrMoveLastInstruction(ident)
        else:
            returnReg = val.getAsOperand()
            if isinstance(ident, WeaveIRDecl):
                # This if-branch is executed, if there is an arithmetic on the RHS. Generating the arithmetic
                # uses temporary registers by default. However, this is an assignment. So the virtual register carrying
                # the result of the arithmetic computation, is moved to the declaration that the value is assigned to.
                # Hence, the temporary declaration is to be removed, since its virtual register was just moved.
                returnDecl = returnReg.getDecl()
                if returnDecl.isTemp:
                    ctx.ctx_scope.removeDeclaration(returnDecl)
            ident.setRetOp(returnReg)

        # Finished generating. Let's restart the temp virtualRegs
        ctx.ctx_scope.endScope()
        return [ident]


class ConditionMixin:
    """
    This class is a Mixin.
    It is used, when the control flow diverges based on a condition. This is the case in while, for, and if statements.
    """

    def generateCondition(
            self,
            ctx: WeaveIRbase,
            condition: tl.Node,
            falseOrPostBlock: WeaveIRbasicBlock,
            fileLocation: FileLocation,
    ) -> Optional[bool]:
        """
        Generate the condition for a conditional statement. This function is used to generate the condition for a
        conditional statement. The condition is evaluated and the appropriate block is jumped to. If the condition is
        always true or always false, then the function returns the value of the condition without generating source
        code to evaluate the condition during runtime. If the condition is neither always true nor always
        false, then the function generates the condition and returns None.
        @param ctx:
        @type ctx: WeaveIRbase
        @param condition: The node containing the condition
        @type condition: tl.Node
        @param falseOrPostBlock: Either the false block, if it exists, or the block after the condition
        @type falseOrPostBlock: WeaveIRbasicBlock
        @param fileLocation: Location of the condition in the source code
        @type fileLocation: FileLocation
        @return: The value of the condition if it is always true or always false, otherwise None
        @rtype: bool | None
        """
        # We expect 1 expression to be returned
        condition_instruction = condition.data.generate(ctx)[0]

        # If the condition instruction has been folded (e.g. 1 == 1), then we can just evaluate the condition and jump
        # to the appropriate block
        if isinstance(condition_instruction, WeaveIRimmediate):
            return bool(condition_instruction.getOriginalValue())
        else:
            branch_instruction = WeaveIRbranch(
                condition_instruction.ctx,
                WIRinst.WeaveIRBranchTypes.CONDITIONALEQ,
                falseOrPostBlock,
                condition_instruction,
                WeaveIRimmediate(ctx, 0, condition_instruction.dtype),
            )
            branch_instruction.setFileLocation(fileLocation)
            if isinstance(condition_instruction, WeaveIRcompare):
                condition_instruction.setBranchInstr(branch_instruction)
            else:
                ctx.ctx_event.addInstruction(branch_instruction)
        return None

    def getDeclFromInstruction(self, instruction) -> Optional[list]:
        if instruction is None:
            return None
        decl = []
        if isinstance(instruction, WeaveIRregister):
            decl = [instruction.getDecl()]
        elif isinstance(instruction, WeaveIRDecl):
            decl = [instruction]
        elif isinstance(instruction, WeaveIRinstruction):
            for op in instruction.getInOps():
                addDecl = self.getDeclFromInstruction(op)
                if addDecl is not None:
                    decl.extend(addDecl)
        return decl

    def getUsedDecl(self, ctx, numBBbefore: int) -> list:
        """ Get a list of declarations that have been used in the newly added basic blocks. Only declarations are added
        which are defined in the current scope. """

        foundDecl = []
        # identify the newly added basic blocks
        newBasicBlocks = ctx.ctx_event.basic_blocks[numBBbefore:]
        for bb in newBasicBlocks:
            for inst in bb.instructions:
                foundDecl.extend(self.getDeclFromInstruction(inst))

        # remove double entries
        foundDecl = list(set(foundDecl))
        return foundDecl




    def generatePhis(self, ctx: WeaveIRbase, insts: list, fileLocation: FileLocation) -> None:
        """ Generate a phi instruction for the current basic block. This is used to merge the control flow from
        multiple basic blocks into the current basic block.
        @param ctx: The current context
        @type ctx: WeaveIRbase
        @param insts: The instructions that have been generated in the previous basic blocks. This list is a flat
        structure, meaning that it contains instructions that have been generated in the if as well as else block, in
        case of an if-branch.
        @type insts: list
        @param fileLocation: The location of the phi instruction in the source code
        @type fileLocation: FileLocation
        """
        alreadyHandledDeclarations = []

        for inst in insts:
            if isinstance(inst, WeaveIRDecl) or isinstance(inst, WeaveIRphi):
                # if the decl has already been handled, do not generate another phi node for it
                if (inst in alreadyHandledDeclarations or isinstance(inst, WeaveIRthreadDecl) or
                        isinstance(inst, WeaveIRParamDecl)):
                    continue

                if isinstance(inst, WeaveIRphi):
                    decl = inst.getDeclaration()
                else:
                    decl = inst

                # Only, if the decl has been defined in the current scope, we generate a Phi node.
                # for instance, in case, this setting has been implemented:
                #    if (a > b) {
                #        int c = 3;
                #    }
                # We do not need a phi node for c at the end of the if statement.
                if not decl in ctx.ctx_scope.getAllCurrentDeclarations():
                    alreadyHandledDeclarations.append(inst)
                    continue

                phi = WeaveIRphi(ctx=ctx, decl=decl)
                reg = WeaveIRregister(ctx, decl, ctx.ctx_scope.getNextRegisterNumber(), WIRinst.WeaveIRregTypes.gpr,
                                      WIRinst.WeaveIRtypes.i64)
                phi.setFileLocation(fileLocation)
                phi.setRetOp(reg)
                inst.setRetOp(reg)
                ctx.ctx_event.addInstruction(phi)
                alreadyHandledDeclarations.append(inst)


class WeaveIfStatement(WeaveNode, ConditionMixin):
    def __init__(
            self, condition: tl.Node, trueE: tl.Node, falseE: tl.Node, loc: FileLocation
    ):
        super().__init__()
        self.type = WeaveASTTypes.IfStatement
        self.condition = condition
        self.trueExp = trueE
        self.falseExp = falseE
        self.fileLocation = loc

    def to_string(self):
        return f"{str(self.type)} <> at {str(self.fileLocation)}"

    def generate(self, ctx: WeaveIRevent):
        numBBbefore = len(ctx.ctx_event.basic_blocks)
        trueLabel = ctx.getLabel("if", "true")
        falseLabel = ctx.getLabel("if", "false")
        postLabel = ctx.getLabel("if", "post")

        trueSection = WeaveIRbasicBlock(ctx, trueLabel)
        falseSection = WeaveIRbasicBlock(ctx, falseLabel)
        postSection = WeaveIRbasicBlock(ctx, postLabel)

        # Copy the outgoing edges of the condition to the post BB, so that we know, how the program flow continues.
        condSection = ctx.ctx_event.curBB
        for outEdge in condSection.out_edges:
            postSection.addOutEdge(outEdge)

        # Delete all outgoing edges from the if condition, as we create the outEdges to the true and false/post BBs.
        condSection.resetOutEdges()

        if self.falseExp and len(self.falseExp) > 0:
            alwaysTrue = self.generateCondition(ctx, self.condition, falseSection, self.fileLocation)
        else:
            alwaysTrue = self.generateCondition(ctx, self.condition, postSection, self.fileLocation)

        lastBBCondSection = ctx.ctx_event.curBB  # This is the last BB of the condition section

        if alwaysTrue is not None:
            def buildBlock(section: WeaveIRbasicBlock, expressions: list):

                ctx.ctx_event.addBasicBlock(section)  # This is the last BB of the true section
                section.setFileLocation(self.fileLocation)

                lastBBCondSection.addOutEdge(section)
                section.addInEdge(lastBBCondSection)
                for i, expression in enumerate(expressions):
                    currentInstructions = helper.flatten(expression.data.generate(ctx))

                    if (i == 0 and currentInstructions is not None and isinstance(currentInstructions, list)
                            and len(currentInstructions) > 0 and currentInstructions[0] is not None):
                        firstInstruction = currentInstructions[0]
                        if isinstance(firstInstruction, WeaveIRassembly):
                            # If the first instruction of the assembly instruction contains a label, we have to rename
                            # the BB
                            if len(firstInstruction.getLines()) > 0:
                                pos = firstInstruction.getLines()[0].find(":")
                                if pos != -1:
                                    label = firstInstruction.getLines()[0][:pos]
                                    section.setName(label)
                                    firstInstruction.getLines()[0] = firstInstruction.getLines()[0][pos + 1:].strip()

                lastBB = ctx.ctx_event.curBB
                postSection.addInEdge(lastBB)
                lastBB.addOutEdge(postSection)

            if alwaysTrue:
                # If the condition is always true, just build the true section. Nothing else.
                buildBlock(trueSection, self.trueExp)
            else:
                # If the condition is evaluated to be always false, just build the false section. Nothing else.
                if self.falseExp and len(self.falseExp) > 0:
                    buildBlock(falseSection, self.falseExp)
                else:
                    # if the condition is always false and there is no false section, then we just need to add the
                    # edges from the condition to the post section
                    postSection.addInEdge(lastBBCondSection)
                    lastBBCondSection.addOutEdge(postSection)
        else:
            # Generate the true block
            ctx.ctx_event.addBasicBlock(trueSection)  # This is the last BB of the true section
            trueSection.setFileLocation(self.fileLocation)
            lastBBCondSection.addOutEdge(trueSection)
            trueSection.addInEdge(lastBBCondSection)
            for exp in self.trueExp:
                exp.data.generate(ctx)

            # Generate instructions for the false block
            if self.falseExp and len(self.falseExp) > 0:
                # Add label to post block and an unconditional jump from the end of the true block
                jump_to_post_instruction = WeaveIRbranch(
                    ctx, WIRinst.WeaveIRBranchTypes.UNCONDITIONAL, postSection
                )
                jump_to_post_instruction.setFileLocation(self.fileLocation)
                ctx.ctx_event.addInstruction(jump_to_post_instruction)
                lastBBTrueSection = ctx.ctx_event.curBB
                postSection.addInEdge(lastBBTrueSection)
                lastBBTrueSection.addOutEdge(postSection)

                # Create the edges for the else block
                ctx.ctx_event.addBasicBlock(falseSection)
                falseSection.setFileLocation(self.fileLocation)

                for exp in self.falseExp:
                    exp.data.generate(ctx)

                lastBBFalseSection = ctx.ctx_event.curBB
                lastBBCondSection.addOutEdge(falseSection)
                falseSection.addInEdge(lastBBCondSection)
                postSection.addInEdge(lastBBFalseSection)
                lastBBFalseSection.addOutEdge(postSection)
            else:
                lastBBTrueSection = ctx.ctx_event.curBB
                postSection.addInEdge(lastBBTrueSection)
                lastBBTrueSection.addOutEdge(postSection)
                lastBBCondSection.addOutEdge(postSection)
                postSection.addInEdge(lastBBCondSection)

            usedDecl = self.getUsedDecl(ctx, numBBbefore)

            # Adding post basic block
            ctx.ctx_event.addBasicBlock(postSection)
            postSection.setFileLocation(self.fileLocation)

            # Add the declarations used in the branch as phi nodes
            self.generatePhis(ctx, usedDecl, self.fileLocation)


class WeaveWhileStatement(WeaveNode, ConditionMixin):
    def __init__(self, condition: tl.Node, body: list, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.WhileStatement
        self.condition = condition
        self.body = body
        self.fileLocation = loc

    def to_string(self):
        return f"{str(self.type)} <> at {str(self.fileLocation)}"

    def generate(self, ctx):
        numBBbefore = len(ctx.ctx_event.basic_blocks)
        conditionLabel = ctx.getLabel("while", "condition")
        whileBodyLabel = ctx.getLabel("while", "body")
        postLabel = ctx.getLabel("while", "post")

        conditionSection = WeaveIRbasicBlock(ctx, conditionLabel)
        whileBodySection = WeaveIRbasicBlock(ctx, whileBodyLabel)
        postSection = WeaveIRbasicBlock(ctx, postLabel)
        ctx.setCtxLoop(conditionSection, whileBodySection, postSection)

        whileBodySection.setFileLocation(self.fileLocation)
        postSection.setFileLocation(self.fileLocation)

        prevBlock = ctx.ctx_event.curBB
        for outEdge in prevBlock.out_edges:
            postSection.addOutEdge(outEdge)
        prevBlock.resetOutEdges()

        ctx.ctx_event.addBasicBlock(conditionSection)
        conditionSection.setFileLocation(self.fileLocation)
        prevBlock.addOutEdge(conditionSection)
        conditionSection.addInEdge(prevBlock)

        self.generateCondition(ctx, self.condition, postSection, self.fileLocation)
        lastBBConditionSection = ctx.ctx_event.curBB

        ctx.ctx_event.addBasicBlock(whileBodySection)
        whileBodySection.addInEdge(lastBBConditionSection)
        lastBBConditionSection.addOutEdge(whileBodySection)

        for exp in self.body:
            exp.data.generate(ctx)

        jmp_to_condition_block_instruction = WeaveIRbranch(
            ctx, WIRinst.WeaveIRBranchTypes.UNCONDITIONAL, conditionSection
        )
        jmp_to_condition_block_instruction.setFileLocation(self.fileLocation)
        ctx.ctx_event.addInstruction(jmp_to_condition_block_instruction)

        lastBBBodySection = ctx.ctx_event.curBB
        lastBBBodySection.addOutEdge(conditionSection)
        conditionSection.addInEdge(lastBBBodySection)

        usedDecl = self.getUsedDecl(ctx, numBBbefore)

        ctx.ctx_event.addBasicBlock(postSection)
        lastBBConditionSection.addOutEdge(postSection)
        postSection.addInEdge(lastBBConditionSection)
        ctx.popCtxLoop()
        self.generatePhis(ctx, usedDecl, self.fileLocation)


class WeaveForStatement(WeaveNode, ConditionMixin):
    def __init__(
            self,
            init: list,
            termCond: tl.Node,
            increment: tl.Node,
            body: list,
            loc: FileLocation,
    ):
        super().__init__()
        self.type = WeaveASTTypes.ForStatement
        self.init = init
        self.endCondition = termCond
        self.increment = increment
        self.body = body
        self.fileLocation = loc

    def to_string(self):
        return f"{str(self.type)} <> at {str(self.fileLocation)}"

    def generate(self, ctx):
        numBBbefore = len(ctx.ctx_event.basic_blocks)

        # Add for-loop init to the prev_block
        for exp in self.init:
            exp.data.generate(ctx)

        conditionLabel = ctx.getLabel("for", "condition")
        bodyLabel = ctx.getLabel("for", "body")
        postLabel = ctx.getLabel("for", "post")

        conditionSection = WeaveIRbasicBlock(ctx, conditionLabel)
        bodySection = WeaveIRbasicBlock(ctx, bodyLabel)
        postSection = WeaveIRbasicBlock(ctx, postLabel)
        ctx.setCtxLoop(conditionSection, bodySection, postSection)

        prevBB = ctx.ctx_event.curBB

        for outEdge in prevBB.out_edges:
            postSection.addOutEdge(outEdge)
        prevBB.resetOutEdges()

        ctx.ctx_event.addBasicBlock(conditionSection)
        conditionSection.setFileLocation(self.fileLocation)
        prevBB.addOutEdge(conditionSection)
        conditionSection.addInEdge(prevBB)


        # Generate the condition
        self.generateCondition(ctx, self.endCondition, postSection, self.fileLocation)
        lastBBConditionSection = ctx.ctx_event.curBB

        # Make a body block with its connections and add body instructions
        ctx.ctx_event.addBasicBlock(bodySection)
        bodySection.setFileLocation(self.fileLocation)
        bodySection.addInEdge(lastBBConditionSection)
        lastBBConditionSection.addOutEdge(bodySection)

        for exp in self.body:
            exp.data.generate(ctx)

        # Add increment at the end of the body
        self.increment.data.generate(ctx)
        jump_instruction = WeaveIRbranch(ctx, WIRinst.WeaveIRBranchTypes.UNCONDITIONAL, conditionSection)
        jump_instruction.setFileLocation(self.fileLocation)
        ctx.ctx_event.addInstruction(jump_instruction)

        # retrieve all used declarations in the added basic blocks
        usedDecl = self.getUsedDecl(ctx, numBBbefore)

        lastBBBodySection = ctx.ctx_event.curBB
        lastBBBodySection.addOutEdge(conditionSection)
        conditionSection.addInEdge(lastBBBodySection)

        # Make a post block and add label
        ctx.ctx_event.addBasicBlock(postSection)
        postSection.setFileLocation(self.fileLocation)
        lastBBConditionSection.addOutEdge(postSection)
        postSection.addInEdge(lastBBConditionSection)
        ctx.popCtxLoop()
        self.generatePhis(ctx, usedDecl, self.fileLocation)


class WeaveBreakStatement(WeaveNode):
    def to_string(self):
        return f"{str(self.type)} <> at {str(self.fileLocation)}"

    def __init__(self, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.Break
        self.fileLocation = loc

    def generate(self, ctx):
        debugMsg(5, f"Generating break statement in location {str(self.fileLocation)}")
        if not ctx.inLoop():
            errorMsg("Break statement outside of loop", self.fileLocation)
        ctx.ctx_event.curBB.addOutEdge(ctx.getPostBlock())
        ctx.getPostBlock().addInEdge(ctx.ctx_event.curBB)

        jump_instruction = WeaveIRbranch(ctx, WIRinst.WeaveIRBranchTypes.UNCONDITIONAL, ctx.getPostBlock())
        jump_instruction.setFileLocation(self.fileLocation)
        ctx.ctx_event.addInstruction(jump_instruction)


class WeaveContinueStatement(WeaveNode):
    def to_string(self):
        return f"{str(self.type)} <> at {str(self.fileLocation)}"

    def __init__(self, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.Continue
        self.fileLocation = loc

    def generate(self, ctx):
        debugMsg(5, f"Generating continue statement in location {str(self.fileLocation)}")
        if not ctx.inLoop():
            errorMsg("Continue statement outside of loop", self.fileLocation)
        ctx.ctx_event.curBB.addOutEdge(ctx.getCondBlock())
        ctx.getCondBlock().addInEdge(ctx.ctx_event.curBB)

        jump_instruction = WeaveIRbranch(ctx, WIRinst.WeaveIRBranchTypes.UNCONDITIONAL, ctx.getCondBlock())
        jump_instruction.setFileLocation(self.fileLocation)
        ctx.ctx_event.addInstruction(jump_instruction)


class WeaveCall(WeaveNode):
    def __init__(self, name: str, args: list, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.Call
        self.name = name
        self.arguments = args
        self.fileLocation = loc

    def to_string(self):
        return f"{str(self.type)} <> name = {self.name} num_params {len(self.arguments)} at {str(self.fileLocation)}"

    def generate(self, ctx):
        debugMsg(
            5,
            f"Generating call statement for {self.name} with {len(self.arguments)} in location "
            f"{str(self.fileLocation)}",
        )

        call = WeaveIRcall(ctx, name=self.name)
        call.setFileLocation(self.fileLocation)

        # Generate all the args
        for arg in self.arguments:
            arg = arg.data.generate(call)
            # If it is a struct, we need to pass the size of the struct.
            if isinstance(arg, WeaveIRstructDecl):
                sym = WeaveIRsymPtr(ctx=ctx, namespace="", nameSymbol=arg.name)
                sym.dataType = WIRinst.WeaveIRuserDefinedType(arg.getSize(self.fileLocation),
                                                              WIRinst.WeaveIRtypes.struct)
                call.addInOperand(sym)
            else:
                call.addInOperand(arg.getAsOperand())

        # Check if intrinsic
        intrs = ctx.ctx_program.getIntrinsicFuncs(self.name)
        if len(intrs) == 0:
            warningMsg(
                f"Function {self.name} not found as intrinsic functions. "
                "Currently, there is no support for other functions other than intrinsics"
            )
            # TODO: Probably it makes sense to think of a common interface for python defined
            # functions. Such that these can be implemented

        selectedInputTypes = None

        for intr in intrs:
            for inputTypes in intr.getInputTypes():
                debugMsg(
                    3,
                    f"Trying to match function {call.name}{[i.name for i in call.getInOpTypes()]}"
                    f" with {intr.getName()}{[i.name for i in inputTypes]}",
                )
                all_ops = True

                if not intr.variadicArguments():
                    if len(call.getInOpTypes()) != len(inputTypes):
                        continue

                    # Check each operand, but convert immediate values to match
                    # the function call type
                    for num, ops in enumerate(zip(call.getInOpTypes(), inputTypes)):
                        # We do not care about void types, they can be anything
                        if ops[1] == WIRinst.WeaveIRtypes.void:
                            continue

                        if ops[0] != ops[1]:
                            debugMsg(4, f"Could not match because {ops[0]} != {ops[1]}")
                            all_ops = False
                            break

                # All operands match?
                if all_ops:
                    debugMsg(4, f"Operands match! {intr}")
                    selectedInputTypes = inputTypes
                    if intr.earlyInline():
                        return intr(call).generateWeaveIR()
                    if intr.getReturnType() is not WIRinst.WeaveIRtypes.void:
                        if ctx.ctx_declaration is None:
                            tempDecl = ctx.ctx_scope.getTempDeclaration(
                                intr.getReturnType(), [WIRinst.WeaveIRqualifiers.unsigned]
                            )
                            tempReg = tempDecl.curReg
                        else:
                            tempReg = ctx.ctx_scope.getNextRegister(ctx.ctx_declaration, intr.getReturnType(),
                                                                [WIRinst.WeaveIRqualifiers.unsigned])
                            ctx.ctx_declaration.addReg(tempReg)
                        call.setRetOp(tempReg)
                    call.setType(intr.getReturnType())
                    call.setDefinition(intr, selectedInputTypes)
                    break

            if selectedInputTypes:
                break

        if not selectedInputTypes:
            candidates = []
            for intr in intrs:
                for it in intr.getInputTypes():
                    candidates.append(f"{intr.getName()}({[t.name for t in it]})")

            errorMsg(
                f"Definition for Function {call.name} with input parameters "
                f"{[i.name for i in call.getInOpTypes()]} not found."
                f" Candidates are {', '.join(candidates)}",
                self.fileLocation,
            )

        ctx.ctx_event.addInstruction(call)
        return call


class WeaveAssemblyOperand(WeaveNode):
    def __init__(
            self, sym_name: str, constraints: str, operandExpr: str, loc: FileLocation
    ):
        super().__init__()
        self.type = WeaveASTTypes.AssemblyOperand
        # Name of the variable inside the assembly code section (e.g. %0 or %[someVar])
        self.symbolName = sym_name
        # Determines if it is input, output, label, etc.
        self.constraints = constraints
        # Name of the symbol or value in the UDWeave world
        self.opExpr = operandExpr
        self.fileLocation = loc

    def getSymbolName(self):
        return self.symbolName

    def setSymbolName(self, sym):
        self.symbolName = sym

    def to_string(self):
        return (f'{str(self.type)} <{self.symbolName}> "{self.constraints}" at {str(self.fileLocation)}: '
                f'{self.opExpr.data}')

    def generate(self, ctx):
        if not self.symbolName:
            errorMsg(
                "Invalid WeaveAssemblyOperand. It should have a symbol name",
                self.fileLocation,
            )
        allConstr = []
        for constr in self.constraints:
            if constr not in WIRinst.WeaveIRasmConstraints.getList():
                errorMsg(
                    f"Unknown constraint {constr} when lowering asm block",
                    self.fileLocation,
                )
            allConstr.append(WIRinst.WeaveIRasmConstraints(constr))

        decl = self.opExpr.data.generate(ctx)
        op = WeaveIRasmOperand(ctx, self.symbolName, allConstr, decl)
        op.setFileLocation(self.fileLocation)
        return op


class WeaveAssembly(WeaveNode):
    def __init__(self, body: str, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.Assembly
        self.body = body
        self.fileLocation = loc
        self._nativeInline = False
        self.operands = []

    @property
    def nativeInline(self) -> bool:
        return self._nativeInline

    def setNativeInline(self, val: bool):
        self._nativeInline = val

    def addOperand(self, operand: WeaveAssemblyOperand):
        self.operands.append(operand)

    def to_string(self):
        return f"{str(self.type)} <native = {self.nativeInline}> at {str(self.fileLocation)}: {self.body}"

    def generate(self, ctx):
        debugMsg(6, f"Generating WeaveAssembly with {len(self.operands)} operands")
        wirAss = WeaveIRassembly(ctx, self.body)
        wirAss.setFileLocation(self.fileLocation)
        wirAss.setNativeInline(self.nativeInline)
        for op in self.operands:
            wirAss.addOperand(op.data.generate(wirAss))
        wirAss.resolveOperands()
        if ctx.ctx_scope.ctx_event:
            debugMsg(8, "Adding assembly block to the event")
            ctx.ctx_scope.ctx_event.addAssemblyBlock(wirAss)
        elif ctx.ctx_scope.ctx_thread:
            debugMsg(8, "Adding assembly block to the thread")
            ctx.ctx_scope.ctx_thread.addAssemblyBlock(wirAss)
            # There are no actions in the thread,
            # so we cannot inline the assembly as an action
            wirAss.setNativeInline(True)
        else:
            debugMsg(8, "Adding assembly block to the program")
            ctx.ctx_program.addAssemblyBlock(wirAss)
            # There are no actions in the top of the program.
            # We cannot inline the assembly as an action
            wirAss.setNativeInline(True)
        return wirAss


class WeaveCast(WeaveNode):
    def __init__(
            self,
            source_type: WeaveDataTypes,
            dest_type: WeaveDataTypes,
            operand: tl.Node,
            loc: FileLocation,
    ):
        super().__init__()
        self.type = WeaveASTTypes.CastOperation
        self._srcType = source_type
        self._dstType = dest_type
        self.operand = operand
        self.fileLocation = loc

    @property
    def srcType(self) -> WeaveDataTypes:
        return self._srcType

    @property
    def dstType(self) -> WeaveDataTypes:
        return self._dstType

    def to_string(self):
        return f"{str(self.type)} <{str(self.dstType)}> from = {str(self.srcType)} at {str(self.fileLocation)}"

    def generate(self, ctx):
        pass


class WeaveComment(WeaveNode):
    def __init__(self, comment: str, loc: FileLocation):
        super().__init__()
        self.type = WeaveASTTypes.Comment
        self.comment = comment
        self.loc = loc

    def to_string(self):
        return f";; {self.comment}"

    def generate(self, ctx):
        comm = WeaveIRcomment(ctx, self.comment)
        comm.setFileLocation(self.fileLocation)
        if ctx.ctx_event:
            debugMsg(8, "Adding a comment to the event")
            ctx.ctx_event.addComment(comm)
        elif ctx.ctx_thread:
            debugMsg(8, "Adding a comment to the thread")
            ctx.ctx_thread.addComment(comm)
        else:
            debugMsg(8, "Adding a comment to the program")
            ctx.ctx_program.addComment(comm)


class WeaveAST(object):
    def __init__(self):
        self.astTree = tl.Tree()
        self.program = self.astTree.create_node(data=WeaveProgram())
        self.currentScope = None

    def __str__(self):
        return self.astTree.show(data_property="as_string", stdout=None)

    @property
    def scope(self):
        return self.currentScope

    def setProgramName(self, name):
        self.program.data.setName(name)

    def create_node(self, nodeData: WeaveNode) -> tl.Node:
        return self.astTree.create_node(data=nodeData, parent=self.program)

    def set_parent(self, node, destination):
        self.astTree.move_node(node.identifier, destination.identifier)

    def print(self):
        self.astTree.show(data_property="as_string")
