"""Minimal KiCad S-expression reader/writer.

Lists are Python lists; atoms are str (unquoted symbols / numbers) or
Q (quoted strings), so a round trip keeps quoting intact.
"""


class Q(str):
    """A quoted string atom."""


def parse(text):
    pos = 0
    n = len(text)
    stack = [[]]
    while pos < n:
        c = text[pos]
        if c in " \t\r\n":
            pos += 1
        elif c == "(":
            stack.append([])
            pos += 1
        elif c == ")":
            node = stack.pop()
            stack[-1].append(node)
            pos += 1
        elif c == '"':
            pos += 1
            buf = []
            while text[pos] != '"':
                if text[pos] == "\\":
                    pos += 1
                    buf.append({"n": "\n", "t": "\t"}.get(text[pos], text[pos]))
                else:
                    buf.append(text[pos])
                pos += 1
            pos += 1
            stack[-1].append(Q("".join(buf)))
        else:
            start = pos
            while pos < n and text[pos] not in " \t\r\n()":
                pos += 1
            stack[-1].append(text[start:pos])
    return stack[0][0]


def _atom(a):
    if isinstance(a, Q):
        return '"' + a.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(a, float):
        s = ("%.4f" % a).rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(a)


def dump(node, indent=0):
    """Serialise in KiCad's style: one child list per line, atoms inline."""
    if not isinstance(node, list):
        return _atom(node)
    head = [x for x in node if not isinstance(x, list)]
    kids = [x for x in node if isinstance(x, list)]
    s = "(" + " ".join(_atom(x) for x in head)
    if not kids:
        return s + ")"
    pad = "\t" * (indent + 1)
    for k in kids:
        s += "\n" + pad + dump(k, indent + 1)
    return s + "\n" + "\t" * indent + ")"


def find(node, key):
    """First direct child list whose head is key."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def load_symbol(lib_path, name):
    lib = parse(open(lib_path).read())
    for s in find_all(lib, "symbol"):
        if s[1] == name:
            return s
    raise KeyError("%s not in %s" % (name, lib_path))


def pins(sym):
    """[(number, name, type, x, y, angle)] for unit 1 / common, body style 1."""
    out = []
    for unit in find_all(sym, "symbol"):
        u, style = unit[1].rsplit("_", 2)[-2:]
        if u not in ("0", "1") or style not in ("0", "1"):
            continue
        for p in find_all(unit, "pin"):
            at = find(p, "at")
            out.append((str(find(p, "number")[1]), str(find(p, "name")[1]), p[1],
                        float(at[1]), float(at[2]), int(float(at[3]))))
    return out


if __name__ == "__main__":
    import sys
    for num, nm, typ, x, y, a in pins(load_symbol(sys.argv[1], sys.argv[2])):
        print(num, nm, typ, x, y, a)
