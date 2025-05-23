import re
from dataclasses import dataclass
from typing import List, Optional, Union


# AST node definitions with line numbers
@dataclass
class Node:
    line: int


@dataclass
class Document(Node):
    blocks: List[Node]


@dataclass
class TextInline(Node):
    value: str


@dataclass
class LinkInline(Node):
    text: str
    url: str


Inline = Union[TextInline, LinkInline]


@dataclass
class Heading(Node):
    level: int
    inlines: List[Inline]


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
    tag: str  # '???' or '!!!'
    title: str
    blocks: List[Node]
    foldable: bool


class Parser:
    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.current = 0
        self.total = len(self.lines)

    def eof(self) -> bool:
        return self.current >= self.total

    def peek(self) -> str:
        return "" if self.eof() else self.lines[self.current]

    def next_line(self) -> str:
        line = self.peek()
        self.current += 1
        return line

    def parse(self) -> Document:
        blocks: List[Node] = []
        while not self.eof():
            block = self.parse_block()
            if block:
                blocks.append(block)
        return Document(blocks=blocks, line=1)

    def parse_block(self) -> Optional[Node]:
        line = self.peek()
        stripped = line
        # Skip blank lines
        if not stripped:
            self.next_line()
            return None
        # Code fence
        if stripped.startswith("```"):
            return self.parse_code_block()
        # Heading
        if re.match(r"#{1,6}\s+", stripped):
            return self.parse_heading()
        # Bullet list
        if stripped.startswith(("- ", "+ ", "*")):
            return self.parse_bullet_list()
        # Blockquote
        if stripped.startswith(">"):
            return self.parse_quote_block()
        # Admonition
        if stripped.startswith("!!!") or stripped.startswith("???"):
            return self.parse_admonition()
        # Tab block
        if stripped.startswith("==="):
            return self.parse_tab_block()
        # Paragraph
        return self.parse_paragraph()

    def parse_code_block(self) -> CodeBlock:
        start_ln = self.current + 1
        fence = self.next_line().strip()
        lang = fence[3:].strip() or None
        content_lines: List[str] = []
        while not self.eof():
            line = self.next_line()
            if line.strip().startswith("```"):
                break
            content_lines.append(line)
        content = "\n".join(content_lines)
        return CodeBlock(language=lang, content=content, line=start_ln)

    def parse_heading(self) -> Heading:
        line = self.next_line().strip()
        ln = self.current
        m = re.match(r"(#{1,6})\s+(.*)", line)
        level = len(m.group(1))
        text = m.group(2)
        inlines = self.parse_inlines(text, ln)
        return Heading(level=level, inlines=inlines, line=ln)

    def parse_bullet_list(self) -> BulletList:
        items: List[ListItem] = []
        start_ln = self.current + 1
        while not self.eof():
            line = self.peek()
            stripped = line.strip()
            if not stripped.startswith("- "):
                break
            ln = self.current + 1
            content = stripped[2:].strip()
            inlines = self.parse_inlines(content, ln)
            para = Paragraph(inlines=inlines, line=ln)
            items.append(ListItem(blocks=[para], line=ln))
            self.next_line()
        return BulletList(items=items, line=start_ln)

    def parse_quote_block(self) -> QuoteBlock:
        lines: List[str] = []
        start_ln = self.current + 1
        while not self.eof():
            line = self.peek()
            if not line.lstrip().startswith(">"):
                break
            content = line.lstrip()[1:].lstrip()
            lines.append(content)
            self.next_line()
        return QuoteBlock(lines=lines, line=start_ln)

    def parse_admonition(self) -> Admonition:
        line = self.next_line().strip()
        start_ln = self.current
        parts = line.split(None, 2)
        tag = parts[0]
        title = parts[1] if len(parts) > 1 else ""
        # Collect indented content
        content_lines: List[str] = []
        while not self.eof():
            peek = self.peek()
            if peek.startswith("    ") or peek.startswith("\t"):
                content_lines.append(peek.lstrip())
                self.next_line()
            else:
                break
        # Recursively parse inner blocks
        inner_parser = Parser("\n".join(content_lines))
        doc = inner_parser.parse()
        return Admonition(
            tag=tag, title=title, blocks=doc.blocks, foldable=False, line=start_ln
        )

    def parse_tab_block(self) -> TabBlock:
        start_ln = self.current + 1
        # consume '::: tabs'
        self.next_line()
        tabs: List[Tab] = []
        current_tab: Optional[Tab] = None
        content_lines: List[str] = []
        while not self.eof():
            line = self.peek()
            stripped = line.strip()
            # End of tabs
            if stripped.startswith("::: endtabs"):
                if current_tab:
                    inner = Parser("\n".join(content_lines))
                    current_tab.blocks = inner.parse().blocks
                    tabs.append(current_tab)
                self.next_line()
                break
            # New tab
            m = re.match(r":::\s*tab\s+(.*)", stripped)
            if m:
                if current_tab:
                    inner = Parser("\n".join(content_lines))
                    current_tab.blocks = inner.parse().blocks
                    tabs.append(current_tab)
                title = m.group(1)
                current_tab = Tab(title=title, blocks=[], line=self.current + 1)
                content_lines = []
                self.next_line()
            else:
                content_lines.append(line)
                self.next_line()
        return TabBlock(tabs=tabs, line=start_ln)

    def parse_paragraph(self) -> Paragraph:
        start_ln = self.current + 1
        lines: List[str] = []
        while not self.eof():
            line = self.peek()
            stripped = line.strip()
            # Stop at blank or new block start
            if not stripped or re.match(
                r"(?:```|#{1,6}\s+|-\s+|>\s*|!!!|\?\?\?|:::)", stripped
            ):
                break
            lines.append(stripped)
            self.next_line()
        text = " ".join(lines)
        inlines = self.parse_inlines(text, start_ln)
        return Paragraph(inlines=inlines, line=start_ln)

    def parse_inlines(self, text: str, line: int) -> List[Inline]:
        inlines: List[Inline] = []
        pos = 0
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            if m.start() > pos:
                inlines.append(TextInline(value=text[pos : m.start()], line=line))
            inlines.append(LinkInline(text=m.group(1), url=m.group(2), line=line))
            pos = m.end()
        if pos < len(text):
            inlines.append(TextInline(value=text[pos:], line=line))
        return inlines
