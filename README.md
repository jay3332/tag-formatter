# tag-formatter
Tag-formatter is a Python Package designed to format strings that based on user-input.  
For example, tag-formatter can parse something such as:
```
Hello there, {user}!
```
Into something like:
```
Hello there, John!
```
## Installation
You can install tag-formatter using pip.
```
pip install tag-formatter
```
## Features
- Highly customizable
    - Uses regex delimiters that you can set.
- Uses a parser rather than things like `str.format`
    - Because this was meant for user input, str.format wouldn't work (invalid tags mean KeyErrors)
    - str.replace on the other hand, would be too tedious and limited.
- Argument parsing for tags
    - Basic and function-based converters
    - Default values for arguments
## Example
You can find more examples in the [examples folder](https://github.com/jay3332/tag-formatter/tree/master/examples).
```py
import random
import tagformatter

class User:
    name = 'John'
    age = 21

parser = tagformatter.Parser()

@parser.tag("user")
def user_tag(env):
    return env["user"].name

@user_tag.tag("age")
def user_age_tag(env):
    return env["user"].age

@parser.tag("random", alias="rng")
def rng_tag(env, low: int = 1, high: int = 10):
    return random.randint(low, high)

print(parser.parse("{user} is {user.age} years old. Random number: {random:1, 20}", 
      env={"user": User()}))
```