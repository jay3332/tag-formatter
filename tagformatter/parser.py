import itertools
import re
import typing
import inspect
from os import urandom
from .classes import Node, Tag, ParsedTag, Converter


class Parser:
    """
    The base parser.
    This class can be subclassed for custom behaviors.
    """
    def __init__(self, env: typing.Optional[dict] = None, **attrs):
        self._parse_attrs(attrs)
        self.env = env or {}
        self.tags = []
        self.setup()

    def _parse_attrs(self, attrs):
        self._delimiter = attrs.pop("delimiter", None) or r"\:"
        self._argument_delimiter = attrs.pop("argument_delimiter", None) or r",\s?"
        self._attribute_delimiter = attrs.pop("attribute_delimiter", None) or r"\."
        self._escape_character = attrs.pop("escape_character", "\\") or urandom(32).hex()
        self._start_character = attrs.pop("start_character", None) or "{"
        self._end_character = attrs.pop("end_character", None) or "}"
        self._case_insensitive = attrs.pop("case_insensitive", False)

    @property
    def is_case_insensitive(self):
        return self._case_insensitive

    def setup(self):
        """
        The setup function for when initiating the parser.
        This is to be used by the user.
        """
        pass

    def update_env(self, new):
        self.env.update(new)

    def get_env(self, var):
        return self.env.get(var)

    @staticmethod
    def _validate_match(pattern, query):
        return re.fullmatch(pattern, query) is not None

    def get_tag(self, name, *, parent=None):
        parent = parent or self
        if self._case_insensitive:
            name = name.lower()

        for tag in parent.tags:
            if tag.name == name or name in tag.aliases:
                return tag
        return None

    def tag(self, name: str, *, alias: str = None, aliases: typing.List[str] = None, **attrs):
        if not aliases:
            aliases = [alias] if alias else []

        if self._case_insensitive:
            aliases = [alias.lower() for alias in aliases]
            name = name.lower()

        def decorator(func):
            tag_ = Tag(self, func, name, aliases, **attrs)
            self.tags.append(tag_)
            return tag_

        return decorator

    def get_nodes(self, content):
        """
        Parses the tag nodes from a string.
        :return: List[Node]
        """
        nodes = []
        buffer = []
        previous = ""

        for i, char in enumerate(content):
            if (
                self._validate_match(self._start_character, char) and
                previous != self._escape_character
            ):
                buffer.append([i])

            if (
                self._validate_match(self._end_character, char) and
                previous != self._escape_character
            ):
                if len(buffer) <= 0:
                    continue
                buffer[-1].append(i)
                nodes.append(Node(*buffer[-1]))
                buffer.pop(-1)
            previous = char

        return nodes

    def _base_argument_conversion(self, arg, converter):
        if converter is str:
            return arg
        if converter in (int, float):
            try:
                return converter(arg)
            except ValueError:
                return None
        if converter is bool:
            lowered = arg.lower()
            if lowered in ("yes", "y", "true", "t", "enable", "enabled", "1", "on"):
                return True
            elif lowered in ("no", "n", "false", "f", "disable", "disabled", "0", "off"):
                return False
            return None
        if isinstance(converter, Converter):
            try:
                conv = converter.converter
                if len(inspect.signature(conv).parameters.values()) > 1:
                    return conv(self, arg)
                return conv(arg)
            except Exception:
                return None

    def do_argument_conversion(self, arg, converter) -> any:
        try:
            origin = converter.__origin__
        except AttributeError:
            pass
        else:
            if origin is typing.Union:
                _NoneType = type(None)
                for conv in converter.__args__:
                    if res := self._base_argument_conversion(arg, conv):
                        return res
                return None
        return self._base_argument_conversion(arg, converter)

    def parse_single_tag(self, tag) -> typing.Optional[ParsedTag]:
        """
        Turns a raw string into a `ParsedTag`.
        :param tag: The string to be parsed.
        :return: A `ParsedTag`.
        """
        regex = f"(?<!{re.escape(self._escape_character)})"
        splitted = re.split(regex+self._delimiter, tag)
        if len(splitted) < 2:
            tag_, args = splitted[0], ''
        else:
            tag_, args = splitted[:2]
        tag_body = re.split(self._attribute_delimiter, tag_)

        buffer = self
        for i, iteration in enumerate(tag_body, start=1):
            if got_tag := self.get_tag(iteration, parent=buffer):
                buffer = got_tag
                continue
            return None

        callback_params = list(inspect.signature(buffer.callback).parameters.values())
        if len(callback_params) < 1:
            raise ValueError("Parser callbacks must have at least on parameter (The environment, usually to be named 'env')")
        arguments = re.split(self._argument_delimiter, args)
        parsed_arguments = []

        if args.strip() != "":
            for i, argument in enumerate(arguments):
                try:
                    param = callback_params[i+1]
                except IndexError:
                    break
                converter = str
                annotation = param.annotation
                if annotation != getattr(inspect, '_empty'):
                    converter = annotation

                kind = param.kind
                if str(kind) == "VAR_POSITIONAL":
                    buf = []
                    for then_arg in arguments[i:]:
                        buf.append(self.do_argument_conversion(then_arg, converter))
                    parsed_arguments.append(buf)
                    continue

                parsed_arguments.append(self.do_argument_conversion(argument, converter))

            args_left = len(callback_params) - len(parsed_arguments) - 1
            if args_left > 0:
                for i in range(len(parsed_arguments), len(callback_params)):
                    try:
                        param = callback_params[i]
                    except IndexError:
                        break
                    default = param.default
                    if default != getattr(inspect, '_empty'):
                        parsed_arguments.append(default)
                        continue
                    parsed_arguments.append(None)

        return ParsedTag(self, tag, tag=buffer, args=parsed_arguments)


    def parse_nodes(self, nodes, content, env):
        """
        Parses a list of nodes to it's content.
        :param nodes: A list of `Nodes` to parse.
        :param content: The content associated with the nodes.
        :param env: The environment for the tag parsing session.
        :return str: The parsed string.
        """
        final = content

        for i, node in enumerate(nodes):
            string = final[node.coord[0]:node.coord[1]+1]
            string = string.lstrip(self._start_character)
            string = string.rstrip(self._end_character)
            parsed_tag = self.parse_single_tag(string)
            try:
                value = str(parsed_tag.tag.callback(env, *parsed_tag.args))
            except AttributeError:
                continue

            start, end = node.coord
            slice_length = (end + 1) - start
            replacement = len(value)
            diff = replacement - slice_length

            final = final[:start] + value + final[end + 1:]

            for future_node in itertools.islice(nodes, i + 1, None):
                if future_node.coord[0] > start:
                    new_start = future_node.coord[0] + diff
                else:
                    new_start = future_node.coord[0]

                if future_node.coord[1] > start:
                    new_end = future_node.coord[1] + diff
                else:
                    new_end = future_node.coord[1]
                future_node.coord = (new_start, new_end)

        return final

    def parse(self, string, env=None):
        session_env = self.env
        session_env.update(env or {})
        nodes = self.get_nodes(string)
        return self.parse_nodes(nodes, string, env)
