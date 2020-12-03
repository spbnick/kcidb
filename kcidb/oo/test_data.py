"""kcdib.oo.data module tests"""

import kcidb


class KCIDBOODataRequest(kcidb.unittest.TestCase):
    """Test case for the Request class"""

    def test_parse(self):
        """Check request parsing works"""
        schema = kcidb.oo.data.Schema(dict(
            revision=dict(
                json_schema=dict(type="object"),
                id_fields=("git_commit_hash", "patchset_hash"),
                children=dict(
                    checkout=("git_commit_hash", "patchset_hash",)
                ),
            ),
            checkout=dict(
                json_schema=dict(type="object"),
                id_fields=("id",),
                children=dict(
                    build=("checkout_id",)
                ),
            ),
            build=dict(
                json_schema=dict(type="object"),
                id_fields=("id",),
                children=dict(
                    test=("build_id",),
                    build_test_environment=("build_id",)
                ),
            ),
            test_environment=dict(
                json_schema=dict(type="object"),
                id_fields=("id",),
                children=dict(
                    test=("environment_id",),
                    build_test_environment=("environment_id",),
                ),
            ),
            build_test_environment=dict(
                json_schema=dict(type="object"),
                id_fields=("build_id", "environment_id"),
                children=dict(
                    test=("build_id", "environment_id"),
                ),
            ),
            test=dict(
                json_schema=dict(type="object"),
                id_fields=("id",),
            ),
        ))

        def parse(string, obj_id_list_list=None):
            return kcidb.oo.data.Request.parse(string, obj_id_list_list,
                                               schema=schema)

        def request(base, child, obj_type_name, obj_id_list, load):
            return kcidb.oo.data.Request(base, child,
                                         schema.types[obj_type_name],
                                         obj_id_list, load)

        self.assertEqual(parse(""), [])
        self.assertEqual(parse("<*"), [])
        self.assertEqual(parse(">revision"),
                         [request(None, True, "revision", None, False)])
        self.assertEqual(parse(">checkout"),
                         [request(None, True, "checkout", None, False)])
        self.assertEqual(parse(">build"),
                         [request(None, True, "build", None, False)])
        self.assertEqual(parse(">build_test_environment"),
                         [request(None, True, "build_test_environment",
                                  None, False)])
        self.assertEqual(parse(">test_environment"),
                         [request(None, True, "test_environment",
                                  None, False)])
        self.assertEqual(parse(">test"),
                         [request(None, True, "test", None, False)])
        self.assertEqual(parse(">revision#"),
                         [request(None, True, "revision", None, True)])
        self.assertEqual(parse(">revision$"),
                         [request(None, True, "revision", None, True)])
        self.assertEqual(parse(">revision%", [[("abc", "def")]]),
                         [request(None, True, "revision",
                                  [("abc", "def")], False)])
        self.assertEqual(
            parse(">revision%>checkout>build#", [[("abc", "def")]]),
            [request(
                request(
                    request(None, True, "revision", [("abc", "def")], False),
                    True, "checkout", None, False
                ),
                True, "build", None, True
            )])
        self.assertEqual(
            parse(">revision%>checkout%>build#",
                  [[("abc", "def")], [("123",)]]),
            [request(
                request(
                    request(None, True, "revision", [("abc", "def")], False),
                    True, "checkout", [("123",)], False
                ),
                True, "build", None, True
            )])
        self.assertEqual(
            parse(">build>*#"),
            [
                request(
                    request(None, True, "build", None, False),
                    True, "test", None, True
                ),
                request(
                    request(
                        request(None, True, "build", None, False),
                        True, "build_test_environment", None, True
                    ),
                    True, "test", None, True
                )
            ]
        )
        self.assertEqual(
            parse(">build%<*$", [[("abc",)]]),
            [
                request(
                    request(
                        request(None, True, "build", [("abc",)], False),
                        False, "checkout", None, False
                    ),
                    False, "revision", None, True
                )
            ]
        )

        build_to_build_request = \
            request(
                request(
                    request(
                        request(
                            request(None, True, "build", [("abc",)], False),
                            False, "checkout", None, False
                        ),
                        False, "revision", None, True
                    ),
                    True, "checkout", None, True
                ),
                True, "build", None, True
            )
        self.assertEqual(
            parse(">build%<*$>*#", [[("abc",)]]),
            [
                request(
                    build_to_build_request,
                    True, "test", None, True
                ),
                request(
                    request(
                        build_to_build_request,
                        True, "build_test_environment", None, True
                    ),
                    True, "test", None, True
                ),
            ]
        )

        self.assertEqual(parse(">revision[abc,def]"),
                         [request(None, True, "revision",
                                  [("abc", "def")], False)])
        self.assertEqual(parse(">checkout[123]"),
                         [request(None, True, "checkout",
                                  [("123",)], False)])
        self.assertEqual(
            parse(">revision[abc, def]>checkout[123]>build#"),
            [request(
                request(
                    request(None, True, "revision", [("abc", "def")], False),
                    True, "checkout", [("123",)], False
                ),
                True, "build", None, True
            )])
        self.assertEqual(parse(">revision[abc,def; ghi, jkl]"),
                         [request(None, True, "revision",
                                  [("abc", "def"), ("ghi", "jkl")], False)])
        self.assertEqual(parse('>checkout["123"]'),
                         [request(None, True, "checkout",
                                  [("123",)], False)])
        self.assertEqual(parse('>checkout["1 2 3"]'),
                         [request(None, True, "checkout",
                                  [("1 2 3",)], False)])
        self.assertEqual(parse('>checkout["1,2;3"]'),
                         [request(None, True, "checkout",
                                  [("1,2;3",)], False)])
        self.assertEqual(parse('>checkout["1\\"2\\"3"]'),
                         [request(None, True, "checkout",
                                  [("1\"2\"3",)], False)])
        self.assertEqual(parse('>checkout["1\\\\2\\\\3"]'),
                         [request(None, True, "checkout",
                                  [("1\\2\\3",)], False)])
        self.assertEqual(parse('>revision["abc","def"; "ghi", "jkl"]'),
                         [request(None, True, "revision",
                                  [("abc", "def"), ("ghi", "jkl")], False)])
        self.assertEqual(
            parse(' > revision [ "abc" , "def" ; "ghi" , "jkl" ] '),
            [request(None, True, "revision",
                     [("abc", "def"), ("ghi", "jkl")], False)]
        )
