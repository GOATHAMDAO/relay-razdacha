import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runner.runner import Runner


class FailedRecipientsTests(unittest.TestCase):
    def test_failed_recipient_file_is_reset_and_deduplicates_addresses(self):
        runner = Runner.__new__(Runner)

        with tempfile.TemporaryDirectory() as temp_dir:
            failed_path = Path(temp_dir) / "failed.txt"
            failed_path.write_text("old-address\n", encoding="utf-8")

            with patch("runner.runner.FAILED_RECIPIENTS", str(failed_path), create=True):
                self.assertTrue(hasattr(runner, "_reset_failed_recipients"))
                if not hasattr(runner, "_reset_failed_recipients"):
                    return

                runner._reset_failed_recipients()
                runner._record_failed_recipient("0xFailed")
                runner._record_failed_recipient("0xFailed")

            self.assertEqual(failed_path.read_text(encoding="utf-8"), "0xFailed\n")

    def test_distribution_records_failed_result_and_exception(self):
        runner = Runner.__new__(Runner)
        runner.private_key = "unused"
        runner.address = "0xSender"
        runner.recipients = ["0xFailedResult", "0xFailedException"]

        with tempfile.TemporaryDirectory() as temp_dir:
            failed_path = Path(temp_dir) / "failed.txt"
            with patch("runner.runner.FAILED_RECIPIENTS", str(failed_path), create=True), \
                    patch.object(runner, "_get_balance", return_value=1.0), \
                    patch.object(runner, "_confirm", return_value=True), \
                    patch.object(runner, "_generate_amount", return_value=1), \
                    patch.object(runner, "_single_bridge", side_effect=[0, RuntimeError("boom")]), \
                    patch("runner.runner.sync_sleep"):
                runner._run_distribution()

            self.assertEqual(
                failed_path.read_text(encoding="utf-8"),
                "0xFailedResult\n0xFailedException\n",
            )


if __name__ == "__main__":
    unittest.main()
