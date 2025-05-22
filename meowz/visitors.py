from meowz.ast import (
    Node, Document, Heading, TextInline, LinkInline, Paragraph,
    CodeBlock, ListItem, BulletList, QuoteBlock, Tab, TabBlock, Admonition
)


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
        self._print(f"Heading(level={node.level}, text={' '.join([inline.value if isinstance(inline, TextInline) else inline.text for inline in node.inlines])!r})")

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
