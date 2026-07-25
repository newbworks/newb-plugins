#!/usr/bin/env python3
"""Launch the `newb-dev` MCP server, installing it first if need be.

Claude Code runs this over stdio when the newb-builder plugin loads, so it must
be stdlib-only (the machine may have nothing else) and it must hand the stdio
channel to the real server via exec — anything printed on stdout would be read
as MCP protocol traffic.

Resolution order, cheapest first:

1. ``NEWB_DEV_SERVER_CMD`` — explicit override, for anyone running from a repo
   checkout (e.g. ``pipenv run newb-dev-server``).
2. ``newb.marketplace.devserver`` already importable by this interpreter.
3. ``newb-dev-server`` already on PATH.
4. A managed venv at ``~/.newb/dev-venv`` — created and installed into once,
   then reused. First launch is slow; later ones are immediate.

Failure is LOUD. A bootstrap that dies quietly leaves the expert with a server
that connected but has no tools, which reads as "the marketplace is broken"
rather than "run this one command" — so every exit path prints what happened and
what to do about it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Where to install from. newb is not on PyPI yet, so the default is the repo.
# Override to pin a fork or a tag — or to point at a local checkout, which is
# what anyone working ON newb wants:
#
#   NEWB_DEV_INSTALL_SPEC="-e /path/to/newb"
#
# The value is shell-split, so multi-word specs like `-e <path>` work; an
# editable install means repo edits reach the dev server with no reinstall.
DEFAULT_SPEC = os.environ.get(
    "NEWB_DEV_INSTALL_SPEC", "git+https://github.com/newbworks/newb.git")
VENV_DIR = Path(os.environ.get(
    "NEWB_DEV_VENV", str(Path.home() / ".newb" / "dev-venv")))
ENTRY = "newb-dev-server"


def die(problem: str, fix: str) -> "NoReturn":  # noqa: F821
    sys.stderr.write(
        f"\nnewb-dev could not start.\n\n  {problem}\n\n  Fix: {fix}\n\n"
        "  (This is the local dev server for building your own expert agent. "
        "The rest of the newb-builder plugin still works without it.)\n\n")
    sys.exit(1)


def exec_server(argv: list) -> "NoReturn":  # noqa: F821
    """Hand over stdio. os.execv replaces this process, so the MCP server owns
    the pipes directly — no wrapper sitting between it and the client."""
    try:
        os.execv(argv[0], argv)
    except OSError as exc:
        die(f"could not launch {argv[0]}: {exc}",
            "check the file exists and is executable, or set "
            "NEWB_DEV_SERVER_CMD to a working command.")


def venv_bin(name: str) -> Path:
    sub = "Scripts" if os.name == "nt" else "bin"
    return VENV_DIR / sub / (name + (".exe" if os.name == "nt" else ""))


def ensure_venv() -> Path:
    """Create ~/.newb/dev-venv and install newb into it. Returns the entry point."""
    entry = venv_bin(ENTRY)
    if entry.is_file():
        return entry

    sys.stderr.write(
        "newb-dev: first launch — installing the local dev server into "
        f"{VENV_DIR}. This takes a minute; later launches are instant.\n")
    if not (VENV_DIR / "pyvenv.cfg").is_file():
        try:
            import venv  # noqa: PLC0415 - only needed on the slow path

            venv.EnvBuilder(with_pip=True, clear=False).create(str(VENV_DIR))
        except Exception as exc:  # noqa: BLE001
            die(f"could not create a virtualenv at {VENV_DIR}: {exc}",
                "ensure python3 has the `venv` module (on Debian/Ubuntu: "
                "apt install python3-venv), or set NEWB_DEV_VENV to a "
                "writable path.")

    python = venv_bin("python")
    if not python.is_file():  # some builds only ship python3
        python = venv_bin("python3")
    import shlex

    try:
        proc = subprocess.run(
            [str(python), "-m", "pip", "install", "--quiet",
             *shlex.split(DEFAULT_SPEC)],
            capture_output=True, text=True, timeout=900,
        )
    except subprocess.TimeoutExpired:
        die("installing the dev server timed out after 15 minutes.",
            f"check your network, then retry. Installing from: {DEFAULT_SPEC}")
    except OSError as exc:
        die(f"could not run pip in {VENV_DIR}: {exc}",
            "delete that directory and reload the plugin to rebuild it.")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[-800:]
        die(f"installing newb failed:\n\n{detail}",
            f"if this is a network or auth error, check access to {DEFAULT_SPEC}. "
            f"Otherwise delete {VENV_DIR} and reload the plugin to retry.")

    entry = venv_bin(ENTRY)
    if not entry.is_file():
        die(f"newb installed but {ENTRY} is not in {VENV_DIR}.",
            "the installed version may predate the dev server — reinstall from "
            "a newer newb, or set NEWB_DEV_SERVER_CMD to run it directly.")
    return entry


def main() -> None:
    override = os.environ.get("NEWB_DEV_SERVER_CMD", "").strip()
    if override:
        import shlex

        parts = shlex.split(override)
        resolved = shutil.which(parts[0])
        if not resolved:
            die(f"NEWB_DEV_SERVER_CMD points at {parts[0]!r}, which is not on PATH.",
                "correct the variable or unset it to use the managed install.")
        exec_server([resolved] + parts[1:])

    # Already importable here (a repo checkout, or a venv this script is
    # running inside): skip every install path.
    try:
        from newb.marketplace.devserver import main as serve  # noqa: PLC0415

        serve()
        return
    except ImportError:
        pass

    on_path = shutil.which(ENTRY)
    if on_path:
        exec_server([on_path])

    exec_server([str(ensure_venv())])


if __name__ == "__main__":
    main()
