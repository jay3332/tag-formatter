import random
import tagformatter

parser = tagformatter.Parser()

@parser.tag(name="random")
def random_tag(env, min_: int, max_: int = 10):
  return random.randint(min_, max_)

@random_tag.tag()
def choice(env, *items):
  return random.choice(items)

parser.parse('Random number: {random:5} | Random item: {random.choice:this,that,other}')