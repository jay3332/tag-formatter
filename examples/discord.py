from discord.ext import commands
from tagformatter import Parser, converter
import random
import os


class TagParser(Parser):
    def __init__(self):
        super().__init__(delimiter=r"\:", argument_delimiter=r",\s?")
        

parser = TagParser()


@parser.tag("user", alias="member")
def _user(env):
    return str(env.user)


@_user.tag("name")
def _user_name(env):
    return env.user.name


@_user.tag("mention", alias="ping")
def _user_mention(env):
    return env.user.mention


@_user.tag("discriminator", alias="discrim")
def _user_discrim(env):
    return env.user.discriminator


@_user.tag("id")
def _user_id(env):
    return env.user.id


@parser.tag("channel")
def _channel(env):
    return env.channel.name


@_channel.tag('mention')
def _channel_mention(env):
    return env.channel.mention


@_channel.tag('id')
def _channel_id(env):
    return env.channel.id


@parser.tag("guild")
def _guild(env):
    return env.guild.name


# Fun tags
@parser.tag("random", alias="rng")
def _random(env, min_: int, max_: int):
    return random.randint(min_, max_)


@_random.tag("choice")
def _random_choice(env, *items):
    return random.choice(items)

# Converters
@converter
def get_user(parser_, arg):
    return parser_.env.ctx.bot.get_user(int(arg))


@parser.tag("get_user")
def _get_user(env, user: get_user):
    return str(user)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__("!")
        self.parser = TagParser

    def run(self):
        super().run(os.environ['TOKEN'])


bot = Bot()


@bot.command()
async def parse_tags(ctx, *, tag):
    env = {"ctx": ctx, "author": ctx.author, "channel": ctx.channel, "guild": ctx.guild}
    await ctx.send(ctx.bot.parser().parse(tag, env))


if __name__ == '__main__':
    bot.run()

# Now, try running your bot and sending:
# !parse_tags Your tag is {user}, this message was sent in {channel.mention} in the server {guild}. Random number: {random:1,10}
