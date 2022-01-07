# The purpose of __all__ is to define the public API of this module, and which
# objects are imported if we call "from dls_python3_skeleton.hello import *"
__all__ = [
    "HelloClass",
    "say_hello_lots",
]


class HelloClass:
    """A class whose only purpose in life is to say hello"""

    def __init__(self, name: str):
        """
        Args:
            name: The initial value of the name of the person who gets greeted
        """
        #: The name of the person who gets greeted
        self.name = name

    def format_greeting(self) -> str:
        """Return a greeting for `name`

        >>> HelloClass("me").format_greeting()
        'Hello me'
        """
        greeting = f"Hello {self.name}"
        return greeting


def say_hello_lots(hello: HelloClass = None, times=5):
    """Print lots of greetings using the given `HelloClass`

    Args:
        hello: A `HelloClass` that `format_greeting` will be called on.
            If not given, use a HelloClass with name="me"
        times: The number of times to call it
    """
    if hello is None:
        hello = HelloClass("me")
    for _ in range(times):
        print(hello.format_greeting())
