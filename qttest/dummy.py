class Token:
    def __init__(self, text, type=None, item=None):
        self.text = text
        self.type = type
        self.item = item


class Event:
    def __init__(self):
        self._callbacks = set()

    def watch(self, callback):
        self._callbacks.add(callback)

    def unwatch(self, callback):
        self._callbacks.remove(callback)

    def fire(self, *args, **kwargs):
        for callback in self._callbacks:
            callback(*args, **kwargs)


class Item:
    def __init__(self, name):
        self._name = name
        self.name_changed = Event()

    def name(self):
        return self._name

    def rename(self, name):
        """Override this to return False on name collisions etc."""
        if not name.isidentifier():
            return False
        self._name = name
        self.name_changed.fire(self)
        return True


class LocalVar(Item):
    def __init__(self, name, function):
        super().__init__(name)
        self._function = function


class Function(Item):
    def __init__(self, name, analysis):
        super().__init__(name)
        self._analysis = analysis
        self.code_changed = Event()
        self.name_changed.watch(self.code_changed.fire)

    def decompilation(self):
        return []

    def disassembly(self):
        return []


# convenience functions for writing dummy code
i = lambda item: Token(item.name(), "ident", item)
n = lambda value: Token(value, "num")
o = lambda opcode: Token(opcode, "opcode")
t = lambda name: Token(name, "type")
to_tokens = lambda code: [
    [token if isinstance(token, Token) else Token(token) for token in line]
    for line in code
]


class FunctionA(Function):
    def __init__(self, analysis):
        super().__init__("func_a", analysis)
        self.x = LocalVar("x", self)
        self.x.name_changed.watch(lambda _: self.code_changed.fire(self))

    def decompilation(self):
        func_b = self._analysis.functions()[1]

        code = [
            [t("int"), " ", i(self), "() {"],
            ["    // this is a comment"],
            ["    ", t("int"), " ", i(self.x), " = ", i(func_b), "(", n("123"), ");"],
            ["}"],
        ]

        return to_tokens(code)

    def disassembly(self):
        func_b = self._analysis.functions()[1]

        return to_tokens(
            [
                [";"],
                [f"; {self._name}"],
                [";"],
                [i(self), ":"],
                ["0x00000000 ", o("ENTER"), "    ", n("0x10")],
                ["0x00000001 ", o("CONST"), "    ", n("123")],
                ["0x00000002 ", o("ARG"), "      ", n("8")],
                ["0x00000003 ", o("LOCAL"), "    ", i(self.x)],
                ["0x00000004 ", o("CONST"), "    ", i(func_b), " ; comment"],
                ["0x00000005 ", o("CALL")],
                ["0x00000006 ", o("STORE4")],
                ["0x00000007 ", o("PUSH")],
                ["0x00000008 ", o("LEAVE"), "    ", n("0x10")],
            ]
        )


class FunctionB(Function):
    def __init__(self, analysis):
        super().__init__("func_b", analysis)

    def decompilation(self):
        return to_tokens(
            [
                [t("void"), " ", i(self), "() {"],
                ["    return;"],
                ["}"],
            ]
        )

    def disassembly(self):
        return to_tokens(
            [
                [";"],
                [f"; {self._name}"],
                [";"],
                [i(self), ":"],
                ["0x00000000 ", o("ENTER"), "    ", n("0x8")],
                ["0x00000007 ", o("PUSH")],
                ["0x00000008 ", o("LEAVE"), "    ", n("0x8")],
            ]
        )


class Analysis:
    def __init__(self):
        self.a = FunctionA(self)
        self.a.name_changed.watch(self.on_function_name_changed)

        self.b = FunctionB(self)
        self.b.name_changed.watch(self.on_function_name_changed)

        self._functions = [self.a, self.b]

    def functions(self):
        return self._functions

    def on_function_name_changed(self, function):
        if function == self.b:
            # a references b so watchers of a's code need to be notified
            self.a.code_changed.fire(self.a)
