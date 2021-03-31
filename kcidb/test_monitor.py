"""kcdib.monitor module tests"""

import unittest
from kcidb_io import schema
from kcidb import oo, monitor

# Disable long line checking for JSON data
# flake8: noqa
# pylint: disable=line-too-long


class MatchOOTestCase(unittest.TestCase):
    """kcidb.monitor.match_oo test case"""

    def setUp(self):
        """Setup tests"""
        # pylint: disable=invalid-name
        self.maxDiff = None
        self.version = dict(
            major=schema.LATEST.major,
            minor=schema.LATEST.minor
        )

    def test_min(self):
        """Check minimal matching"""

        oo_data = oo.from_io({
            "version": self.version,
            "checkouts": [
                {
                    "contacts": [
                        "rdma-dev-team@redhat.com"
                    ],
                    "start_time": "2020-03-02T15:16:15.790000+00:00",
                    "git_repository_branch": "wip/jgg-for-next",
                    "git_commit_hash": "5e29d1443c46b6ca70a4c940a67e8c09f05dcb7e",
                    "git_repository_url": "git://git.kernel.org/pub/scm/linux/kernel/git/rdma/rdma.git",
                    "misc": {
                        "pipeline_id": 467715
                    },
                    "id": "non_test:1",
                    "origin": "non_test",
                    "patchset_files": [],
                    "valid": True,
                },
                {
                    "contacts": [
                        "rdma-dev-team@redhat.com"
                    ],
                    "start_time": "2020-03-02T15:16:15.790000+00:00",
                    "git_repository_branch": "wip/jgg-for-next",
                    "git_commit_hash": "1254e88b4fc1470d152f494c3590bb6a33ab33eb",
                    "git_repository_url": "git://git.kernel.org/pub/scm/linux/kernel/git/rdma/rdma.git",
                    "misc": {
                        "pipeline_id": 467715
                    },
                    "id": "test:1",
                    "origin": "test",
                    "patchset_files": [],
                    "valid": True,
                },
            ],
            "builds": [
                {
                    "architecture": "aarch64",
                    "command": "make -j30 INSTALL_MOD_STRIP=1 targz-pkg",
                    "compiler": "aarch64-linux-gnu-gcc (GCC) 9.2.1 20190827 (Red Hat Cross 9.2.1-1)",
                    "config_name": "fedora",
                    "duration": 237.0,
                    "id": "non_test:1",
                    "origin": "non_test",
                    "input_files": [],
                    "log_url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/03/469720/build_aarch64.log",
                    "misc": {
                        "job_id": 678223,
                        "pipeline_id": 469720
                    },
                    "output_files": [],
                    "checkout_id": "test:1",
                    "start_time": "2020-03-03T17:52:02.370000+00:00",
                    "valid": True
                },
                {
                    "architecture": "aarch64",
                    "command": "make -j30 INSTALL_MOD_STRIP=1 targz-pkg",
                    "compiler": "aarch64-linux-gnu-gcc (GCC) 9.2.1 20190827 (Red Hat Cross 9.2.1-1)",
                    "config_name": "fedora",
                    "duration": 237.0,
                    "id": "test:1",
                    "origin": "test",
                    "input_files": [],
                    "log_url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/03/469720/build_aarch64.log",
                    "misc": {
                        "job_id": 678223,
                        "pipeline_id": 469720
                    },
                    "output_files": [],
                    "checkout_id": "test:1",
                    "start_time": "2020-03-03T17:52:02.370000+00:00",
                    "valid": True
                },
            ],
            "tests": [
                {
                    "build_id": "redhat:679936",
                    "comment": "IOMMU boot test",
                    "duration": 1847.0,
                    "id": "non_test:1",
                    "origin": "non_test",
                    "output_files": [
                        {
                            "name": "x86_64_4_console.log",
                            "url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/04/471145/x86_64_4_console.log"
                        },
                        {
                            "name": "x86_64_4_IOMMU_boot_test_dmesg.log",
                            "url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/04/471145/x86_64_4_IOMMU_boot_test_dmesg.log"
                        },
                        {
                            "name": "x86_64_4_IOMMU_boot_test_resultoutputfile.log",
                            "url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/04/471145/x86_64_4_IOMMU_boot_test_resultoutputfile.log"
                        },
                        {
                            "name": "x86_64_4_IOMMU_boot_test_taskout.log",
                            "url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/04/471145/x86_64_4_IOMMU_boot_test_taskout.log"
                        }
                    ],
                    "environment": {
                        "comment": "meson-gxl-s905d-p230 in lab-baylibre",
                        "misc": {
                            "device": "meson-gxl-s905d-p230",
                            "instance": "meson-gxl-s905d-p230-sea",
                            "lab": "lab-baylibre",
                            "mach": "amlogic",
                            "rootfs_url": "https://storage.kernelci.org/images/rootfs/buildroot/kci-2019.02-9-g25091c539382/arm64/baseline/rootfs.cpio.gz"
                        }
                    },
                    "path": "redhat_iommu_boot",
                    "start_time": "2020-03-04T21:30:57+00:00",
                    "status": "ERROR",
                    "waived": True
                },
                {
                    "build_id": "redhat:679936",
                    "comment": "IOMMU boot test",
                    "duration": 1847.0,
                    "id": "test:1",
                    "origin": "test",
                    "output_files": [
                        {
                            "name": "x86_64_4_console.log",
                            "url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/04/471145/x86_64_4_console.log"
                        },
                        {
                            "name": "x86_64_4_IOMMU_boot_test_dmesg.log",
                            "url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/04/471145/x86_64_4_IOMMU_boot_test_dmesg.log"
                        },
                        {
                            "name": "x86_64_4_IOMMU_boot_test_resultoutputfile.log",
                            "url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/04/471145/x86_64_4_IOMMU_boot_test_resultoutputfile.log"
                        },
                        {
                            "name": "x86_64_4_IOMMU_boot_test_taskout.log",
                            "url": "https://cki-artifacts.s3.amazonaws.com/datawarehouse/2020/03/04/471145/x86_64_4_IOMMU_boot_test_taskout.log"
                        }
                    ],
                    "environment": {
                        "comment": "meson-gxl-s905d-p230 in lab-baylibre",
                        "misc": {
                            "device": "meson-gxl-s905d-p230",
                            "instance": "meson-gxl-s905d-p230-sea",
                            "lab": "lab-baylibre",
                            "mach": "amlogic",
                            "rootfs_url": "https://storage.kernelci.org/images/rootfs/buildroot/kci-2019.02-9-g25091c539382/arm64/baseline/rootfs.cpio.gz"
                        }
                    },
                    "path": "redhat_iommu_boot",
                    "start_time": "2020-03-04T21:30:57+00:00",
                    "status": "ERROR",
                    "waived": True
                },
            ],
        })

        notifications = monitor.match_oo(oo_data)
        self.assertEqual(len(notifications), 3)
        for notification in notifications:
            obj_list_name = notification.obj_list_name
            assert obj_list_name.endswith("s")
            obj_name = obj_list_name[:-1]
            self.assertIsInstance(notification, monitor.output.Notification)
            message = notification.render()
            self.assertIsNone(message['From'])
            self.assertEqual(message['To'], "test@kernelci.org")
            self.assertEqual(message['X-KCIDB-Notification-Message-ID'],
                             obj_name)
            self.assertIn(f"Test {obj_name}: ", message['Subject'])
            self.assertIn(f"Test {obj_name} detected!\n\n",
                          message.get_payload())
