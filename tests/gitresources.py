import os.path
import sys
from typing import Union

import dulwich.repo
import dulwich.porcelain
import dulwich.client
import dulwich.index

from dulwich import porcelain
from dulwich.file import ensure_dir_exists
from dulwich.object_store import iter_tree_contents

from dulwich.objects import TreeEntry, Tree
from dulwich.refs import LOCAL_BRANCH_PREFIX
from dulwich.objectspec import parse_tree, to_bytes
from dulwich.porcelain import update_head

LOCAL_REMOTE_PREFIX = b"refs/remotes/"

here = os.path.abspath(os.path.dirname(__file__))


def setup_resources():
    url = "https://github.com/hsorby/sparc-dataset-curation-test-resources.git"
    environment_location = os.environ.get("SPARC_DATASET_CURATION_TEST_RESOURCES", "<not-set>")
    default_resources_path = os.path.join(here, "resources")
    readme_file = os.path.join(default_resources_path, "README.rst")
    if os.path.isfile(os.path.join(environment_location, "README.rst")):
        repo = dulwich.repo.Repo(environment_location, bare=False)
    elif os.path.isfile(readme_file):
        repo = dulwich.repo.Repo(default_resources_path, bare=False)
    else:
        repo = dulwich.porcelain.clone(url, os.path.join(here, "resources"))
        if not os.path.isfile(readme_file):
            sys.exit(1)

    return repo


def dulwich_checkout(repo, target):
    checkout_branch(repo, target)


def dulwich_proper_stash_and_drop(repo):
    dulwich.porcelain.stash_push(repo)
    for e in dulwich.porcelain.stash_list(repo):
        dulwich.porcelain.reset(repo, "hard", e[1].old_sha)
    dulwich.porcelain.stash_drop(repo, 0)


class CheckoutError(Exception):
    """Indicates that the working directory is not clean while trying to checkout."""


def _update_head_during_checkout_branch(repo, target):
    checkout_target = None
    if target == b'HEAD':  # Do not update head while trying to checkout to HEAD.
        pass
    elif target in repo.refs.keys(base=LOCAL_BRANCH_PREFIX):
        update_head(repo, target)
    else:
        # If checking out a remote branch, create a local one without the remote name prefix.
        config = repo.get_config()
        name = target.split(b"/")[0]
        section = (b"remote", name)
        if config.has_section(section):
            checkout_target = target.replace(name + b"/", b"")
            try:
                porcelain.branch_create(repo, checkout_target, (LOCAL_REMOTE_PREFIX + target).decode())
            except porcelain.Error:
                pass
            update_head(repo, LOCAL_BRANCH_PREFIX + checkout_target)
        else:
            update_head(repo, target, detached=True)

    return checkout_target


def checkout_branch(repo, target: Union[bytes, str], force: bool = False):
    """switch branches or restore working tree files.
    The implementation of this function will probably not scale well
    for branches with lots of local changes.
    This is due to the analysis of a diff between branches before any
    changes are applied.
    Args:
      repo: dulwich Repo object
      target: branch name or commit sha to checkout
      force: true or not to force checkout
    """
    target = to_bytes(target)

    current_tree = parse_tree(repo, repo.head())
    target_tree = parse_tree(repo, target)

    if force:
        repo.reset_index(target_tree.id)
        _update_head_during_checkout_branch(repo, target)
    else:
        status_report = porcelain.status(repo)
        changes = list(set(status_report[0]['add'] + status_report[0]['delete'] + status_report[0]['modify'] + status_report[1]))
        index = 0
        while index < len(changes):
            change = changes[index]
            if sys.platform == "win32" and change == b'derivative/Scaffold/mouseColon_view.json':
                # Can't explain this, just employing a workaround until it can be dealt with properly.
                changes.pop(index)
                continue
            try:
                current_tree.lookup_path(repo.object_store.__getitem__, change)
                try:
                    target_tree.lookup_path(repo.object_store.__getitem__, change)
                    index += 1
                except KeyError:
                    raise CheckoutError('Your local changes to the following files would be overwritten by checkout: ' + change.decode())
            except KeyError:
                changes.pop(index)

        # Update head.
        checkout_target = _update_head_during_checkout_branch(repo, target)
        if checkout_target is not None:
            target_tree = parse_tree(repo, checkout_target)

        dealt_with = set()
        repo_index = repo.open_index()
        for entry in iter_tree_contents(repo.object_store, target_tree.id):
            dealt_with.add(entry.path)
            if entry.path in changes:
                continue
            full_path = os.path.join(os.fsencode(repo.path), entry.path)
            blob = repo.object_store[entry.sha]
            ensure_dir_exists(os.path.dirname(full_path))
            st = porcelain.build_file_from_blob(blob, entry.mode, full_path)
            repo_index[entry.path] = dulwich.index.index_entry_from_stat(st, entry.sha, 0)

        repo_index.write()

        for entry in iter_tree_contents(repo.object_store, current_tree.id):
            if entry.path not in dealt_with:
                repo.unstage([entry.path])

    # Remove the untracked files which are in the current_file_set.
    repo_index = repo.open_index()
    for change in repo_index.changes_from_tree(repo.object_store, current_tree.id):
        path_change = change[0]
        if path_change[1] is None:
            file_name = path_change[0]
            full_path = os.path.join(repo.path, file_name.decode())
            if os.path.isfile(full_path):
                os.remove(full_path)
            dir_path = os.path.dirname(full_path)
            while dir_path != repo.path:
                is_empty = len(os.listdir(dir_path)) == 0
                if is_empty:
                    os.rmdir(dir_path)
                dir_path = os.path.dirname(dir_path)
