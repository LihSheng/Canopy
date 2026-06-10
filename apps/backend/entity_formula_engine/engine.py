"""Formula engine for deterministic computed property evaluation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from common.errors import ValidationError


class FormulaEngine:
    """Deterministic evaluator for same-entity computed property formulas.

    Supported functions:
      upper, lower, trim, add, subtract, multiply, divide,
      coalesce, is_null, if, concat, length, equals, greater_than, less_than
    """

    def evaluate(self, formula: str, row_data: dict) -> object:
        """Evaluate a formula string against a row of data.

        Args:
            formula: The expression to evaluate.
            row_data: Dict of property_key -> value.
        """
        parser = _Parser(formula)
        ast_node = parser.parse()
        return _Evaluator(row_data).eval(ast_node)

    def extract_property_references(self, formula: str) -> set[str]:
        """Parse *formula* and return the set of bare property references."""
        parser = _Parser(formula)
        ast_node = parser.parse()
        return _PropertyExtractor().extract(ast_node)

    def infer_output_type(self, formula: str) -> str | None:
        """Infer the output type of *formula*.

        Returns 'string', 'number', 'boolean', or None when unknown.
        """
        parser = _Parser(formula)
        ast_node = parser.parse()
        return _TypeInferer().infer(ast_node)


# ─── AST nodes ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _LiteralNode:
    value: object


@dataclass(frozen=True)
class _PropertyNode:
    name: str


@dataclass(frozen=True)
class _FunctionNode:
    name: str
    args: list[object]


# ─── Tokenizer ──────────────────────────────────────────────────────────


class _Token:
    def __init__(self, kind: str, value: str):
        self.kind = kind
        self.value = value

    def __repr__(self) -> str:
        return f"_Token({self.kind!r}, {self.value!r})"


_KINDS = {
    "IDENT": "IDENT",
    "LPAREN": "LPAREN",
    "RPAREN": "RPAREN",
    "COMMA": "COMMA",
    "STRING": "STRING",
    "NUMBER": "NUMBER",
    "EOF": "EOF",
}


class _Tokenizer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def next_token(self) -> _Token:
        self._skip_whitespace()
        if self.pos >= self.length:
            return _Token(_KINDS["EOF"], "")

        ch = self.text[self.pos]

        if ch == "(":
            self.pos += 1
            return _Token(_KINDS["LPAREN"], "(")
        if ch == ")":
            self.pos += 1
            return _Token(_KINDS["RPAREN"], ")")
        if ch == ",":
            self.pos += 1
            return _Token(_KINDS["COMMA"], ",")

        if ch in ('"', "'"):
            return self._read_string(ch)

        if ch == "-" or ch.isdigit():
            return self._read_number()

        if ch.isalpha() or ch == "_":
            return self._read_identifier()

        if ch == ".":
            raise ValidationError(
                f"Cross-entity references are not allowed in computed property formulas. "
                f"Found '.' at position {self.pos}."
            )

        raise ValidationError(f"Unexpected character '{ch}' at position {self.pos}.")

    def _skip_whitespace(self) -> None:
        while self.pos < self.length and self.text[self.pos].isspace():
            self.pos += 1

    def _read_string(self, quote: str) -> _Token:
        start = self.pos
        self.pos += 1  # consume opening quote
        while self.pos < self.length and self.text[self.pos] != quote:
            self.pos += 1
        if self.pos >= self.length:
            raise ValidationError(f"Unterminated string starting at position {start}.")
        value = self.text[start + 1 : self.pos]
        self.pos += 1  # consume closing quote
        return _Token(_KINDS["STRING"], value)

    def _read_number(self) -> _Token:
        start = self.pos
        if self.text[self.pos] == "-":
            self.pos += 1
        dot_seen = False
        while self.pos < self.length and (self.text[self.pos].isdigit() or self.text[self.pos] == "."):
            if self.text[self.pos] == ".":
                if dot_seen:
                    break
                dot_seen = True
            self.pos += 1
        return _Token(_KINDS["NUMBER"], self.text[start : self.pos])

    def _read_identifier(self) -> _Token:
        start = self.pos
        while self.pos < self.length and (self.text[self.pos].isalnum() or self.text[self.pos] == "_"):
            self.pos += 1
        return _Token(_KINDS["IDENT"], self.text[start : self.pos])


# ─── Parser ───────────────────────────────────────────────────────────────


class _Parser:
    ALLOWED_FUNCTIONS = {
        "upper",
        "lower",
        "trim",
        "add",
        "subtract",
        "multiply",
        "divide",
        "coalesce",
        "is_null",
        "if",
        "concat",
        "length",
        "equals",
        "greater_than",
        "less_than",
    }

    def __init__(self, text: str):
        self.tokenizer = _Tokenizer(text)
        self.current = self.tokenizer.next_token()

    def parse(self) -> object:
        node = self._parse_expression()
        if self.current.kind != _KINDS["EOF"]:
            raise ValidationError(f"Unexpected token '{self.current.value}' after end of expression.")
        return node

    def _advance(self) -> None:
        self.current = self.tokenizer.next_token()

    def _parse_expression(self) -> object:
        return self._parse_atom()

    def _parse_atom(self) -> object:
        token = self.current
        if token.kind == _KINDS["STRING"]:
            self._advance()
            return _LiteralNode(token.value)
        if token.kind == _KINDS["NUMBER"]:
            self._advance()
            value = _parse_number(token.value)
            return _LiteralNode(value)
        if token.kind == _KINDS["IDENT"]:
            self._advance()
            # Look ahead for function call
            if self.current.kind == _KINDS["LPAREN"]:
                if token.value not in self.ALLOWED_FUNCTIONS:
                    raise ValidationError(f"Unknown function '{token.value}'.")
                return self._parse_function_call(token.value)
            # Literal keywords
            if token.value == "null":
                return _LiteralNode(None)
            if token.value == "true":
                return _LiteralNode(True)
            if token.value == "false":
                return _LiteralNode(False)
            # Property reference
            return _PropertyNode(token.value)
        if token.kind == _KINDS["EOF"]:
            raise ValidationError("Unexpected end of formula.")
        raise ValidationError(f"Unexpected token '{token.value}'.")

    def _parse_function_call(self, name: str) -> _FunctionNode:
        self._advance()  # consume LPAREN
        args: list[object] = []
        if self.current.kind != _KINDS["RPAREN"]:
            args.append(self._parse_expression())
            while self.current.kind == _KINDS["COMMA"]:
                self._advance()
                if self.current.kind == _KINDS["RPAREN"]:
                    raise ValidationError("Trailing comma in function arguments.")
                args.append(self._parse_expression())
        if self.current.kind != _KINDS["RPAREN"]:
            raise ValidationError(f"Expected ')' but found '{self.current.value}'.")
        self._advance()  # consume RPAREN
        return _FunctionNode(name, args)


# ─── Property Extractor ─────────────────────────────────────────────────────


class _PropertyExtractor:
    def extract(self, node: object) -> set[str]:
        if isinstance(node, _LiteralNode):
            return set()
        if isinstance(node, _PropertyNode):
            return {node.name}
        if isinstance(node, _FunctionNode):
            refs = set()
            for arg in node.args:
                refs.update(self.extract(arg))
            return refs
        return set()


# ─── Type Inferer ───────────────────────────────────────────────────────────


class _TypeInferer:
    def infer(self, node: object) -> str | None:
        if isinstance(node, _LiteralNode):
            if isinstance(node.value, bool):
                return "boolean"
            if isinstance(node.value, (int, float)):
                return "number"
            if isinstance(node.value, str):
                return "string"
            return None
        if isinstance(node, _PropertyNode):
            return None
        if isinstance(node, _FunctionNode):
            return self._infer_function(node)
        return None

    def _infer_function(self, node: _FunctionNode) -> str | None:
        if node.name in {"upper", "lower", "trim", "concat"}:
            return "string"
        if node.name in {"add", "subtract", "multiply", "divide", "length"}:
            return "number"
        if node.name in {"equals", "greater_than", "less_than", "is_null"}:
            return "boolean"
        return None


# ─── Evaluator ────────────────────────────────────────────────────────────


class _Evaluator:
    def __init__(self, row_data: dict):
        self._row_data = row_data

    def eval(self, node: object) -> object:
        if isinstance(node, _LiteralNode):
            return node.value
        if isinstance(node, _PropertyNode):
            return self._row_data.get(node.name)
        if isinstance(node, _FunctionNode):
            return self._eval_function(node)
        raise ValidationError(f"Unknown AST node type: {type(node).__name__}")

    def _eval_function(self, node: _FunctionNode) -> object:
        func = _FUNCTIONS.get(node.name)
        if func is None:
            raise ValidationError(f"Unsupported function '{node.name}'.")
        evaluated_args = [self.eval(arg) for arg in node.args]
        return func(*evaluated_args)


# ─── Function implementations ─────────────────────────────────────────────


def _upper(s):
    if s is None:
        return None
    return str(s).upper()


def _lower(s):
    if s is None:
        return None
    return str(s).lower()


def _trim(s):
    if s is None:
        return None
    return str(s).strip()


def _add(a, b):
    if a is None or b is None:
        return None
    return a + b


def _subtract(a, b):
    if a is None or b is None:
        return None
    return a - b


def _multiply(a, b):
    if a is None or b is None:
        return None
    return a * b


def _divide(a, b):
    if a is None or b is None:
        return None
    if b == 0:
        return None
    return a / b


def _coalesce(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None


def _is_null(a):
    return a is None


def _if(condition, then_value, else_value):
    if condition:
        return then_value
    return else_value


def _concat(*args):
    if not args:
        return ""
    return "".join(str(arg) if arg is not None else "" for arg in args)


def _length(a):
    if a is None:
        return None
    return len(a)


def _equals(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a == b


def _greater_than(a, b):
    if a is None or b is None:
        return None
    return a > b


def _less_than(a, b):
    if a is None or b is None:
        return None
    return a < b


_Func = Callable[..., object]

_FUNCTIONS: dict[str, _Func] = {
    "upper": _upper,
    "lower": _lower,
    "trim": _trim,
    "add": _add,
    "subtract": _subtract,
    "multiply": _multiply,
    "divide": _divide,
    "coalesce": _coalesce,
    "is_null": _is_null,
    "if": _if,
    "concat": _concat,
    "length": _length,
    "equals": _equals,
    "greater_than": _greater_than,
    "less_than": _less_than,
}


def _parse_number(text: str) -> int | float:
    if "." in text:
        return float(text)
    return int(text)
