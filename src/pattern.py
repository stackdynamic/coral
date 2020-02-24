import itertools
from abc import ABC, abstractmethod
from tokens import TokenType, Token


class Match:
    def __init__(self, is_match, groups=None):
        self.is_match = is_match
        self.groups = groups

    def __bool__(self):
        return self.is_match

    def __str__(self):
        return str(self.__bool__())


class Pattern(ABC):
    @abstractmethod
    def match(self, token_stream):
        """
        pattern for matching against fixed sequence of tokens
        :param tokens: iterator of tokens
        :return: Match object
        """
        pass


class TokenSequence(Pattern):
    def __init__(self, *pattern):
        """
        directly matches against provided Token objects
        :param pattern: Any combination of Token objects and TokenTypes to match against
        """
        self.pattern = pattern
        self.pattern_len = len(self.pattern)

    def check_token(self, i, token):
        """
        checks if token matches ith element of self.pattern
        :param i: index of self.pattern to check against
        :param token: Token object
        :return: boolean indicating match
        """
        p = self.pattern[i]
        if isinstance(p, TokenType):
            return token.token_type == p
        elif isinstance(p, Token):
            return token == p
        else:
            raise TypeError("TokenSequence pattern contains non-TokenType or Token object")

    def match(self, token_stream):
        try:
            for i, token in enumerate(token_stream.stream()):
                if not self.check_token(i, token):
                    break
            else:
                token_stream.consume(self.pattern_len)
                return Match(True)
        except StopIteration:
            pass
        return Match(False)


class TerminatingSequence(Pattern):
    def __init__(self, terminator=Token(TokenType.GROUPING, ";")):
        self.terminator = terminator

    def match(self, token_stream):
        """
        consumes tokens until a terminator is found
        :return: Match(True) (error if terminator not found)
        """
        try:
            for token in token_stream:
                if token == self.terminator:
                    return Match(True)
        except StopIteration:
            raise EOFError(
                "attempted to parse terminating sequence against stream without terminator")


class BracketedSequence(Pattern):
    def __init__(self, open, close):
        self.open = open
        self.close = close

    def match(self, token_stream):
        """
        reads tokens until there is a balanced amount of open_bracketing and closing bracket-types
        :param open_bracket: open_bracketing bracket-type
        :param close_bracket: closing bracket-type
        :return: the number of read tokens, the read tokens if successful, else None
        """
        buffer = []
        level = 0
        for token in token_stream:
            if token == self.open:
                level += 1
            elif token.value == self.close:
                level -= 1
            buffer.append(token)
            if not level:
                break
        else:
            raise SyntaxError("unbalanced bracketed expression detected")
        return Match(len(buffer), buffer[1:-1])


class DelimitedSequence(Pattern):
    def __init__(self, filter_func=lambda x: True, delimiter=Token(TokenType.SEPARATOR, ",")):
        """
        pattern for matching against a delimited sequence e.g list, function args, etc.
        :param delimiter: Token delimiter - default is separator comma
        :param filter_func: filtering function for elements
        """
        self.delimiter = delimiter
        self.filter_func = filter_func

    def match(self, token_stream):
        groups = []
        while True:
            e = token_stream.peek()
            if self.filter_func(e):
                groups.append(e)
                next(token_stream)
            else:
                break
            d = token_stream.peek()
            if d == self.delimiter:
                next(token_stream)
            else:
                break
        return Match(True, groups)
