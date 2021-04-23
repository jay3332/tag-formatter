import tagformatter


class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.happiness = 0

    def entertain(self, intensity=1):
        self.happiness += intensity


class Parser(tagformatter.Parser):
    def __init__(self):
        super().__init__(delimiter=r"\|", argument_delimiter=r",\s")


parser = Parser()


@parser.tag("user")
def tag_user(env):
    return env.get("user").name


@tag_user.tag("name")
def tag_user_name(env):
    return env.get("user").name


@tag_user.tag("age")
def tag_user_age(env):
    return env.get("user").age


@tag_user.tag("entertain")
def tag_user_entertain(env, intensity: int = 1):
    env.get("user").entertain(intensity)
    return env.get("user").happiness


to_be_parsed = "{user.name} is {user.age} years old. {user.entertain|2}"
print(parser.parse(to_be_parsed, env={"user": User('John', 24)}))
