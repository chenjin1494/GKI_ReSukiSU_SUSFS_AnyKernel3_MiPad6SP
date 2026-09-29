# Sources and References

This repository does not reproduce private device properties or user-provided `getprop` output. Source revisions and hashes belong in the project-maintained `sources.lock.json`; a release must not proceed while those values are placeholders.

The workflow and test contracts are based on these public references:

- GitHub Actions workflow syntax: <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions>
- GitHub Actions security hardening and permissions: <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions>
- GitHub artifact actions: <https://github.com/actions/upload-artifact> and <https://github.com/actions/download-artifact>
- Python `unittest` command-line interface: <https://docs.python.org/3/library/unittest.html#command-line-interface>
- GNU Bash syntax checking (`bash -n`): <https://www.gnu.org/software/bash/manual/bash.html>

These links document tool behavior and workflow mechanics. They are not evidence that the kernel, patch chain, KPM integration, or hardware has been built or validated.
