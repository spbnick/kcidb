"""kcidb namespace tests"""

import re
import json
import textwrap
import kcidb_io
import kcidb


class LightAssertsTestCase(kcidb.unittest.TestCase):
    """Light assertions test case"""

    def test_light_asserts_are_disabled(self):
        """Check light asserts are disabled"""
        self.assertFalse(kcidb_io.misc.LIGHT_ASSERTS,
                         "Tests must run with KCIDB_IO_HEAVY_ASSERTS "
                         "environment variable set to a non-empty string")
        self.assertFalse(kcidb.misc.LIGHT_ASSERTS,
                         "Tests must run with KCIDB_HEAVY_ASSERTS "
                         "environment variable set to a non-empty string")


class KCIDBMainFunctionsTestCase(kcidb.unittest.TestCase):
    """Test case for main functions"""

    def test_json_output_options(self):
        """Check JSON output options work"""
        self.assertExecutes("", "kcidb.schema_main",
                            stdout_re="\\{.*")
        self.assertExecutes("", "kcidb.schema_main", "--seq",
                            stdout_re="\x1e\\{.*")
        self.assertExecutes("", "kcidb.schema_main", "--indent=0",
                            stdout_re="\\{\".*")
        self.assertExecutes("", "kcidb.schema_main", "--indent=4",
                            stdout_re="\\{\n    \".*")
        self.assertExecutes("", "kcidb.schema_main", "--indent=2",
                            stdout_re="\\{\n  \".*")

    def test_submit_main(self):
        """Check kcidb-submit works"""
        driver_source = textwrap.dedent("""
            from unittest.mock import patch, Mock
            with patch("kcidb.mq.Publisher.__init__",
                       return_value=None) as init, \
                 patch("kcidb.mq.Publisher.future_publish") as future_publish:
                status = function()
                init.assert_called_once_with("project", "topic")
            return status
        """)
        argv = ["kcidb.submit_main", "-p", "project", "-t", "topic"]

        self.assertExecutes("", *argv, driver_source=driver_source)
        self.assertExecutes('{', *argv, driver_source=driver_source,
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', *argv, driver_source=driver_source,
                            status=1, stderr_re=".*ValidationError.*")

        empty = kcidb_io.new()

        driver_source = textwrap.dedent(f"""
            from unittest.mock import patch, Mock
            future = Mock()
            future.done = lambda: True
            future.add_done_callback = lambda cb: cb(future)
            future.result = Mock(return_value="id")
            with patch("kcidb.mq.Publisher.__init__",
                       return_value=None) as init, \
                 patch("kcidb.mq.Publisher.future_publish",
                       return_value=future) as future_publish:
                status = function()
                init.assert_called_once_with("project", "topic")
                future_publish.assert_called_once_with({repr(empty)})
            return status
        """)
        self.assertExecutes(json.dumps(empty), *argv,
                            driver_source=driver_source,
                            stdout_re="id\n")

        driver_source = textwrap.dedent(f"""
            from unittest.mock import patch, Mock, call
            future = Mock()
            future.done = lambda: True
            future.add_done_callback = lambda cb: cb(future)
            future.result = Mock(return_value="id")
            with patch("kcidb.mq.Publisher.__init__",
                       return_value=None) as init, \
                 patch("kcidb.mq.Publisher.future_publish",
                       return_value=future) as future_publish:
                status = function()
                init.assert_called_once_with("project", "topic")
                assert future_publish.call_count == 2
                future_publish.assert_has_calls([call({repr(empty)}),
                                                 call({repr(empty)})])
            return status
        """)
        self.assertExecutes(json.dumps(empty) + json.dumps(empty), *argv,
                            driver_source=driver_source,
                            stdout_re="id\nid\n")

    def test_query_main(self):
        """Check kcidb-query works"""
        driver_source = textwrap.dedent("""
            from unittest.mock import patch
            with patch("kcidb.Client"):
                return function()
        """)
        argv = ["kcidb.query_main", "-d", "bigquery:project.dataset"]
        self.assertExecutes("", *argv, driver_source=driver_source)

        argv = [
            "kcidb.query_main", "-d", "bigquery:project.dataset",
            "-c", "test:checkout:1", "-b", "test:build:1",
            "-t", "test:test:1",
            "--parents", "--children", "--objects-per-report", "10",
            "--indent=0",
        ]
        empty = kcidb_io.new()
        driver_source = textwrap.dedent(f"""
            from unittest.mock import patch, Mock
            client = Mock()
            client.query_iter = Mock(return_value=iter((
                {repr(empty)}, {repr(empty)},
            )))
            with patch("kcidb.Client", return_value=client) as Client:
                status = function()
            Client.assert_called_once_with(
                database="bigquery:project.dataset"
            )
            client.query_iter.assert_called_once_with(
                ids=dict(checkouts=["test:checkout:1"],
                         builds=["test:build:1"],
                         tests=["test:test:1"]),
                parents=True,
                children=True,
                objects_per_report=10
            )
            return status
        """)
        self.assertExecutes(
            json.dumps(empty), *argv,
            driver_source=driver_source,
            stdout_re=re.escape(
                json.dumps(empty) + "\n" +
                json.dumps(empty) + "\n"
            )
        )

    def test_schema_main(self):
        """Check kcidb-schema works"""
        self.assertExecutes("", "kcidb.schema_main", stdout_re="\\{.*")

    def test_validate_main(self):
        """Check kcidb-validate works"""
        self.assertExecutes('', "kcidb.validate_main")
        self.assertExecutes('{"version":{"major":4,"minor":0}}',
                            "kcidb.validate_main")
        self.assertExecutes('{', "kcidb.validate_main",
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', "kcidb.validate_main",
                            status=1, stderr_re=".*ValidationError.*")

    def test_upgrade_main(self):
        """Check kcidb-upgrade works"""
        major = kcidb_io.schema.LATEST.major
        minor = kcidb_io.schema.LATEST.minor

        prev_version = \
            json.dumps(dict(version=dict(major=major - 1, minor=minor))) + "\n"
        latest_version = \
            json.dumps(dict(version=dict(major=major, minor=minor))) + "\n"

        self.assertExecutes('', "kcidb.upgrade_main")
        self.assertExecutes('{', "kcidb.upgrade_main",
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', "kcidb.upgrade_main",
                            status=1, stderr_re=".*ValidationError.*")
        self.assertExecutes(latest_version, "kcidb.upgrade_main", "--indent=0",
                            stdout_re=re.escape(latest_version))
        self.assertExecutes(latest_version + latest_version,
                            "kcidb.upgrade_main", "--indent=0",
                            stdout_re=re.escape(latest_version +
                                                latest_version))
        self.assertExecutes(prev_version, "kcidb.upgrade_main", "--indent=0",
                            stdout_re=re.escape(latest_version))
        self.assertExecutes(prev_version + prev_version,
                            "kcidb.upgrade_main", "--indent=0",
                            stdout_re=re.escape(latest_version +
                                                latest_version))

    def test_count_main(self):
        """Check kcidb-count works"""
        self.assertExecutes('', "kcidb.count_main")
        self.assertExecutes('{', "kcidb.count_main",
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', "kcidb.count_main",
                            status=1, stderr_re=".*ValidationError.*")

        empty = json.dumps(dict(version=dict(major=4, minor=0)))
        self.assertExecutes(empty, "kcidb.count_main", stdout_re="0\n")
        self.assertExecutes(empty + empty, "kcidb.count_main",
                            stdout_re="0\n0\n")

        one_checkout = json.dumps(dict(
            version=dict(major=4, minor=0),
            checkouts=[dict(id="test:1", origin="test")]
        ))
        self.assertExecutes(one_checkout, "kcidb.count_main", stdout_re="1\n")
        self.assertExecutes(one_checkout + one_checkout,
                            "kcidb.count_main", stdout_re="1\n1\n")

    def test_summarize_main(self):
        """Check kcidb-summarize works"""
        self.assertExecutes('', "kcidb.summarize_main", "checkouts")
        self.assertExecutes('{', "kcidb.summarize_main", "checkouts",
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', "kcidb.summarize_main", "checkouts",
                            status=1, stderr_re=".*ValidationError.*")

        empty = json.dumps(dict(version=dict(major=4, minor=0)))
        self.assertExecutes(empty, "kcidb.summarize_main", "checkouts")
        self.assertExecutes(empty + empty, "kcidb.summarize_main", "checkouts")

        git_commit_hash = "c003f145ae96b769858ee5501189c582a97c6742"
        one_checkout = json.dumps(dict(
            version=dict(major=4, minor=0),
            checkouts=[
                dict(id="test:1",
                     git_commit_hash=git_commit_hash,
                     origin="test")
            ]
        ))
        self.assertExecutes(one_checkout, "kcidb.summarize_main", "checkouts",
                            stdout_re="c003f145ae96\n")
        self.assertExecutes(one_checkout + one_checkout,
                            "kcidb.summarize_main", "checkouts",
                            stdout_re="c003f145ae96\nc003f145ae96\n")

    def test_describe_main(self):
        """Check kcidb-describe works"""
        self.assertExecutes('', "kcidb.describe_main", "checkouts")
        self.assertExecutes('{', "kcidb.describe_main", "checkouts",
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', "kcidb.describe_main", "checkouts",
                            status=1, stderr_re=".*ValidationError.*")

        empty = json.dumps(dict(version=dict(major=4, minor=0)))
        self.assertExecutes(empty, "kcidb.describe_main", "checkouts")
        self.assertExecutes(empty + empty, "kcidb.describe_main", "checkouts")

        git_commit_hash = "c003f145ae96b769858ee5501189c582a97c6742"
        one_checkout = json.dumps(dict(
            version=dict(major=4, minor=0),
            checkouts=[
                dict(id="test:1",
                     git_commit_hash=git_commit_hash,
                     origin="test")
            ]
        ))
        self.assertExecutes(one_checkout, "kcidb.describe_main", "checkouts",
                            stdout_re="Below is the summary.*\x00")
        self.assertExecutes(one_checkout + one_checkout,
                            "kcidb.describe_main", "checkouts",
                            stdout_re="Below .*\x00Below .*\x00")

    def test_merge_main(self):
        """Check kcidb-merge works"""
        empty = json.dumps(dict(version=dict(major=4, minor=0))) + "\n"

        self.assertExecutes('', "kcidb.merge_main", "--indent=0",
                            stdout_re=re.escape(empty))
        self.assertExecutes('{', "kcidb.merge_main",
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', "kcidb.merge_main",
                            status=1, stderr_re=".*ValidationError.*")
        self.assertExecutes(empty, "kcidb.merge_main", "--indent=0",
                            stdout_re=re.escape(empty))
        self.assertExecutes(empty + empty, "kcidb.merge_main", "--indent=0",
                            stdout_re=re.escape(empty))

        report_a = dict(
            version=dict(major=4, minor=0),
            checkouts=[
                dict(id="test:checkout:1", origin="test")
            ],
            builds=[
                dict(id="test:build:1", origin="text",
                     checkout_id="test:checkout:1")
            ],
            tests=[
                dict(id="test:test:1", origin="text", build_id="test:build:1")
            ]
        )

        report_b = dict(
            version=dict(major=4, minor=0),
            checkouts=[
                dict(id="test:checkout:1", origin="test")
            ],
            builds=[
                dict(id="test:build:2", origin="text",
                     checkout_id="test:checkout:1")
            ],
            tests=[
                dict(id="test:test:2", origin="text", build_id="test:build:2")
            ]
        )
        merged_report = dict(
            version=dict(major=4, minor=0),
            checkouts=report_a["checkouts"] + report_b["checkouts"],
            builds=report_a["builds"] + report_b["builds"],
            tests=report_a["tests"] + report_b["tests"],
        )
        self.assertExecutes(json.dumps(report_a) + json.dumps(report_b),
                            "kcidb.merge_main", "--indent=0",
                            stdout_re=re.escape(
                                json.dumps(merged_report) + "\n"
                            ))

    def test_notify_main(self):
        """Check kcidb-notify works"""
        self.assertExecutes('', "kcidb.notify_main")
        self.assertExecutes('{', "kcidb.notify_main",
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', "kcidb.notify_main",
                            status=1, stderr_re=".*ValidationError.*")

        empty = json.dumps(dict(version=dict(major=4, minor=0)))
        self.assertExecutes(empty, "kcidb.notify_main")
        self.assertExecutes(empty + empty, "kcidb.notify_main")

        git_commit_hash = "4ff6a2469104218a044ff595a0c1eb469ca7ea01"
        build_fail = json.dumps(dict(
            version=dict(major=4, minor=0),
            checkouts=[
                dict(id="test:checkout:1",
                     git_commit_hash=git_commit_hash,
                     origin="test")
            ],
            builds=[
                dict(id="test:build:1",
                     origin="test",
                     checkout_id="test:checkout:1",
                     valid=False)
            ]
        ))

        self.assertExecutes(build_fail, "kcidb.notify_main",
                            stdout_re="Subject: Test checkout: .*\x00"
                                      "Subject: Test build: .*\x00")
        self.assertExecutes(build_fail + build_fail, "kcidb.notify_main",
                            stdout_re="Subject: Test checkout: .*\x00"
                                      "Subject: Test build: .*\x00"
                                      "Subject: Test checkout: .*\x00"
                                      "Subject: Test build: .*\x00")
