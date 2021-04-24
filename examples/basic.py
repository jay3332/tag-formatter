import tagformatter


class User:
    name = "John"
    age = 15


user = User()
parser = tagformatter.Parser()


@parser.tag("user")
def tag_user(env):
    return env.user.name


@tag_user.tag("age", alias="a")
def user_age(env):
    return env.user.age


@parser.tag("minus")
def minus(env, low: int, high: int):
    return abs(low-high)


string = "{user} is {user.age} years old. {minus:5,2}"
print(parser.parse(string, {"user": user}))
