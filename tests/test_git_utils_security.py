import subprocess

from app import git_utils


def _make_repo_with_commit(tmp_path):
    bare = tmp_path / "repo.git"
    git_utils.init_bare_repo(bare)
    work = tmp_path / "work"
    subprocess.run(["git", "clone", str(bare), str(work)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", "a@a.com"], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", "a"], check=True)
    (work / "file.txt").write_text("hello\n")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "c1"], check=True)
    subprocess.run(["git", "-C", str(work), "push", "origin", "HEAD:main"], check=True, capture_output=True)
    return bare


def _malicious_ref(tmp_path, name):
    """A revision string crafted to look like a git CLI option instead of a
    ref, targeting a file outside the repo to prove no injection occurs."""
    return f"--output={tmp_path / name}"


def test_log_rejects_option_like_ref(tmp_path):
    bare = _make_repo_with_commit(tmp_path)
    try:
        git_utils.log(bare, ref=_malicious_ref(tmp_path, "pwned_log.txt"))
    except git_utils.GitError:
        pass
    assert not (tmp_path / "pwned_log.txt").exists()


def test_show_commit_rejects_option_like_sha(tmp_path):
    bare = _make_repo_with_commit(tmp_path)
    try:
        git_utils.show_commit(bare, _malicious_ref(tmp_path, "pwned_show.txt"))
    except git_utils.GitError:
        pass
    assert not (tmp_path / "pwned_show.txt").exists()


def test_read_file_rejects_option_like_ref(tmp_path):
    bare = _make_repo_with_commit(tmp_path)
    try:
        git_utils.read_file(bare, _malicious_ref(tmp_path, "pwned_read.txt"), "file.txt")
    except git_utils.GitError:
        pass
    assert not (tmp_path / "pwned_read.txt").exists()


def test_list_tree_rejects_option_like_ref(tmp_path):
    bare = _make_repo_with_commit(tmp_path)
    try:
        git_utils.list_tree(bare, _malicious_ref(tmp_path, "pwned_tree.txt"))
    except git_utils.GitError:
        pass
    assert not (tmp_path / "pwned_tree.txt").exists()


def test_list_tree_recursive_rejects_option_like_ref(tmp_path):
    bare = _make_repo_with_commit(tmp_path)
    try:
        git_utils.list_tree_recursive(bare, _malicious_ref(tmp_path, "pwned_treerec.txt"))
    except git_utils.GitError:
        pass
    assert not (tmp_path / "pwned_treerec.txt").exists()


# --- regression: legitimate refs must still behave exactly as before -------


def test_log_still_works_with_real_ref(tmp_path):
    bare = _make_repo_with_commit(tmp_path)
    commits = git_utils.log(bare, ref="main")
    assert len(commits) == 1
    assert commits[0].message == "c1"


def test_read_file_still_works_with_real_ref(tmp_path):
    bare = _make_repo_with_commit(tmp_path)
    assert git_utils.read_file(bare, "main", "file.txt") == "hello\n"


def test_list_tree_still_works_with_real_ref(tmp_path):
    bare = _make_repo_with_commit(tmp_path)
    entries = git_utils.list_tree(bare, "main")
    assert [e.name for e in entries] == ["file.txt"]
