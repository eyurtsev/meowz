from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class Node:
    pass


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
    tag: str             # '???' or '!!!'
    title: str
    blocks: List[Node]
    foldable: bool
