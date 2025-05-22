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
