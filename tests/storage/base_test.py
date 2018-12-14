from __future__ import absolute_import

import os
import subprocess
from contextlib import contextmanager

import mock
import pytest

from detect_secrets_server.storage.base import BaseStorage
from detect_secrets_server.storage.base import get_filepath_safe
from detect_secrets_server.storage.base import LocalGitRepository
from testing.mocks import mock_git_calls
from testing.mocks import SubprocessMock


class TestBaseStorage(object):

    def logic(self):
        return BaseStorage(
            os.path.expanduser('~/.detect-secrets-server'),
        )

    def test_setup_creates_directories(self):
        with assert_directories_created([
            '~/.detect-secrets-server',
            '~/.detect-secrets-server/repos',
        ]):
            self.logic().setup('git@github.com:yelp/detect-secrets')

    @pytest.mark.parametrize(
        'repo,name',
        [
            (
                'git@github.com:yelp/detect-secrets',
                'yelp/detect-secrets',
            ),

            # Ends with .git
            (
                'git@github.com:yelp/detect-secrets.git',
                'yelp/detect-secrets',
            ),
        ],
    )
    def test_repository_name(self, repo, name):
        with assert_directories_created():
            assert self.logic().setup(repo).repository_name == name

    def test_baseline_file_does_not_exist(self):
        """This also conveniently tests our _git function"""
        with assert_directories_created():
            repo = self.logic().setup('git@github.com:yelp/detect-secrets')

        with pytest.raises(subprocess.CalledProcessError):
            repo.get_baseline_file('does_not_exist')

    def test_clone_repo_if_exists(self):
        with assert_directories_created():
            repo = self.logic().setup('git@github.com:yelp/detect-secrets')

        with mock_git_calls(
            self.construct_subprocess_mock_git_clone(
                repo,
                b'fatal: destination path \'blah\' already exists',
            ),
            SubprocessMock(
                expected_input='git pull',
            ),
        ):
            repo.clone_and_pull_master()

    def test_clone_repo_something_else_went_wrong(self):
        with assert_directories_created():
            repo = self.logic().setup('git@github.com:yelp/detect-secrets')

        with mock_git_calls(
            self.construct_subprocess_mock_git_clone(
                repo,
                b'Some other error message, not expected',
            )
        ), pytest.raises(
            subprocess.CalledProcessError
        ):
            repo.clone_and_pull_master()

    @staticmethod
    def construct_subprocess_mock_git_clone(repo, mocked_output):
        return SubprocessMock(
            expected_input=(
                'git clone git@github.com:yelp/detect-secrets {} --bare'.format(
                    os.path.expanduser(
                        '~/.detect-secrets-server/repos/{}'.format(
                            repo.hash_filename('yelp/detect-secrets')
                        )
                    ),
                )
            ),
            mocked_output=mocked_output,
            should_throw_exception=True,
        )


class TestLocalGitRepository(object):

    def logic(self):
        return LocalGitRepository(
            os.path.expanduser('~/.detect-secrets-server'),
        )

    @pytest.mark.parametrize(
        'repo,name',
        [
            (
                '/file/to/yelp/detect-secrets',
                'yelp/detect-secrets',
            ),
            (
                '/file/to/yelp/detect-secrets/.git',
                'yelp/detect-secrets',
            ),
        ]
    )
    def test_name(self, repo, name):
        """OK, I admit this is kinda a lame test case, because technically
        everything is mocked out. However, it's needed for coverage, and
        it *does* test things (kinda).
        """
        with mock_git_calls(
            SubprocessMock(
                expected_input='git remote get-url origin',
                mocked_output='git@github.com:yelp/detect-secrets',
            ),
        ), assert_directories_created():
            assert self.logic().setup(repo).repository_name == name

    def test_clone_and_pull_master(self):
        # We're asserting that nothing is run in this case.
        with mock_git_calls(), assert_directories_created():
            self.logic().setup('git@github.com:yelp/detect-secrets')\
                .clone_and_pull_master()


class TestGetFilepathSafe(object):

    @pytest.mark.parametrize(
        'prefix,filename,expected',
        [
            ('/path/to', 'file', '/path/to/file',),
            ('/path/to', '../to/file', '/path/to/file',),
            ('/path/to/../to', 'file', '/path/to/file',),
        ]
    )
    def test_success(self, prefix, filename, expected):
        assert get_filepath_safe(prefix, filename) == expected

    def test_failure(self):
        with pytest.raises(ValueError):
            get_filepath_safe('/path/to', '../../etc/pwd')


@contextmanager
def assert_directories_created(directories_created=None):
    """
    :type directories_created: list
    """
    with mock.patch(
        'detect_secrets_server.storage.base.os.makedirs'
    ) as makedirs, mock.patch(
        'detect_secrets_server.storage.base.os.path.isdir',
        return_value=False,
    ):
        yield

        if directories_created:
            makedirs.assert_has_calls(map(
                lambda x: mock.call(os.path.expanduser(x)),
                directories_created,
            ))
        else:
            assert makedirs.called
