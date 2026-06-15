# Changelog

All notable changes to this project will be documented in this file.

## 0.1.2 - 2026-06-15

- Fixed packaged installs by declaring `click` as a direct runtime dependency.

## 0.1.1 - 2026-02-21

- Updated README with PyPI release workflow and trusted publishing setup.

## 0.1.0 - 2026-02-06

First public release of `vidio-cli`.

- Added core commands for everyday video workflows:
  - `list` / `ls`
  - `info`
  - `trim`
  - `resize`
  - `crop`
  - `concat`
  - `grid`
  - `to-gif`
- Added dynamic command discovery and registration.
- Added test coverage for command behavior and output handling.
- Added distribution build support for wheel and source tarball.
