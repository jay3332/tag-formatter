import typing
import tagformatter

p = tagformatter.Parser()

@p.tag('add')
def add(env, *things: typing.Union[int, float]):
  return sum(things)

print(p.parse('{add:1,2,3}'))
