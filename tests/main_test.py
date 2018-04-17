from __future__ import absolute_import

import mock
import pytest

from detect_secrets_server.__main__ import main


class TestMain(object):

    def test_main_no_args(self):
        with pytest.raises(SystemExit):
            main([])

    def test_main_no_actions(self):
        argument_string = (
            '--s3-config examples/s3.yaml'
        )
        assert main(argument_string.split()) == 0

    @pytest.mark.parametrize(
        'argument_string,action_executed',
        [
            (
                '--initialize examples/repos.yaml '
                '--output-hook pysensu '
                '--output-config examples/pysensu.config.yaml '
                '--s3-config examples/s3.yaml',
                'initialize',
            ),
            (
                '--add-repo git@github.com:yelp/detect-secrets '
                '--s3-credentials-file examples/aws_credentials.json '
                '--s3-bucket pail',
                'add_repo',
            ),
            (
                '--scan-repo yelp/detect-secrets '
                '--output-hook examples/standalone_hook.py '
                '--s3-config examples/s3.yaml',
                'scan_repo',
            ),
        ]
    )
    def test_actions(self, argument_string, action_executed):
        """All detailed actions tests are covered in their individual
        test cases. This just makes sure they run, for coverage.
        """
        with mock.patch(
            'detect_secrets_server.__main__.actions',
            autospec=True,
        ) as mock_actions:
            mock_actions.initialize.return_value = ''
            mock_actions.scan_repo.return_value = 0

            assert main(argument_string.split()) == 0
            assert getattr(mock_actions, action_executed).called
