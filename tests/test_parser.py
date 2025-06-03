from meowz.parser import Parser


MARKDOWN_1 = """\
# Hello World

## Subheader

> This is a quote
> with a second line

This is a long sentence and 
another long sentence

```python
import re
```

```js
function test() {
    console.log("Hello, world!");
}
```

!!! note "This is a note"

    tell me about yourself
    
    tell me some more about yourself
    
=== "Tab 1"
    
    Some content in the first tab
    
=== "Tab 2"

    Some content in the second tab.
"""


def test_parser() -> None:
    """Test the parser."""
    parser = Parser(MARKDOWN_1)
    document = parser.parse()
    assert document == []


MARKDOWN_2 = """\

=== "Tab 1"
    
    Some content in the first tab
    
=== "Tab 2"

    Some content in the second tab.
"""


def test_parsing_tabs() -> None:
    """Test parsing tabs."""
    parser = Parser(MARKDOWN_2)
    document = parser.parse()
    assert document == []