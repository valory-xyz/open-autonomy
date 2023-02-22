# Contribution Guide.

### Creating A Pull Request
- **Target branch:** double-check the PR is opened against the correct branch before submitting
- **Naming convention:** name of the branch should be in kebab case with not more than two or three words. for example `some-feature` or `feat/some-feature`.
- **Tag relevant ticket/issue:** describe the purpose of the PR properly with relevant ticket/issue. Also attaching a tag such as enhancement/bug/test would help.
- **Include a sensible description:** descriptions help reviewers to understand the purpose and context of the proposed changes.
- **Properly comment non-obvious  code** to avoid confusion during the review and enhance maintainability.
- **Code reviews:** two reviewers will be assigned to a PR.
- **Linters:** make sure every linter and checks pass before making a commit. Linters help us maintain a coherent codebase with a common code style, proper API documentation and will help you catch most errors before even running your code.
- **Tests:** the PR needs to contain tests for the newly added code or updated code. (If a commit is made for sole purpose of the review you can add tests later after review is done and PR is ready to merge)

Also mention potential effects on other branches/code might have from your changes.

For a clean workflow run checks in following order before making a PR or pushing the code

- make clean
- make formatters
- make code-checks
- make security

**Run only if you've modified an AbciApp definition**
- make abci-docstrings

**Only run following if you have modified a file in `packages/`**
- make generators
- make common-checks-1

**else run**
- make copyright

**run this after making a commit**
- make common-checks-2


### Documentation (Docstrings and inline comments)
- Instead of writing just single line of docstring write more informative docstring. If a method is fairly easy to understand one line of docstring will do but if the method has more complex logic it needs be documented properly.
```python
def some_method(some_arg: Type) -> ReturnType:
    """
    This method does something very complex.

    example:
      >> a = Type("value")
      >> some_method(a)
      output

    :param some_arg: describe argument.
    :return: value of ReturnType

    optional
    - types of exceptions it might raise
    """
```
- To run documentation server use `mkdocs serve`.
- After editing documentation use `./scripts/spell-check.sh` to ensure spelling is correct.

### Some more suggestions to help you write better code.

- Always use guard clauses where possible. This leads to more efficient code that has less nesting and is much easier to read.


### Agent development

You can find several general recommendations in the **Considerations to Develop FSM Apps** section in our documentation [here](https://docs.autonolas.network/open-autonomy/key_concepts/fsm_app_introduction/).