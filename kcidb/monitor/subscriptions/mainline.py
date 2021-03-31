"""Mainline tree subscriptions"""

from kcidb.monitor.output import NotificationMessage as Message

REPO_URL = \
    "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
RECIPIENTS = ["Linux Kernel Mailing List <linux-kernel@vger.kernel.org>"]


def match_revision(revision):
    """Match revisions of interest to stable tree developers"""
    if REPO_URL not in revision.repo_branch_checkouts:
        return ()
    if not revision.builds_valid:
        return (Message(RECIPIENTS, "Builds failed for "),)
    for test in revision.tests:
        # Ignore syzbot until we have issues/incidents
        if test.origin == "syzbot":
            continue
        if test.status == "FAIL" and not test.waived:
            return (Message(RECIPIENTS, "Tests failed for "),)
    return ()
