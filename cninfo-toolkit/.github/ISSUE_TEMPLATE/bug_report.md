name: Bug Report

description: Report a bug in cninfo-toolkit
title: "[Bug] "
labels: ["bug", "triage"]

body:
  - type: markdown
    attributes:
      value: |
        Thanks for reporting a bug. Please fill out the template below.

  - type: textarea
    id: description
    attributes:
      label: Describe the bug
      description: A clear and concise description of what the bug is.
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to reproduce
      description: Steps to reproduce the behavior.
      placeholder: |
        1. Install cninfo-toolkit via `pip install ...`
        2. Run `cninfo anns 600487.SH`
        3. See error
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
      description: A clear and concise description of what you expected to happen.
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual behavior
      description: What actually happens, including any error messages.
    validations:
      required: true

  - type: input
    id: version
    attributes:
      label: cninfo-toolkit version
      description: Run `pip show cninfo-toolkit` and paste the version.
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python
    attributes:
      label: Python version
      description: Run `python --version` and paste the output.
      placeholder: "3.11.5"
    validations:
      required: true

  - type: input
    id: os
    attributes:
      label: Operating System
      description: Your OS and version (e.g., macOS 14.1, Ubuntu 22.04, Windows 11).
      placeholder: "macOS 14.1"
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      description: Please paste any relevant log output or stack traces.
      render: shell

  - type: checkboxes
    id: checks
    attributes:
      label: Pre-submission checks
      options:
        - label: I have searched the [issue tracker](https://github.com/chenliitaz/cninfo-toolkit/issues) for similar issues.
          required: true
        - label: I have tested with the latest version of cninfo-toolkit.
          required: true
        - label: I have included a minimal reproduction (code snippet or commands).
          required: true