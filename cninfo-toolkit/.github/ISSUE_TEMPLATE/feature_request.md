name: Feature Request

description: Suggest a new feature for cninfo-toolkit
title: "[Feature] "
labels: ["enhancement", "triage"]

body:
  - type: markdown
    attributes:
      value: |
        Thanks for suggesting a new feature. Please fill out the template below.

  - type: textarea
    id: problem
    attributes:
      label: Problem statement
      description: What problem does this feature solve?
      placeholder: "I'm always frustrated when..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
      description: A clear and concise description of what you want to happen.
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      description: What other approaches have you considered?
    validations:
      required: false

  - type: textarea
    id: usage
    attributes:
      label: Example usage
      description: Show how the feature would be used (CLI and/or Python API).
      render: python
      placeholder: |
        ```python
        from cninfo_toolkit import new_feature
        result = new_feature("600487.SH")
        print(result)
        ```
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: Contribution
      options:
        - label: I would be willing to submit a PR for this feature.
        - label: I would be willing to test this feature during development.