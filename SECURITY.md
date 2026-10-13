# Security policy

## Supported versions

Only the latest release gets fixes. Update with
`tern plugin install github.com/willstarnet/tern-git-fx --force`.

## Reporting a vulnerability

Report it privately through GitHub:
<https://github.com/willstarnet/tern-git-fx/security/advisories/new>. Do not open a public issue,
pull request or discussion about it.

Include what you found, the tern-git-fx version (`tern plugin list`), the Tern version
(`tern --version`), your OS, and steps or a proof of concept. You will get a reply within a week;
the fix ships in a new release with a published advisory.

## Scope

Tern has no plugin permission system, so these guarantees are the plugin's own, enforced by its
code and review. A way to make tern-git-fx break one is in scope:

- storing, logging or sending a command line, working directory or path;
- typing into, running commands in, or reading output from a terminal;
- any network request, child process, clipboard access or change to Tern's settings;
- the overlay taking clicks, keystrokes, selection or focus from a pane, or changing its
  content;
- a `config.json` value or a bundled asset injecting CSS or escaping the plugin's folders.

Out of scope: vulnerabilities in Tern itself (report those to Stencil), other plugins, and a
modified copy of the plugin's source.
