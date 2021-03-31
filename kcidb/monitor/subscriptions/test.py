"""Test subscription"""

from kcidb.monitor.output import NotificationMessage as Message


def match_revision(revision):
    """Match test revisions"""
    for checkout in revision.checkouts:
        if checkout.origin == "test":
            return (
                Message(["test@kernelci.org"],
                        "Test revision: ",
                        "Test revision detected!\n\n",
                        "revision"),
            )
    return ()


def match_checkout(checkout):
    """Match test checkouts"""
    if checkout.origin == "test":
        return (
            Message(["test@kernelci.org"],
                    "Test checkout: ",
                    "Test checkout detected!\n\n",
                    "checkout"),
        )
    return ()


def match_build(build):
    """Match test builds"""
    if build.origin == "test":
        return (
            Message(["test@kernelci.org"],
                    "Test build: ",
                    "Test build detected!\n\n",
                    "build"),
        )
    return ()


def match_test(test):
    """Match test tests"""
    if test.origin == "test":
        return (
            Message(["test@kernelci.org"],
                    "Test test: ",
                    "Test test detected!\n\n",
                    "test"),
        )
    return ()
