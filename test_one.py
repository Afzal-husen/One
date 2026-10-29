import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import one


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = one.main(list(argv))
    return code, out.getvalue() + err.getvalue()


class OneTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.file = Path(self.dir.name) / "one.json"
        os.environ["ONE_FILE"] = str(self.file)

    def tearDown(self):
        del os.environ["ONE_FILE"]
        self.dir.cleanup()

    def test_no_thing_shows_question(self):
        self.assertIn("ONE thing I can do", run()[1])

    def test_set_then_show(self):
        run("set", "write", "ch.1")
        self.assertIn("write ch.1", run()[1])

    def test_done_bumps_streak_and_clears(self):
        run("set", "x")
        self.assertEqual(run("done")[0], 0)
        state = one.load()
        self.assertEqual((state["thing"], state["streak"]), (None, 1))
        self.assertEqual(state["done"][0]["thing"], "x")
        self.assertIn("x", run("log")[1])

    def test_old_file_without_log_still_loads(self):
        self.file.write_text('{"thing": "a", "streak": 4}')
        self.assertEqual(one.load(), {"thing": "a", "streak": 4, "done": [],
                                      "started": None, "best": 0.0})

    def test_stopwatch_sets_and_beats_record(self):
        with mock.patch("one.time.time", return_value=1000.0):
            run("start")
        self.assertEqual(run("start")[0], 1)  # already running
        with mock.patch("one.time.time", return_value=1600.0):
            self.assertIn("NEW RECORD", run("stop")[1])
        self.assertEqual(one.load()["best"], 600.0)
        with mock.patch("one.time.time", return_value=2000.0):
            run("start")
        with mock.patch("one.time.time", return_value=2100.0):
            self.assertIn("to beat it", run("stop")[1])
        self.assertEqual(one.load()["best"], 600.0)

    def test_stop_when_not_running_fails(self):
        self.assertEqual(run("stop")[0], 1)

    def test_done_stops_running_stopwatch(self):
        run("set", "x")
        run("start")
        run("done")
        self.assertIsNone(one.load()["started"])

    def test_done_without_thing_fails(self):
        self.assertEqual(run("done")[0], 1)
        self.assertEqual(one.load()["streak"], 0)

    def test_corrupt_file_loads_defaults(self):
        self.file.write_text("{not json")
        self.assertEqual(one.load(), {"thing": None, "streak": 0, "done": [],
                                      "started": None, "best": 0.0})

    def test_empty_set_rejected(self):
        self.assertEqual(run("set", " ")[0], 1)


if __name__ == "__main__":
    unittest.main()
