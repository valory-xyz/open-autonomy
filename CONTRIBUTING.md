# Contribution Guide.

### Making A PR
- **naming convention:** Name of the branch should be in kebab case with not more than two or three words. for example `some-feature` or `feat/some-feature`.
- **tag relevant ticket/issue:** Describe the purpose of the PR properly with relevant ticket/issue. Also attaching a tag such as enhancement/bug/test would help.
- **code reviews:** 2 reviewers will be assigned to a PR.
- **linters:** Make sure every linter and checks pass before making a commit.
- **tests:** The PR needs to contain tests for the newly added code or updated code. (If a commit is made for sole purpose of the review you can add tests later after review is done and PR is ready to merge)
  
Also mention potential effects on other branches/code might have from your changes.
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
### Some more suggestions to help you write better code.

- Always use guard clauses where possible - this leads to code that has less nesting and is much easier to read! It also leads to more efficient code!
- when developing agent applications raise exceptions for all branches which are currently unhandled and would cause inconsistencies in the app. These exceptions can then be surgically addressed in separate PRs. Example: on the happy path a file is loaded properly, on the unhappy path an exception is raised by the file not being present. In production handling this can get involved. During development it is best to "park" this issue and focus on the happy case. But the unhappy case should raise so we can capture its prevalence in tests. Logging is the worst approach as it hides this issue!
