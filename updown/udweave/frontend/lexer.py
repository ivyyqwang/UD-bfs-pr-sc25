import ply.lex as lex
import sys

class WeaveLexer(object):
    reserved = {
        "if": "IF",
        "else": "ELSE",
        "elif": "ELSEIF",
        "while": "WHILE",
        "for": "FOR",
        "char": "CHAR",
        "short": "SHORT",
        "int": "INT",
        "long": "LONG",
        "bf16": "BF16",
        "float": "FLOAT",
        "double": "DOUBLE",
        "unsigned": "UNSIGNED",
        "const": "CONST",
        "constexp": "CONSTEXP",
        "local": "LOCAL",
        "thread": "THREAD",
        "event": "EVENT",
        "asm": "ASSEMBLY",
        "native": "NATIVE",
        "struct": "STRUCT",
        "union": "UNION",
        "extern": "EXTERN",
        "static": "STATIC",
        "private": "PRIVATE",
        "template": "TEMPLATE",
        "typename": "TYPENAME",
        "eventname": "EVENTNAME",
        "break": "BREAK",
        "continue": "CONTINUE",
    }

    # The precedence is a list that is sorted from the lowest precedence to the highest one.
    precedence = (
        ("left", "OR"),
        ("left", "AND"),
        ("left", "BWOR"),
        ("left", "BWXOR"),
        ("left", "BWAND"),
        ("nonassoc", "EQUAL", "DIFFERENT"),
        ("nonassoc", "LESSTHAN", "LESSEQTO", "GREATERTHAN", "GREATEREQTO"),
        ("left", "SHFTLFT", "SHFTRGT"),
        ("left", "PLUS", "MINUS"),
        ("left", "TIMES", "DIVIDE", "MODULO"),
        # ('right', '++', '--'),
        ("right", "NOT"),
        ("right", "BWNOT"),
        # ('nonassoc', '?'),
        # ('right', ':')

        # This is different from C: https://en.cppreference.com/w/c/language/operator_precedence
        # Here we prioritize the dereference over the element access. This is the purpose of the
        # structs in our language: They are there to ease the memory operations and not designed
        # to be used as a "data container" like in C. Hence, if a field is accessed, it is expected
        # that the struct is a pointer to a memory location and the field is accessed through the
        # pointer. For C compatibility swap the two lines below.
        ("right", "ELEMENT_ACCESS"),
        ("left", "DEREFERENCE"),
    )

    # Tokenize the input
    tokens = [
        "INT_NUMBER",
        "FLOAT_NUMBER",
        "STRING",
        "ID",
        "LPAREN",
        "RPAREN",
        "LCBRACKET",
        "RCBRACKET",
        "LSBRACKET",
        "RSBRACKET",
        "PLUS",
        "MINUS",
        "TIMES",
        "DIVIDE",
        "MODULO",
        "SHFTLFT",
        "SHFTRGT",
        "LESSTHAN",
        "LESSEQTO",
        "GREATERTHAN",
        "GREATEREQTO",
        "AND",
        "OR",
        "NOT",
        "BWOR",
        "BWAND",
        "BWXOR",
        "BWNOT",
        "EQUAL",
        "DIFFERENT",
        "ASSIGN",
        "SEMICOLON",
        "COLON",
        "NAMESPACE",
        "COMMA",
        "COMMENT",
        "ELEMENT_ACCESS",
        "DEREFERENCE",
        "PREPROCESSOR",
    ] + list(set(reserved.values()))

    # Regular expression rules for simple tokens
    t_LPAREN = r"\("
    t_RPAREN = r"\)"
    t_LCBRACKET = r"{"
    t_RCBRACKET = r"}"
    t_LSBRACKET = r"\["
    t_RSBRACKET = r"\]"

    t_PLUS = r"\+"
    t_MINUS = r"-"
    t_TIMES = r"\*"
    t_DIVIDE = r"/"
    t_MODULO = r"%"

    t_SHFTLFT = r"<<"
    t_SHFTRGT = r">>"
    t_LESSTHAN = r"<"
    t_LESSEQTO = r"<="
    t_GREATERTHAN = r">"
    t_GREATEREQTO = r">="
    t_AND = r"\&\&"
    t_OR = r"\|\|"
    t_NOT = r"!"
    t_BWAND = r"\&"
    t_BWOR = r"\|"
    t_BWXOR = r"\^"
    t_BWNOT = r"~"
    t_EQUAL = r"=="
    t_DIFFERENT = r"!="

    t_ASSIGN = r"="
    t_SEMICOLON = r";"
    t_NAMESPACE = r"::"
    t_COLON = r":"
    t_COMMA = r","
    t_ELEMENT_ACCESS = r"\."

    def t_COMMENT(self, t):
        r"//.*"
        return t

    def t_ignore_IGNOREDCOMMENT(self, t):
        r"\/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+\/"
        t.lexer.lineno += t.value.count("\n")
        pass

    def t_PREPROCESSOR(self, t):
        r"\#.*"
        vals = t.value.split()
        try:
            newLine = int(vals[1])
            t.lexer.lineno = newLine - 1
        except:
            pass
        return t

    def t_FLOAT_NUMBER(self, t):
        r"-?\d+\.\d+"
        t.value = float(t.value)
        return t

    def t_INT_NUMBER(self, t):
        r"(0b[01_]+|0x[0-9a-fA-F_]+|\d+(_\d+)*)"
        try:
            if t.value.startswith("0b"):
                t.value = int(t.value[2:], 2)
            elif t.value.startswith("0x"):
                t.value = int(t.value[2:], 16)
            else:
                t.value = int(t.value)
        except ValueError:
            print(f"Incorrect integer format: {t.value}")
            sys.exit(0)
        return t

    def t_STRING(self, t):
        r'"(?:[^"\\]|\\.)*"'
        t.value = t.value[1:-1]  # remove the surrounding double quotes
        return t

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)

    # Define a rule to recognize variables
    def t_ID(self, t):
        r"[a-zA-Z_][a-zA-Z_0-9]*"
        t.type = self.reserved.get(t.value, "ID")
        return t

    # A string containing ignored characters (spaces and tabs)
    t_ignore = " \t"

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Test its output
    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)
