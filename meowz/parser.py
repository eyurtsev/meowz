from dataclasses import dataclass
from typing import List, Optional, Union

from lark import Lark

from meowz.grammar import grammar

# Lark grammar for a subset of Markdown with mkdocs-style extensions

# Initialize the parser
parser = Lark(grammar, parser='lalr', propagate_positions=True)

# AST node definitions
@dataclass
class Node:
    pass

@dataclass
class Document(Node):
    blocks: List[Node]

@dataclass
class Heading(Node):
    level: int
    text: str

@dataclass
class TextInline(Node):
    value: str

@dataclass
class LinkInline(Node):
    text: str
    url: str

Inline = Union[TextInline, LinkInline]

@dataclass
class Paragraph(Node):
    inlines: List[Inline]

@dataclass
class CodeBlock(Node):
    language: Optional[str]
    content: str

@dataclass
class ListItem(Node):
    blocks: List[Node]

@dataclass
class BulletList(Node):
    items: List[ListItem]

@dataclass
class QuoteBlock(Node):
    lines: List[str]

@dataclass
class Tab(Node):
    title: str
    blocks: List[Node]

@dataclass
class TabBlock(Node):
    tabs: List[Tab]

@dataclass
class Admonition(Node):
    tag: str             # '???' or '!!!'
    title: str
    blocks: List[Node]
    foldable: bool

# Visitor for printing the AST
class ASTPrinter:
    def __init__(self):
        self.indent_level = 0

    def _print(self, text: str):
        print('    ' * self.indent_level + text)

    def visit(self, node: Node):
        method = getattr(self, f"visit_{type(node).__name__}", self.generic_visit)
        method(node)

    def generic_visit(self, node: Node):
        self._print(f"{type(node).__name__}")
        self.indent_level += 1
        for field, value in vars(node).items():
            if isinstance(value, list):
                self._print(f"{field}:")
                self.indent_level += 1
                for item in value:
                    if isinstance(item, Node):
                        self.visit(item)
                    else:
                        self._print(repr(item))
                self.indent_level -= 1
            else:
                self._print(f"{field}: {repr(value)}")
        self.indent_level -= 1

    def visit_Document(self, doc: Document):
        self._print("Document")
        self.indent_level += 1
        for block in doc.blocks:
            self.visit(block)
        self.indent_level -= 1

    def visit_Heading(self, node: Heading):
        self._print(f"Heading(level={node.level}, text={node.text!r})")

    def visit_Paragraph(self, node: Paragraph):
        self._print("Paragraph")
        self.indent_level += 1
        for inline in node.inlines:
            self.visit(inline)
        self.indent_level -= 1

    def visit_TextInline(self, node: TextInline):
        self._print(f"TextInline({node.value!r})")

    def visit_LinkInline(self, node: LinkInline):
        self._print(f"LinkInline(text={node.text!r}, url={node.url!r})")

    def visit_CodeBlock(self, node: CodeBlock):
        lang = node.language or ''
        self._print(f"CodeBlock(language={lang!r})")
        self.indent_level += 1
        for line in node.content.splitlines():
            self._print(repr(line))
        self.indent_level -= 1

    def visit_BulletList(self, node: BulletList):
        self._print("BulletList")
        self.indent_level += 1
        for item in node.items:
            self.visit(item)
        self.indent_level -= 1

    def visit_ListItem(self, node: ListItem):
        self._print("ListItem")
        self.indent_level += 1
        for blk in node.blocks:
            self.visit(blk)
        self.indent_level -= 1

    def visit_QuoteBlock(self, node: QuoteBlock):
        self._print("QuoteBlock")
        self.indent_level += 1
        for line in node.lines:
            self._print(repr(line))
        self.indent_level -= 1

    def visit_TabBlock(self, node: TabBlock):
        self._print("TabBlock")
        self.indent_level += 1
        for tab in node.tabs:
            self.visit(tab)
        self.indent_level -= 1

    def visit_Tab(self, node: Tab):
        self._print(f"Tab(title={node.title!r})")
        self.indent_level += 1
        for blk in node.blocks:
            self.visit(blk)
        self.indent_level -= 1

    def visit_Admonition(self, node: Admonition):
        self._print(f"Admonition(tag={node.tag!r}, title={node.title!r}, foldable={node.foldable})")
        self.indent_level += 1
        for blk in node.blocks:
            self.visit(blk)
        self.indent_level -= 1


class MarkdownTransformer(Transformer):
    def start(self, items):
        return Document(blocks=items)

    def heading(self, items):
        hash_token = items[0]
        # Extract only inline nodes
        inlines = [item for item in items if isinstance(item, (TextInline, LinkInline))]
        level = len(hash_token.value)
        return Heading(level=level, inlines=inlines)

    def paragraph(self, items):
        inlines = [item for item in items if isinstance(item, (TextInline, LinkInline))]
        return Paragraph(inlines=inlines)

    def link(self, items):
        text_token, url_token = items
        return LinkInline(text=text_token.value, url=url_token.value)

    def text(self, items):
        token = items[0]
        return TextInline(value=token.value)

    def code_lines(self, items):
        # Single regex token
        return items[0].value

    def code_block(self, items):
        if len(items) == 2 and isinstance(items[0], Token) and items[0].type == 'LANGUAGE':
            language = items[0].value
            content = items[1]
        else:
            language = None
            content = items[0]
        return CodeBlock(language=language, content=content)

    def list_item(self, items):
        # Inline children and nested list items
        inline_nodes = [item for item in items if isinstance(item, (TextInline, LinkInline))]
        blocks = []
        if inline_nodes:
            blocks.append(Paragraph(inlines=inline_nodes))
        nested = [item for item in items if isinstance(item, ListItem)]
        if nested:
            blocks.append(BulletList(items=nested))
        return ListItem(blocks=blocks)

    def list_block(self, items):
        # items are ListItem
        return BulletList(items=items)

    def quote_block(self, items):
        lines = []
        # each group contains Tokens and inline nodes
        temp = []
        for item in items:
            if isinstance(item, (TextInline, LinkInline)):
                temp.append(item.value if isinstance(item, TextInline) else item.text)
            else:
                # on NEWLINE or '>' tokens, flush
                if temp:
                    lines.append(''.join(temp))
                    temp = []
        if temp:
            lines.append(''.join(temp))
        return QuoteBlock(lines=lines)

    def tab_header(self, items):
        # items: STRING token
        token = [i for i in items if isinstance(i, Token) and i.type == 'STRING'][0]
        return token.value.strip('"')

    def tab_body(self, items):
        # items are block nodes
        return items

    def tab_block(self, items):
        titles = []
        blocks = []
        for item in items:
            if isinstance(item, str):
                titles.append(item)
            elif isinstance(item, list):
                blocks = item
        tabs = [Tab(title=title, blocks=blocks) for title in titles]
        return TabBlock(tabs=tabs)

    def admonition(self, items):
        tag_token = items[0]
        title_token = items[1]
        blocks = items[2:]
        tag = tag_token.value
        title = title_token.value.strip('"')
        foldable = (tag == '???')
        return Admonition(tag=tag, title=title, blocks=blocks, foldable=foldable)

# --- Parse function ---

def parse(text: str) -> Document:
    """
    Parse the given Markdown text and return a Document AST.
    """
    tree = parser.parse(text)
    return MarkdownTransformer().transform(tree)