#!/usr/bin/env python3
"""
Static Terraform sanity checks that do not need provider downloads.

`terraform validate` needs `terraform init`, which needs registry.terraform.io. In
CI that is fine. On a locked-down runner (or in a sandbox with no egress) it is not,
and a broken module graph should still be caught before it reaches a plan. These
three checks catch the mistakes that actually happen when a platform is decomposed
into modules:

  1. module dependency cycles      — Terraform refuses to build a graph at all
  2. undeclared module inputs      — a variable passed that the module never declares
  3. missing required inputs       — a module variable with no default and no value
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "infra" / "terraform"
MODULE_BLOCK = re.compile(r'module\s+"([^"]+)"\s*\{', re.M)
VARIABLE_DECL = re.compile(r'^variable\s+"([^"]+)"', re.M)
HAS_DEFAULT = re.compile(r'^variable\s+"([^"]+)"\s*\{(.*?)^\}', re.M | re.S)


def read_dir(path: Path) -> str:
    return "\n".join(f.read_text() for f in sorted(path.glob("*.tf")))


def block_body(text: str, start: int) -> tuple[str, int]:
    """Return the body of the brace-delimited block whose '{' follows `start`."""
    i = text.index("{", start)
    depth, j = 0, i
    while j < len(text):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j], j
        j += 1
    raise ValueError("unbalanced braces")


def module_blocks(text: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    for m in MODULE_BLOCK.finditer(text):
        if m.start() < pos:
            continue
        body, end = block_body(text, m.start())
        out.append((m.group(1), body))
        pos = end
    return out


def top_level_attributes(body: str) -> set[str]:
    """
    Attribute names at depth 0 of a block body.

    A naive `^\\s*(\\w+)\\s*=` over the whole body also matches keys inside nested maps
    and objects — `model_name`, `cpu`, `tenant` — and reports them as bogus module
    inputs. Tracking brace/bracket depth, and skipping strings, comments and
    heredocs, is what makes the check trustworthy enough to gate a build on.
    """
    names: set[str] = set()
    depth = 0
    i, n = 0, len(body)
    current = ""

    while i < n:
        ch = body[i]

        if ch == "#" or body.startswith("//", i):
            while i < n and body[i] != "\n":
                i += 1
            continue
        if body.startswith("/*", i):
            j = body.find("*/", i)
            i = n if j < 0 else j + 2
            continue
        if body.startswith("<<", i):
            eol = body.find("\n", i)
            tag = body[i:eol].lstrip("<-").strip() if eol > 0 else ""
            end = body.find("\n" + tag, eol) if tag else -1
            i = n if end < 0 else end + len(tag) + 1
            continue
        if ch == '"':
            i += 1
            while i < n and body[i] != '"':
                i += 2 if body[i] == "\\" else 1
            i += 1
            continue

        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        elif ch == "=" and depth == 0 and body[i:i + 2] != "==":
            candidate = current.strip().split()[-1] if current.strip() else ""
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
                names.add(candidate)
            current = ""
        elif ch == "\n":
            current = ""
        else:
            current += ch
        i += 1

    return names


def module_declared_vars(source: str, env_dir: Path) -> tuple[set[str], set[str]]:
    """(all declared, required-without-default) for a module referenced by `source`."""
    mod_dir = (env_dir / source).resolve()
    if not mod_dir.is_dir():
        return set(), set()
    text = read_dir(mod_dir)
    declared = set(VARIABLE_DECL.findall(text))
    required = {name for name, body in HAS_DEFAULT.findall(text)
                if not re.search(r"^\s*default\s*=", body, re.M)}
    return declared, required


def check_env(env_dir: Path) -> list[str]:
    problems: list[str] = []
    text = read_dir(env_dir)
    blocks = module_blocks(text)
    names = {n for n, _ in blocks}

    graph: dict[str, set[str]] = {}
    for name, body in blocks:
        graph[name] = {m for m in re.findall(r"module\.([A-Za-z0-9_-]+)", body)
                       if m in names and m != name}

        src = re.search(r'source\s*=\s*"([^"]+)"', body)
        if not src:
            problems.append(f"{env_dir.name}: module '{name}' has no source")
            continue

        passed = top_level_attributes(body) - {"source"}
        declared, required = module_declared_vars(src.group(1), env_dir)
        if not declared:
            problems.append(f"{env_dir.name}: module '{name}' source '{src.group(1)}' not found")
            continue
        for undeclared in sorted(passed - declared):
            problems.append(
                f"{env_dir.name}: module '{name}' is passed '{undeclared}', "
                f"which {src.group(1)} does not declare")
        for missing in sorted(required - passed):
            problems.append(
                f"{env_dir.name}: module '{name}' is missing required input '{missing}'")

    # cycle detection: iterative DFS with a colour map
    WHITE, GREY, BLACK = 0, 1, 2
    colour = dict.fromkeys(graph, WHITE)

    def visit(node: str, path: list[str]) -> None:
        colour[node] = GREY
        for dep in sorted(graph[node]):
            if colour[dep] == GREY:
                cycle = " → ".join(path[path.index(dep):] + [dep]) if dep in path \
                    else f"{node} → {dep}"
                problems.append(f"{env_dir.name}: module dependency cycle: {cycle}")
            elif colour[dep] == WHITE:
                visit(dep, path + [dep])
        colour[node] = BLACK

    for node in sorted(graph):
        if colour[node] == WHITE:
            visit(node, [node])

    return problems


def main() -> int:
    envs = sorted((ROOT / "envs").iterdir())
    if not envs:
        print("no environments found", file=sys.stderr)
        return 1
    all_problems: list[str] = []
    for env in envs:
        if env.is_dir():
            all_problems += check_env(env)

    if all_problems:
        print("Terraform graph check FAILED:\n")
        for p in all_problems:
            print(f"  ✗ {p}")
        return 1

    print(f"Terraform graph check passed for: {', '.join(e.name for e in envs if e.is_dir())}")
    print("  ✓ no module dependency cycles")
    print("  ✓ every module input is declared by its module")
    print("  ✓ every required module input is supplied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
