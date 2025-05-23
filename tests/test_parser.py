from meowz.parser2 import Parser


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
    
    

"""


def test_parser() -> None:
    """Test the parser."""
    parser = Parser(MARKDOWN_1)
    document = parser.parse()
    assert document == []
