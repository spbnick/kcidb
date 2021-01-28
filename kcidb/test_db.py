"""kcdib.db module tests"""

import re
import textwrap
import json
from unittest.mock import Mock, patch
import kcidb_io
import kcidb


class KCIDBDBMainFunctionsTestCase(kcidb.unittest.TestCase):
    """Test case for main functions"""

    def test_init_main(self):
        """Check kcidb-db-init works"""
        argv = ["kcidb.db.init_main", "-d", "bigquery:project.dataset"]
        driver_source = textwrap.dedent("""
            from unittest.mock import patch, Mock
            client = Mock()
            client.init = Mock()
            client.is_initialized = Mock(return_value=False)
            with patch("kcidb.db.Client", return_value=client) as \
                    Client:
                status = function()
            Client.assert_called_once_with("bigquery:project.dataset")
            client.init.assert_called_once()
            return status
        """)
        self.assertExecutes("", *argv, driver_source=driver_source)

    def test_cleanup_main(self):
        """Check kcidb-db-cleanup works"""
        argv = ["kcidb.db.cleanup_main", "-d", "bigquery:project.dataset"]
        driver_source = textwrap.dedent("""
            from unittest.mock import patch, Mock
            client = Mock()
            client.cleanup = Mock()
            client.is_initialized = Mock(return_value=True)
            with patch("kcidb.db.Client", return_value=client) as \
                    Client:
                status = function()
            Client.assert_called_once_with("bigquery:project.dataset")
            client.cleanup.assert_called_once()
            return status
        """)
        self.assertExecutes("", *argv, driver_source=driver_source)

    def test_dump_main(self):
        """Check kcidb-db-dump works"""
        empty = kcidb_io.new()
        argv = ["kcidb.db.dump_main", "-d", "bigquery:project.dataset",
                "--indent=0"]

        driver_source = textwrap.dedent(f"""
            from unittest.mock import patch, Mock
            client = Mock()
            client.dump_iter = Mock(return_value=iter(({repr(empty)},)))
            with patch("kcidb.db.Client", return_value=client) as \
                    Client:
                status = function()
            Client.assert_called_once_with("bigquery:project.dataset")
            client.dump_iter.assert_called_once()
            return status
        """)
        self.assertExecutes("", *argv, driver_source=driver_source,
                            stdout_re=re.escape(json.dumps(empty) + "\n"))

        driver_source = textwrap.dedent(f"""
            from unittest.mock import patch, Mock
            client = Mock()
            client.dump_iter = Mock(return_value=iter({repr((empty, empty))}))
            with patch("kcidb.db.Client", return_value=client) as \
                    Client:
                status = function()
            Client.assert_called_once_with("bigquery:project.dataset")
            client.dump_iter.assert_called_once()
            return status
        """)
        self.assertExecutes("", *argv, driver_source=driver_source,
                            stdout_re=re.escape(json.dumps(empty) + "\n" +
                                                json.dumps(empty) + "\n"))

    def test_query_main(self):
        """Check kcidb-db-query works"""
        driver_source = textwrap.dedent("""
            from unittest.mock import patch
            with patch("kcidb.db.Client"):
                return function()
        """)
        argv = ["kcidb.db.query_main", "-d", "bigquery:project.dataset"]
        self.assertExecutes("", *argv, driver_source=driver_source)

        argv = [
            "kcidb.db.query_main", "-d", "bigquery:project.dataset",
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
            with patch("kcidb.db.Client", return_value=client) as Client:
                status = function()
            Client.assert_called_once_with("bigquery:project.dataset")
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

    def test_load_main(self):
        """Check kcidb-db-load works"""
        driver_source = textwrap.dedent("""
            from unittest.mock import patch
            with patch("kcidb.db.Client"):
                return function()
        """)
        argv = ["kcidb.db.load_main", "-d", "bigquery:project.dataset"]

        self.assertExecutes("", *argv, driver_source=driver_source)
        self.assertExecutes('{', *argv, driver_source=driver_source,
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', *argv, driver_source=driver_source,
                            status=1, stderr_re=".*ValidationError.*")

        empty = kcidb_io.new()

        driver_source = textwrap.dedent(f"""
            from unittest.mock import patch, Mock
            client = Mock()
            client.load = Mock()
            with patch("kcidb.db.Client", return_value=client) as Client:
                status = function()
            Client.assert_called_once_with("bigquery:project.dataset")
            client.load.assert_called_once_with({repr(empty)})
            return status
        """)
        self.assertExecutes(json.dumps(empty), *argv,
                            driver_source=driver_source)

        driver_source = textwrap.dedent(f"""
            from unittest.mock import patch, Mock, call
            client = Mock()
            client.load = Mock()
            with patch("kcidb.db.Client", return_value=client) as Client:
                status = function()
            Client.assert_called_once_with("bigquery:project.dataset")
            assert client.load.call_count == 2
            client.load.assert_has_calls([call({repr(empty)}),
                                          call({repr(empty)})])
            return status
        """)
        self.assertExecutes(json.dumps(empty) + json.dumps(empty), *argv,
                            driver_source=driver_source)

    def test_complement_main(self):
        """Check kcidb-db-complement works"""
        driver_source = textwrap.dedent("""
            from unittest.mock import patch
            with patch("kcidb.db.Client"):
                return function()
        """)
        argv = ["kcidb.db.complement_main", "-d", "bigquery:project.dataset",
                "--indent=0"]

        self.assertExecutes("", *argv, driver_source=driver_source)
        self.assertExecutes('{', *argv, driver_source=driver_source,
                            status=1, stderr_re=".*JSONParseError.*")
        self.assertExecutes('{}', *argv, driver_source=driver_source,
                            status=1, stderr_re=".*ValidationError.*")

        report_a = {**kcidb_io.new(),
                    "checkouts": [dict(id="test:checkout:1", origin="test")]}
        report_b = {**kcidb_io.new(),
                    "checkouts": [dict(id="test:checkout:2", origin="test")]}

        driver_source = textwrap.dedent(f"""
            from unittest.mock import patch, Mock
            client = Mock()
            client.complement = Mock(return_value={repr(report_b)})
            with patch("kcidb.db.Client", return_value=client) as Client:
                status = function()
            Client.assert_called_once_with("bigquery:project.dataset")
            client.complement.assert_called_once_with({repr(report_a)})
            return status
        """)
        self.assertExecutes(json.dumps(report_a), *argv,
                            driver_source=driver_source,
                            stdout_re=re.escape(json.dumps(report_b) + "\n"))

        driver_source = textwrap.dedent(f"""
            from unittest.mock import patch, Mock, call
            client = Mock()
            client.complement = Mock(side_effect={repr((report_b, report_a))})
            with patch("kcidb.db.Client", return_value=client) as Client:
                status = function()
            Client.assert_called_once_with("bigquery:project.dataset")
            assert client.complement.call_count == 2
            client.complement.assert_has_calls([call({repr(report_a)}),
                                                call({repr(report_b)})])
            return status
        """)
        self.assertExecutes(json.dumps(report_a) + json.dumps(report_b), *argv,
                            driver_source=driver_source,
                            stdout_re=re.escape(json.dumps(report_b) + "\n" +
                                                json.dumps(report_a) + "\n"))


class KCIDBDBClient(kcidb.unittest.TestCase):
    """Test case for the Client class"""

    def test_load(self):
        """Check all possible I/O fields can be loaded"""
        # Calm down, pylint: disable=no-self-use
        io_data = {
            **kcidb_io.new(),
            "checkouts": [
                dict(
                    id="origin:1",
                    origin="origin",
                    tree_name="mainline",
                    git_repository_url="https://git.kernel.org/pub/scm/"
                                       "linux/kernel/git/torvalds/linux.git",
                    git_commit_hash="ef2b753c38bc9c0d1eea84e29a6bb6f9e776d0e3",
                    git_commit_name="v5.8-rc7-98-g7dc6fd0f3b84",
                    git_repository_branch="master",
                    patchset_files=[
                        dict(name="0001.patch",
                             url="https://example.com/0001.patch"),
                        dict(name="0002.patch",
                             url="https://example.com/0002.patch"),
                    ],
                    patchset_hash="903638c087335b10293663c682b9aa00"
                                  "76f9f7be478a8e7828bc22e12d301b42",
                    message_id="5f9fccd2.1c69fb81.1b2f.6d9c@mx.google.com",
                    comment="v5.8",
                    publishing_time="2020-08-14T23:08:06.967000+00:00",
                    start_time="2020-08-14T23:08:06.967000+00:00",
                    contacts=[
                        "clang-built-linux@googlegroups.com",
                        "stable@vger.kernel.org"
                    ],
                    log_url="https://example.com/checkout.log",
                    log_excerpt="error: patch failed: "
                                "arch/arm64/boot/dts/qcom/sc7180.dtsi:510\n"
                                "error: arch/arm64/boot/dts/qcom/sc7180.dtsi:"
                                " patch does not apply\n",
                    valid=True,
                    misc=dict(
                        foo="bar",
                        baz=42
                    ),
                ),
            ],
            "builds": [
                dict(
                    checkout_id="origin:1",
                    id="origin:1",
                    origin="origin",
                    comment="x86_64",
                    start_time="2020-08-14T23:08:06.967000+00:00",
                    duration=600,
                    architecture="x86_64",
                    command="make",
                    compiler="gcc",
                    input_files=[
                        dict(name="foo.bar",
                             url="https://example.com/foo.bar"),
                        dict(name="bar.foo",
                             url="https://example.com/bar.foo"),
                    ],
                    output_files=[
                        dict(name="foo.bar",
                             url="https://example.com/foo.bar"),
                        dict(name="bar.foo",
                             url="https://example.com/bar.foo"),
                    ],
                    config_name="fedora",
                    config_url="https://example.com/fedora.config",
                    log_url="https://example.com/build.log",
                    log_excerpt="error: invalid input constraint 'rZ'\n",
                    valid=True,
                    misc=dict(
                        foo="bar",
                        baz=42
                    ),
                ),
            ],
            "tests": [
                dict(
                    build_id="origin:1",
                    id="origin:1",
                    origin="origin",
                    environment=dict(
                        comment="Lenovo x230",
                        misc=dict(
                            foo="bar",
                            baz=42
                        ),
                    ),
                    path="ltp",
                    comment="ltp on Lenovo x230",
                    status="PASS",
                    waived=False,
                    start_time="2020-08-14T23:08:07.967000+00:00",
                    duration=600,
                    output_files=[
                        dict(name="foo.bar",
                             url="https://example.com/foo.bar"),
                        dict(name="bar.foo",
                             url="https://example.com/bar.foo"),
                    ],
                    misc=dict(
                        foo="bar",
                        baz=42
                    ),
                ),
            ]
        }
        dataset = Mock()
        dataset.labels = dict(version_major=io_data['version']['major'],
                              version_minor=io_data['version']['minor'])
        client = Mock()
        client.get_dataset = Mock(return_value=dataset)
        with patch("google.cloud.bigquery.Client", return_value=client), \
             patch("google.cloud.bigquery.job.LoadJobConfig"):
            client = kcidb.db.Client("bigquery:dataset")
            client.load(io_data)
