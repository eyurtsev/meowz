from lark import Lark, Token, Transformer

from meowz.ast import (
    Node, Document, Heading, TextInline, LinkInline, Inline, Paragraph,
    CodeBlock, ListItem, BulletList, QuoteBlock, Tab, TabBlock, Admonition
)

grammar = r"""
start: block+

block: heading
     | admonition
     | tab_block
     | code_block
     | quote_block
     | list_block
     | paragraph

heading: HASHES WS_INLINE inline NEWLINE    -> heading

admonition: ADMO_TAG WS_INLINE STRING NEWLINE INDENT block+ DEDENT    -> admonition

# mkdocs-material tabs
tab_block: tab_header+ tab_body             -> tab_block
tab_header: "===" WS_INLINE STRING NEWLINE -> tab_header
tab_body: INDENT block+ DEDENT               -> tab_body

# fenced code blocks
code_block: "```" LANGUAGE? NEWLINE code_lines "```" NEWLINE?  -> code_block
code_lines: /(.|\n)*?(?=```)/

# blockquote
quote_block: ( ">" WS_INLINE? inline NEWLINE )+   -> quote_block

# bullet lists
list_block: list_item+                             -> list_block
list_item: LIST_MARKER WS_INLINE? inline NEWLINE (INDENT list_item+ DEDENT)?   -> list_item

# paragraphs (simple inline runs)
paragraph: inline+ NEWLINE+                        -> paragraph

# inline elements
?inline: link                                   -> link
       | TEXT                                   -> text

link: "[" TEXT "]" "(" URL ")"           -> link

HASHES: /#{1,6}/
ADMO_TAG: "???" | "!!!"
LIST_MARKER: /[-*+]/
LANGUAGE: /[a-zA-Z0-9_+\-]+/
URL: /[^()\s]+/
TEXT: /[^\[\]\n]+/
STRING: ESCAPED_STRING
WS_INLINE: /[ \t]+/

%import common.NEWLINE
%import common.INDENT
%import common.DEDENT
%import common.ESCAPED_STRING
%ignore /[ ]+$/
"""

# Initialize the parser
parser = Lark(grammar, parser='lalr', propagate_positions=True)

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

def parse(text: str) -> Document:
    """Parse the given Markdown text and return a Document AST. """
    tree = parser.parse(text)
    return MarkdownTransformer().transform(tree)