from __future__ import absolute_import
from __future__ import print_function

import sys

from detect_secrets.core.log import log

from detect_secrets_server import actions
from detect_secrets_server.core.usage.parser import ServerParserBuilder


def parse_args(argv):
    return ServerParserBuilder().parse_args(argv)


def main(argv=None):
    """
    Expected Usage:
      1. Initialize TrackedRepos from config.yaml, and save to crontab.
      2. Each cron command will run and scan git diff from previous commit saved, to now.
      3. If something is found, alert.

    :return: shell error code
    """
    if len(sys.argv) == 1:  # pragma: no cover
        sys.argv.append('-h')

    args = parse_args(argv)
    if args.verbose:    # pragma: no cover
        log.set_debug_level(args.verbose)

    print(args)
    return
    if args.action == 'add':
        if isinstance(args.repo, dict):
            output = actions.initialize(args)
            if output:
                print(output)
        else:
            actions.add_repo(args)

    elif args.action == 'scan':
        return actions.scan_repo(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
