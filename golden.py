import contextlib
import io
import logging
import os
import tempfile

import machine
import pytest
import translator


@pytest.mark.golden_test("golden/*.yml")
def test_translator_and_machine(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source.asm")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target.o")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target)
            machine.main(target, input_stream)
        with open(target, "rb") as file:
            code = str(file.read())
        assert code == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
