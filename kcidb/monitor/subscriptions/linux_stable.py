"""Stable tree subscriptions"""

from kcidb.monitor.output import NotificationMessage as Message

REPO_URL_BASE = "https://git.kernel.org/pub/scm/linux/kernel/git"
REPO_URL_SET = {
    REPO_URL_BASE + suffix for suffix in [
        "/stable/linux-stable-rc.git",
        "/stable/linux-stable.git",
        "/sashal/linux-stable.git",
        "/stable/stable-queue.git",
    ]
}
RECIPIENTS = ["Linux Stable maillist <stable@vger.kernel.org>"]


def match_revision(revision):
    """Match revisions of interest to stable tree developers"""
    if not set(revision.repo_branch_checkouts) & REPO_URL_SET:
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
