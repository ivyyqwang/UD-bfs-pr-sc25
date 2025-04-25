import ply.yacc as yacc
import frontend.lexer as lexer
from frontend.ASTweave import *
from Weave.debug import *
import os


# Grammar rules and actions
class WeaveParser(lexer.WeaveLexer):
    def p_program(self, p):
        """
        program : program_sections
        """
        prog_sections = p[1]
        p[0] = self.astTree.program

        # Set parent for all sections
        for s in prog_sections:
            self.astTree.set_parent(node=s, destination=p[0])
            if isinstance(s.data, WeaveDeclarationStatement):
                s.data.setDeclType(WeaveDeclTypes.Global)

        self.astTree.program.data.setProgramSections(prog_sections)

    def p_program_sections(self, p):
        """
        program_section : threads
                          | templates
                          | comments
                          | assembly-statement
                          | struct-definitions
                          | extern-declarations
                          | declaration-statements
                          | preproc-comment
        """
        p[0] = p[1]

    def p_statement(self, p):
        """
        statement : assign-statement
                | declaration-statement
                | expression SEMICOLON
                | if-statement SEMICOLON
                | if-statement
                | while-statement
                | for-statement
                | assembly-statement
                | comments
                | preproc-comment
                | break-statement
                | continue-statement
        """
        p[0] = p[1]

    def p_event_name(self, p):
        """
        event-name : ID NAMESPACE event-name
                     | ID

        """
        if len(p) == 2:
            p[0] = {"name": p[1], "namespace": ""}
        else:
            p[3]["namespace"] = (
                (p[1] + "::" + p[3]["namespace"]) if p[3]["namespace"] != "" else p[1]
            )
            p[0] = p[3]

    def p_event_declaration(self, p):
        """
        event-declaration : EVENT event-name LPAREN params RPAREN
                          | EVENT event-name LPAREN RPAREN
        """
        params = []

        if len(p) == 6:
            params = p[4]

        # Set all params declarations to type Param
        for param in params:
            param.data.setDeclType(WeaveDeclTypes.Param)

        # Expected dict {"name": "event_name", "namespace": "namespace"}
        name = p[2]["name"]
        namespace = p[2]["namespace"]

        node = WeaveEvent(
            name=name,
            params=params,
            statements=[],
            loc=FileLocation(p.lineno(2), p.lexpos(2), self._fileMgr),
        )

        if namespace != "":
            node.setNamespace(namespace)

        p[0] = self.astTree.create_node(node)

        for param in params:
            self.astTree.set_parent(node=param, destination=p[0])

    def p_event(self, p):
        """
        event : event-scope
        """
        self.__createScopeHeader(p)

    def p_event_scope(self, p):
        """
        event-scope : event-declaration LCBRACKET event-body RCBRACKET
                      | event-declaration LCBRACKET RCBRACKET
                      | event-declaration SEMICOLON
        """

        body = []

        if len(p) == 5:
            body = p[3]

        p[0] = p[1]
        p[0].data.setBody(body)

        if len(p) == 3:
            p[0].data.setIsInterface(True)

        for stmt in body:
            self.astTree.set_parent(node=stmt, destination=p[0])

    def p_event_body(self, p):
        """
        event-body : statements
        """
        p[0] = p[1]

    def p_params(self, p):
        """
        params : params COMMA qual_type_specifier declarator
                | qual_type_specifier declarator
        """
        empty_default = self.astTree.create_node(WeaveEmpty())

        if len(p) == 3:
            ty = p[1][0]
            qual = (p[1][1]).copy()
            if p[2][1] == "pointer":
                qual.append(WeaveTypeQualifier.Pointer)
            elif p[2][1] == "local-pointer":
                qual.append(WeaveTypeQualifier.LocalPointer)

            # A param should not be named as a reserved keyword
            self.checkIsType(
                p[2][0],
                throw=True,
                loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
            )
            astTreeNode = self.astTree.create_node(
                WeaveIdentifier(
                    dataType=ty,
                    quals=qual,
                    name=p[2][0],
                    loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
                )
            )
            decl = self.astTree.create_node(
                WeaveDeclarationStatement(
                    dataType=ty,
                    identifier=astTreeNode,
                    default_val=empty_default,
                    loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
                )
            )
            self.astTree.set_parent(astTreeNode, decl)
            self.astTree.set_parent(empty_default, decl)

            p[0] = [decl]
        else:
            ty = p[3][0]
            qual = (p[3][1]).copy()
            if p[4][1] == "pointer":
                qual.append(WeaveTypeQualifier.Pointer)
            elif p[4][1] == "local-pointer":
                qual.append(WeaveTypeQualifier.LocalPointer)

            # A param should not be named as a reserved keyword
            self.checkIsType(
                p[4][0],
                throw=True,
                loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
            )
            astTreeNode = self.astTree.create_node(
                WeaveIdentifier(
                    dataType=ty,
                    quals=qual,
                    name=p[4][0],
                    loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
                )
            )

            decl = self.astTree.create_node(
                WeaveDeclarationStatement(
                    dataType=ty,
                    identifier=astTreeNode,
                    default_val=empty_default,
                    loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
                )
            )
            self.astTree.set_parent(astTreeNode, decl)
            self.astTree.set_parent(empty_default, decl)
            p[0] = p[1] + [decl]

    def p_qual_type_specifier(self, p):
        """
        qual_type_specifier : declaration_qualifiers type-specifier
                            | type-specifier declaration_qualifiers
                            | type-specifier
        """
        # type specifier -> int, double, long, etc.
        # declaration_qualifiers -> signed, unsigned, etc. as list
        if len(p) == 3:
            if isinstance(p[1], WeaveDataTypes):
                ty = p[1]
                quals = p[2]
            else:
                ty = p[2]
                quals = p[1]
        else:
            # No qualifiers, just declarations
            quals = [WeaveTypeQualifier.Signed]
            ty = p[1]

        p[0] = (ty, quals)

    def p_assembly_statement(self, p):
        """
        assembly-statement : assembly SEMICOLON
        """
        p[0] = p[1]

    def p_assembly_start(self, p):
        """
        assembly-start : ASSEMBLY
        """
        self.isAssemblyRegion = True
        p[0] = p[1]

    def p_assembly(self, p):
        """
        assembly : assembly-scope
        """
        self.__createScopeHeader(p)

    def p_assembly_scope(self, p):
        """
        assembly-scope : assembly-start LCBRACKET asm-body RCBRACKET
                       | assembly-start NATIVE LCBRACKET asm-body RCBRACKET
                       | assembly-start LCBRACKET asm-body RCBRACKET COLON asm-operands
                       | assembly-start NATIVE LCBRACKET asm-body RCBRACKET COLON asm-operands
        """
        body = []
        nativeInline = False
        if len(p) == 5:
            body = p[3]
        elif len(p) == 6:
            body = p[4]
            nativeInline = True
        elif len(p) == 7:
            body = p[3]
        elif len(p) == 8:
            body = p[4]
            nativeInline = True

        node = WeaveAssembly(
            body=body, loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr)
        )
        node.setNativeInline(nativeInline)
        p[0] = self.astTree.create_node(node)
        if len(p) == 7 or len(p) == 8:
            ops = p[6] if len(p) == 7 else p[7]
            for opNum, op in enumerate(ops):
                if not op.data.getSymbolName():
                    op.data.setSymbolName(str(opNum))
                self.astTree.set_parent(op, p[0])
                node.addOperand(op)

        self.isAssemblyRegion = False

    def p_assembly_operands(self, p):
        """
        asm-operands : asm-operands COMMA asm-operand
                     | asm-operand
        """
        if len(p) == 4:
            p[0] = p[1] + p[3]
        else:
            if not isinstance(p[1], list):
                p[0] = [p[1]]
            else:
                p[0] = p[1]

    def p_assembly_operand(self, p):
        """
        asm-operand : LSBRACKET ID RSBRACKET strings LPAREN expression RPAREN
                    | strings LPAREN expression RPAREN
        """
        sym = None
        constr = None
        udwvar = None
        if len(p) == 8:
            sym = f"[{p[2]}]"
            constr = p[4]
            udwvar = p[6]
        elif len(p) == 5:
            constr = p[1]
            udwvar = p[3]

        if len(constr) != 1:
            errorMsg(
                f"Only one constraint is allowed per operand",
                FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
            )
        constr = constr[0]
        node = WeaveAssemblyOperand(
            sym, constr, udwvar, FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr)
        )

        p[0] = [self.astTree.create_node(node)]

        self.astTree.set_parent(node=udwvar, destination=p[0][0])

    def p_assembly_body(self, p):
        """
        asm-body : strings
        """
        p[0] = p[1]

    #############################
    ##### TEMPLATE SUPPORT ######
    #############################

    def p_template_header(self, p):
        """
        template : TEMPLATE LESSTHAN template-params GREATERTHAN thread
        """
        params = p[3]
        scope = p[5].data
        thread = scope.body[0]
        thread.data.setIsTemplate(True)
        thread.data.setTemplateParams(params)
        p[0] = p[5]

    def p_template_params(self, p):
        """
        template-params : template-params COMMA template-param
                        | template-param
        """
        if len(p) == 4:
            p[0] = p[1] + [p[3]]
        else:
            if not isinstance(p[1], list):
                p[0] = [p[1]]
            else:
                p[0] = p[1]

    def p_template_param(self, p):
        """
        template-param : TYPENAME ID
                       | EVENTNAME ID
        """
        if p[1] == "typename":
            p[0] = ("typename", p[2])
        else:
            p[0] = ("eventname", p[2])

    def p_template_instance_params(self, p):
        """
        template-instance-params : template-instance-params COMMA factor-identifier
                                 | factor-identifier
        """
        if len(p) == 4:
            p[0] = p[1] + [p[3].data]
        else:
            if not isinstance(p[1], list):
                p[0] = [p[1].data]
            else:
                p[0] = p[1]

    #############################
    ##### THREADS SUPPORT #######
    #############################

    def p_thread_name(self, p):
        """
        thread-name : ID LESSTHAN template-instance-params GREATERTHAN
                    | ID
        """
        if len(p) == 2:
            p[0] = (p[1], None)
        else:
            ## Template instance is a tuple (template_name, params)
            template_name = p[1]
            params = p[3]
            p[0] = (template_name, params)

    def p_thread_header(self, p):
        """
        thread-header : THREAD
                      | THREAD thread-name
                      | THREAD COLON inherit-thread-names
                      | THREAD thread-name COLON inherit-thread-names
        """
        # Create a tuple (thread_name, template_names, inherited_threads)
        if len(p) == 2:
            p[0] = (None, None, [])
        elif len(p) == 3:
            p[0] = p[2] + ([],)
        elif len(p) == 4:
            p[0] = (None, None, p[3])
        else:
            p[0] = p[2] + (p[4],)

    def p_threads_inherited(self, p):
        """
        inherit-thread-names : inherit-thread-names COMMA thread-name
                             | thread-name

        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_thread(self, p):
        """
        thread : thread-header LCBRACKET thread_body RCBRACKET
               | thread-header LCBRACKET RCBRACKET
               | thread-header SEMICOLON
        """
        body_sections = []
        thread_name = p[1][0]
        template_params = p[1][1]
        inherited_threads = p[1][2]

        if len(p) == 3:
            # Semicolon means that we are using a template and instantiating it here
            # We directly create a WeaveThread node that is empty, and add the template as a child
            # as well as all the other inherited threads
            if p[1][0] is None:
                errorMsg(
                    f"Templates cannot be anonymous threads. They must have a name",
                    FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
                )
            if p[1][1] is None:
                errorMsg(
                    f"Template instantiation must have template parameters",
                    FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
                )

            thread_name = self.thread_name_scrambler(thread_name, template_params)

            inherited_threads = [p[1]] + inherited_threads

        if len(p) == 5:
            body_sections = p[3]

        # These declarations are thread local
        for d in body_sections:
            if isinstance(d.data, WeaveDeclarationStatement):
                d.data.setDeclType(WeaveDeclTypes.Thread)

        thread = WeaveThread(
            name=thread_name if thread_name is not None else "",
            thread_sections=body_sections,
            inherit_list=inherited_threads,
            loc=FileLocation(p.lineno(2), p.lexpos(2), self._fileMgr),
        )

        if template_params is not None and len(p) != 3:
            thread.setIsTemplate(True)
            thread.setTemplateParams(template_params)

        thread.setIsAnonymous(thread_name is None)
        threadNode = self.astTree.create_node(thread)

        for decl in body_sections:
            self.astTree.set_parent(node=decl, destination=threadNode)

        scope = WeaveScope(
            body=[threadNode],
            parent=self.astTree.currentScope,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )
        p[0] = self.astTree.create_node(scope)
        self.astTree.set_parent(node=threadNode, destination=p[0])
        self.astTree.currentScope = scope

    def p_thread_body(self, p):
        """
        thread_body : thread_body_sections
        """
        p[0] = p[1]

    def p_thread_body_section(self, p):
        """
        thread_body_section : declaration-statements
                            | events
                            | extern-declarations
                            | comments
                            | assembly-statement
                            | preproc-comment
        """
        p[0] = p[1]

    def p_declaration(self, p):
        """
        declaration : qual_type_specifier init_declarator_list
        """

        ty = p[1][0]
        quals = p[1][1]
        decls = p[2]
        res = []

        if WeaveTypeQualifier.Constant in quals and not isinstance(decls[0][2].data, WeaveAssignStatement):
            errorMsg(
                f"Constant declaration must be initialized",
                FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
            )

        # determine the type from the first declaration
        if decls[0][1][1] == "pointer":
            quals.append(WeaveTypeQualifier.Pointer)
        elif decls[0][1][1] == "local-pointer":
            quals.append(WeaveTypeQualifier.LocalPointer)

        for decl in decls:
            # decl has the structure
            # ("init_declarator", (var_name, "pointer"/"local-pointer"/None), Init_Expression)

            # A decl name should not be named as a reserved keyword
            self.checkIsType(
                decl[1][0],
                throw=True,
                loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
            )
            # Create identifier
            astTreeNode = self.astTree.create_node(
                WeaveIdentifier(
                    dataType=ty,
                    quals=quals.copy(),
                    name=decl[1][0],
                    loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
                )
            )

            if isinstance(decl[2].data, WeaveAssignStatement):
                decl[2].data.setDestination(astTreeNode)

            res.append(
                self.astTree.create_node(
                    WeaveDeclarationStatement(
                        dataType=ty,
                        identifier=astTreeNode,
                        default_val=decl[2],
                        loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
                    )
                )
            )
            self.astTree.set_parent(astTreeNode, res[-1])
            self.astTree.set_parent(decl[2], res[-1])
        p[0] = res

    def p_declaration_statement(self, p):
        """
        declaration-statement : declaration SEMICOLON
        """
        p[0] = p[1]

    def p_external_declaration(self, p):
        """
        extern-declaration : EXTERN event-declaration SEMICOLON
                           | EXTERN declaration-statement
        """
        if len(p) == 4:
            # This is of type event declaration
            p[2].data.setIsExternal(True)
        else:
            # This is of type variable declaration
            for decl in p[2]:
                decl.data.setDeclType(WeaveDeclTypes.Extern)

        self.__createScopeHeader(p, 2)

    def p_struct_definition(self, p):
        """
        struct-definition : STRUCT ID LCBRACKET struct_body RCBRACKET
        """
        node = WeaveStruct(
            name=p[2],
            fields=p[4],
            loc=FileLocation(p.lineno(2), p.lexpos(2), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

        for decl in p[4]:
            decl.data.setDeclType(WeaveDeclTypes.Struct)
            self.astTree.set_parent(node=decl, destination=p[0])

    def p_struct_body(self, p):
        """
        struct_body : declaration-statements
        """
        # A struct declarator must not be initialized
        for decl in p[1]:
            default = decl.data.get_default()
            if not isinstance(default.data, WeaveEmpty):
                errorMsg(
                    f"Initialization of struct members is not allowed",
                    FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
                )

        p[0] = p[1]

    def p_struct_element_access(self, p):
        """
        struct-element-access : expression ELEMENT_ACCESS ID
        """
        lhs = p[1]
        astTreeNode = p[3]
        # A decl name should not be named as a reserved keyword
        self.checkIsType(
            astTreeNode,
            throw=True,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )
        astTreeNode = self.astTree.create_node(
            WeaveIdentifier(
                dataType=WeaveDataTypes(WeaveDataTypesPrimitives.String),
                quals=[],
                name=astTreeNode,
                loc=FileLocation(p.lineno(3), p.lexpos(3), self._fileMgr),
            )
        )

        node = WeaveBinaryOperator(
            opType=WeaveBinaryOps.STRUCT_ELEMENT_ACCESS,
            left=lhs,
            right=astTreeNode,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )
        p[0] = self.astTree.create_node(node)
        self.astTree.set_parent(node=lhs, destination=p[0])
        self.astTree.set_parent(node=astTreeNode, destination=p[0])

    ###################
    # UNION DEFINITION
    ###################
    def p_union_definition(self, p):
        """
        struct-definition : UNION ID LCBRACKET struct_body RCBRACKET
        """
        node = WeaveUnion(
            name=p[2],
            fields=p[4],
            loc=FileLocation(p.lineno(2), p.lexpos(2), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

        for decl in p[4]:
            decl.data.setDeclType(WeaveDeclTypes.Union)
            self.astTree.set_parent(node=decl, destination=p[0])

    def p_union_element_access(self, p):
        """
        union-element-access : expression ELEMENT_ACCESS ID
        """
        lhs = p[1]
        astTreeNode = p[3]
        # A decl name should not be named as a reserved keyword
        self.checkIsType(
            astTreeNode,
            throw=True,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )
        astTreeNode = self.astTree.create_node(
            WeaveIdentifier(
                dataType=WeaveDataTypes(WeaveDataTypesPrimitives.String),
                quals=[],
                name=astTreeNode,
                loc=FileLocation(p.lineno(3), p.lexpos(3), self._fileMgr),
            )
        )

        node = WeaveBinaryOperator(
            opType=WeaveBinaryOps.STRUCT_ELEMENT_ACCESS,
            left=lhs,
            right=astTreeNode,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )
        p[0] = self.astTree.create_node(node)
        self.astTree.set_parent(node=lhs, destination=p[0])
        self.astTree.set_parent(node=astTreeNode, destination=p[0])

    def p_type_specifier(self, p):
        """
        type-specifier : primitive-data-type
                        | ID
        """
        if isinstance(p[1], str):
            p[0] = WeaveDataTypes(WeaveDataTypesPrimitives.UserDefined, p[1])
        else:
            p[0] = p[1]

    def p_primitive_dataTypes(self, p):
        """
        primitive-data-type : CHAR
                            | SHORT
                            | INT
                            | LONG
                            | BF16
                            | FLOAT
                            | DOUBLE
        """
        dict_types = {
            "char": WeaveDataTypesPrimitives.Char,
            "short": WeaveDataTypesPrimitives.Short,
            "int": WeaveDataTypesPrimitives.Integer,
            "long": WeaveDataTypesPrimitives.Long,
            "bf16": WeaveDataTypesPrimitives.BF16,
            "float": WeaveDataTypesPrimitives.Float,
            "double": WeaveDataTypesPrimitives.Double,
        }

        p[0] = WeaveDataTypes(dict_types[p[1]])

    def p_declaration_qualifier(self, p):
        """
        declaration_qualifier : UNSIGNED
                            | CONST
                            | STATIC
                            | PRIVATE
                            | CONSTEXP
        """
        if p[1] == "unsigned":
            p[0] = WeaveTypeQualifier.Unsigned
        elif p[1] == "const":
            p[0] = WeaveTypeQualifier.Constant
        elif p[1] == "static":
            p[0] = WeaveTypeQualifier.Static
        elif p[1] == "private":
            p[0] = WeaveTypeQualifier.Private
        elif p[1] == "constexp":
            p[0] = WeaveTypeQualifier.GlobalConstant

    def p_init_declarator_list(self, p):
        """
        init_declarator_list : init_declarator_list COMMA init_declarator
                            | init_declarator
        """
        if len(p) == 4:
            if not isinstance(p[3], list):
                p[0] = p[1] + [p[3]]
            else:
                p[0] = p[1] + p[3]
        else:
            if not isinstance(p[1], list):
                p[0] = [p[1]]
            else:
                p[0] = p[1]

    def p_init_declarator(self, p):
        """
        init_declarator : declarator ASSIGN expression
                        | declarator
        """
        if len(p) == 4:
            node = WeaveAssignStatement(
                dest=p[1][0],
                val=p[3],
                loc=FileLocation(p.lineno(2), p.lexpos(2), self._fileMgr),
            )
            p[0] = ("init_declarator", p[1], self.astTree.create_node(node))
            self.astTree.set_parent(node=p[3], destination=p[0][2])
        else:
            p[0] = ("init_declarator", p[1], self.astTree.create_node(WeaveEmpty()))

    def p_declarator(self, p):
        """
        declarator : ID
                    | TIMES LOCAL ID %prec DEREFERENCE
                    | TIMES ID %prec DEREFERENCE
        """
        if len(p) == 2:
            p[0] = (p[1], None)
        elif len(p) == 3:
            p[0] = (p[2], "pointer")
        elif len(p) == 4:
            p[0] = (p[3], "local-pointer")

    def p_assign(self, p):
        """
        assign-expression : expression ASSIGN expression
                           | struct-element-access ASSIGN expression
        """
        dest = p[1]
        val = p[3]

        node = WeaveAssignStatement(
            dest=dest,
            val=val,
            loc=FileLocation(
                p.lineno(2),
                p.lexpos(2),
                self._fileMgr,
            ),
        )
        p[0] = self.astTree.create_node(node)
        # Set parent of expression
        self.astTree.set_parent(node=dest, destination=p[0])
        self.astTree.set_parent(node=val, destination=p[0])

    def p_comment(self, p):
        """
        comment_line : COMMENT
        """
        node = WeaveComment(p[1], FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr))
        p[0] = self.astTree.create_node(node)

    def p_assign_statement(self, p):
        """
        assign-statement : assign-expression SEMICOLON
        """
        p[0] = p[1]

    def p_for(self, p):
        """
        for-statement : for-scope
        """
        # the scope consists of the for-range and the loop body
        self.__createScopeHeader(p)

    def p_for_scope(self, p):
        """
        for-scope : FOR for-range scope
        """
        body = p[3]
        init = p[2][1]
        end = p[2][2]
        incr = p[2][3]

        if not isinstance(init, list):
            init = [init]

        if isinstance(body, list) and len(body) == 0:
            errorMsg(
                f"For loop must have a body",
                FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
            )

        node = WeaveForStatement(
            init=init,
            termCond=end,
            increment=incr,
            body=[body],
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

        for decl in init:
            self.astTree.set_parent(decl, p[0])

        self.astTree.set_parent(end, p[0])
        self.astTree.set_parent(incr, p[0])
        self.astTree.set_parent(body, p[0])

    def p_for_range(self, p):
        """
        for-range : LPAREN declaration SEMICOLON scopedExpression SEMICOLON assign-expression RPAREN
                  | LPAREN assign-expression SEMICOLON scopedExpression SEMICOLON assign-expression RPAREN

        """
        p[0] = ("for-range", p[2], p[4], p[6])

    def p_while(self, p):
        """
        while-statement : WHILE LPAREN scopedExpression RPAREN scope
        """
        cond = p[3]
        body = [p[5]]

        node = WeaveWhileStatement(
            condition=cond,
            body=body,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

        self.astTree.set_parent(cond, p[0])

        if isinstance(body, list) and isinstance(body[0], list) and len(body[0]) == 0:
            errorMsg(
                f"While loop must have a body",
                FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
            )
        for stmt in body:
            self.astTree.set_parent(stmt, p[0])

    def p_if_elif(self, p):
        """
        if-statement : IF LPAREN scopedExpression RPAREN scope else-statement
                     | IF LPAREN scopedExpression RPAREN scope elif-statement
                     | IF LPAREN scopedExpression RPAREN scope
        elif-statement : ELSEIF LPAREN scopedExpression RPAREN scope elif-statement
                       | ELSEIF LPAREN scopedExpression RPAREN scope else-statement
                       | ELSEIF LPAREN scopedExpression RPAREN scope
        """

        exp = p[3]
        fbody = []

        if isinstance(p[5], list):
            tbody = p[5]
        else:
            tbody = [p[5]]

        # an `if` condition with an `else` or `elif` branch
        if len(p) == 7:
            if isinstance(p[6], list):
                fbody = p[6]
            else:
                # Whenever the fbody is an elif
                # We need to make it a list
                fbody = [p[6]]

        node = WeaveIfStatement(
            condition=exp,
            trueE=tbody,
            falseE=fbody,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

        self.astTree.set_parent(exp, p[0])

        for stmt in tbody:
            self.astTree.set_parent(stmt, p[0])

        for stmt in fbody:
            self.astTree.set_parent(stmt, p[0])

    def p_else(self, p):
        """
        else-statement : ELSE scope
        """
        if len(p) == 3:
            p[0] = p[2]
        else:
            p[0] = []

    def p_scopedExpression(self, p):
        """
        scopedExpression : expression
        """
        expression = p[1]
        scope = WeaveScope(
            body=[expression],
            parent=self.astTree.currentScope,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )
        p[0] = self.astTree.create_node(scope)
        self.astTree.set_parent(expression, p[0])
        if isinstance(expression.data, WeaveDeclarationStatement):
            expression.data.setDeclType(WeaveDeclTypes.Scope)
        self.astTree.currentScope = scope

    def p_expression(self, p):
        """
        expression : expression-unary
                    | expression-arith
                    | expression-array
                    | expression-call
                    | struct-element-access
                    | factor
                    | LPAREN expression RPAREN
        """
        if len(p) == 4:
            p[0] = p[2]
        else:
            p[0] = p[1]

    def p_expression_call(self, p):
        """
        expression-call : ID LPAREN call-arguments RPAREN
                        | ID LPAREN RPAREN"""

        args = []
        if len(p) == 5:
            args = p[3]
        node = WeaveCall(
            name=p[1],
            args=args,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )
        p[0] = self.astTree.create_node(node)

        for param in args:
            self.astTree.set_parent(param, p[0])

    def p_call_args(self, p):
        """
        call-arguments : call-arguments COMMA expression
                       | expression
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_expression_array(self, p):
        """
        expression-array : ID LSBRACKET expression RSBRACKET
        """
        # Array expression from a keyword is invalid
        self.checkIsType(
            p[1],
            throw=True,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )
        node_id = WeaveIdentifier(
            dataType=WeaveDataTypes(WeaveDataTypesPrimitives.Undefined),
            quals=[WeaveTypeQualifier.LocalPointer],
            name=p[1],
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )

        astTreeNode = self.astTree.create_node(node_id)
        node = WeaveBinaryOperator(
            opType=WeaveBinaryOps.MEMORY_DERREF,
            left=astTreeNode,
            right=p[3],
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

        self.astTree.set_parent(astTreeNode, p[0])
        self.astTree.set_parent(p[3], p[0])

    def p_expression_arith(self, p):
        """
        expression-arith : expression PLUS expression
                        | expression MINUS expression
                        | expression TIMES expression %prec TIMES
                        | expression DIVIDE expression
                        | expression MODULO expression
                        | expression SHFTLFT expression
                        | expression SHFTRGT expression
                        | expression LESSTHAN expression
                        | expression LESSEQTO expression
                        | expression GREATERTHAN expression
                        | expression GREATEREQTO expression
                        | expression AND expression
                        | expression OR expression
                        | expression BWOR expression
                        | expression BWAND expression
                        | expression BWXOR expression
                        | expression EQUAL expression
                        | expression DIFFERENT expression
        """

        ops_dict = {
            "+": WeaveBinaryOps.PLUS,
            "-": WeaveBinaryOps.MINUS,
            "*": WeaveBinaryOps.TIMES,
            "/": WeaveBinaryOps.DIVIDE,
            "%": WeaveBinaryOps.MODULO,
            "<<": WeaveBinaryOps.SHFTLFT,
            ">>": WeaveBinaryOps.SHFTRGT,
            "<": WeaveBinaryOps.LESSTHAN,
            "<=": WeaveBinaryOps.LESSEQTO,
            ">": WeaveBinaryOps.GREATERTHAN,
            ">=": WeaveBinaryOps.GREATEREQTO,
            "&&": WeaveBinaryOps.AND,
            "||": WeaveBinaryOps.OR,
            "|": WeaveBinaryOps.BWOR,
            "&": WeaveBinaryOps.BWAND,
            "^": WeaveBinaryOps.BWXOR,
            "==": WeaveBinaryOps.EQUAL,
            "!=": WeaveBinaryOps.DIFFERENT,
        }

        # TODO: Add constant expression elimination. If both
        # sides of the equation are numbers, we resolve the
        # equation and return an immediate node instead

        node = WeaveBinaryOperator(
            opType=ops_dict[p[2]],
            left=p[1],
            right=p[3],
            loc=FileLocation(p.lineno(2), p.lexpos(2), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

        self.astTree.set_parent(p[1], p[0])
        self.astTree.set_parent(p[3], p[0])

    def p_unary_expression(self, p):
        """
        expression-unary : NOT expression
                        | BWNOT expression
                        | MINUS expression
                        | TIMES expression %prec DEREFERENCE
        """

        ops_dict = {
            "!": WeaveUnaryOps.NOT,
            "~": WeaveUnaryOps.BWNOT,
            "-": WeaveUnaryOps.NEGATE,
            "*": WeaveUnaryOps.DERREF,
        }

        node = WeaveUnaryOperator(
            opType=ops_dict[p[1]],
            operand=p[2],
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

        self.astTree.set_parent(p[2], p[0])

    def p_factor(self, p):
        """
        factor : factor-int
                | factor-float
                | factor-identifier
                | factor-string
        """
        if len(p) == 4:
            p[0] = p[2]
        else:
            p[0] = p[1]

    def p_factor_int(self, p):
        """
        factor-int : INT_NUMBER
        """
        node = WeaveLiteral(
            dataType=WeaveDataTypes(WeaveDataTypesPrimitives.Integer),
            value=p[1],
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

    def p_factor_string(self, p):
        """
        factor-string : strings
        """
        node = WeaveLiteral(
            dataType=WeaveDataTypes(WeaveDataTypesPrimitives.String),
            value=p[1],
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

    def p_factor_float(self, p):
        """
        factor-float : FLOAT_NUMBER
        """
        node = WeaveLiteral(
            dataType=WeaveDataTypes(WeaveDataTypesPrimitives.Float),
            value=p[1],
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )

        p[0] = self.astTree.create_node(node)

    def p_factor_id(self, p):
        """
        factor-identifier : ID NAMESPACE factor-identifier
                          | ID
                          | primitive-data-type
        """
        if len(p) > 2:
            p[3].data.nameSpace = (
                (p[1] + "::" + p[3].data.nameSpace)
                if p[3].data.nameSpace != ""
                else p[1]
            )
            p[0] = p[3]
        else:
            node = WeaveIdentifier(
                dataType=WeaveDataTypes(WeaveDataTypesPrimitives.Undefined),
                quals=[],
                name=p[1],
                loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
            )

            if self.checkIsType(p[1]):
                node.setIsReserved(True)

            p[0] = self.astTree.create_node(node)

    def p_strings_concat(self, p):
        """
        strings : strings STRING
                | STRING
        """
        if len(p) == 3:
            p[0] = (p[1] + p[2]) if not self.isAssemblyRegion else p[1] + [p[2]]
        else:
            p[0] = p[1] if not self.isAssemblyRegion else [p[1]]

    def p_plurals(self, p):
        """
        statements : statements statement
                   | statement
        program_sections : program_sections program_section
                           | program_section
        thread_body_sections : thread_body_sections thread_body_section
                           | thread_body_section
        declaration-statements : declaration-statements declaration-statement
                               | declaration-statement
        struct-definitions : struct-definitions struct-definition
                            | struct-definition
        extern-declarations : extern-declarations extern-declaration
                            | extern-declaration
        templates : templates template
                    | template
        threads : threads thread
                | thread
        events : events event
                | event
        declaration_qualifiers : declaration_qualifiers declaration_qualifier
                               | declaration_qualifier
        comments : comments comment_line
                 | comment_line
        """
        if len(p) == 3:
            if not isinstance(p[2], list):
                p[0] = p[1] + [p[2]]
            else:
                p[0] = p[1] + p[2]
        else:
            if not isinstance(p[1], list):
                p[0] = [p[1]]
            else:
                p[0] = p[1]

    def p_scope(self, p):
        """
        scope : LCBRACKET statements RCBRACKET
                | LCBRACKET RCBRACKET
        """

        if len(p) == 4:
            statements = p[2]
            if not isinstance(statements, list):
                statements = [statements]

            scope = WeaveScope(
                body=statements,
                parent=self.astTree.currentScope,
                loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
            )
            p[0] = self.astTree.create_node(scope)

            for s in statements:
                self.astTree.set_parent(s, p[0])
                if isinstance(s.data, WeaveDeclarationStatement):
                    s.data.setDeclType(WeaveDeclTypes.Scope)
            self.astTree.currentScope = scope
        else:
            p[0] = []

    def p_preproc_comment(self, p):
        """
        preproc-comment : PREPROCESSOR
        """
        # Example of a preprocessor line:
        # 1 "UDKVMSR.udwh" 1
        # The format is
        # line_number "file_name" flag
        # flag = 1 indicates the start of a new file
        # flag = 2 indicates returning to a file after a #include
        # flag = 3 indicates the following text comes from a system header file
        # flag = 4 indicates that the following text should be treated as being wrapped in an implicit extern "C" block
        preproc_vals = p[1].split(" ")
        debugMsg(10, f"Preprocessor line: {preproc_vals}")
        if len(preproc_vals) > 3:
            file_name = preproc_vals[2].replace('"', "")
            # Check if file exists
            if os.path.isfile(file_name):
                # Check if flag is 1 then create a new file manager
                if preproc_vals[3] == "1":
                    debugMsg(4, f"Creating new file manager for {file_name}")
                    self._fileMgrs[file_name] = FileManager(
                        file_name, self._fileMgr.getFileContent()
                    )
                    self._fileMgr = self._fileMgrs[file_name]
                elif preproc_vals[3] == "2":
                    debugMsg(4, f"Returning to file {file_name}")
                    self._fileMgr = self._fileMgrs[file_name]
            else:
                debugMsg(4, f"{file_name} is not a file, ignoring preprocessor line")
        # Return empty node
        p[0] = self.astTree.create_node(WeaveEmpty())

    def p_break(self, p):
        """
        break-statement : BREAK SEMICOLON
        """
        node = WeaveBreakStatement(
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr)
        )
        p[0] = self.astTree.create_node(node)

    def p_continue(self, p):
        """
        continue-statement : CONTINUE SEMICOLON
        """
        node = WeaveContinueStatement(
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr)
        )
        p[0] = self.astTree.create_node(node)

    def p_error(self, p):
        if p:
            loc = FileLocation(p.lineno, p.lexpos, self._fileMgr)
        else:
            loc = FileLocation(1, 0, self._fileMgr)
        errorMsg(f"Syntax error in input! {loc}, Token: {p}")

    def __init__(self, lexerIn):
        self.isAssemblyRegion = False
        self.lexer = lexerIn
        self.astTree = WeaveAST()
        self._fileMgr = None

    ########################################################
    ################# HELPER FUNCTIONS #####################
    ########################################################

    def thread_name_scrambler(self, name: str, params: list):
        return (
                name
                + "_"
                + "_".join(
            [
                (
                    p.get_name().value
                    if isinstance(p.get_name(), WeaveDataTypes)
                    else p.get_name()
                )
                for p in params
            ]
        )
        )

    def checkIsType(self, p, throw: bool = False, loc: FileLocation = None) -> bool:
        if isinstance(p, WeaveDataTypes):
            if throw:
                errorMsg(
                    f"Using a restricted data type name in an unexpected context", loc
                )
            return True
        else:
            return False

    def getTree(self):
        return self.astTree

    def __createScopeHeader(self, p, index=1):
        scope = WeaveScope(
            body=[p[index]],
            parent=self.astTree.currentScope,
            loc=FileLocation(p.lineno(1), p.lexpos(1), self._fileMgr),
        )
        p[0] = self.astTree.create_node(scope)
        self.astTree.set_parent(node=p[index], destination=p[0])
        self.astTree.currentScope = scope

    # Build the parser
    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    def parse(self, inStr: str, **kwargs):
        fileName = ""
        fileContent = ""
        if kwargs.get("fileName"):
            fullPath = kwargs.get("fileName")
            fileName = fullPath
            name = os.path.basename(fullPath)
            self.astTree.setProgramName("_".join(name.split(".")[:-1]))
            kwargs.pop("fileName")
        if kwargs.get("fileContent"):
            fileContent = kwargs.get("fileContent")
            kwargs.pop("fileContent")

        fcont = FileContent(fileContent)

        self._fileMgrs = {}
        self._fileMgrs[fileName] = FileManager(fileName, fcont)
        self._fileMgr = self._fileMgrs[fileName]

        return self.parser.parse(inStr, tracking=True, lexer=self.lexer, **kwargs)
