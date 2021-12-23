# Contribution Guide.

### Making A PR
- **naming convention:** (I think David M. has already mentioned this) Name of the branch should be in kebab case with not more than two words. for example `some-feature` or `feat/some-feature` (We can discuss).
- **tag relevent ticket/issue:** Describe the purpose of the PR properly with relevent ticket/issue. Also attaching a tag such as enhancement/bug/test this can be optional.
- **code reviews:** I don't know if we need to change anything but open to discussion.
- **linters:** Make sure every linter and checks pass before making a commit.
- **tests:** The PR needs to contain tests for the newly added code or updated code (More in Test Driven Development).
  
### Test Driven Development
-

## Better Documentation (Docstrings and inline comments)
- **Docstrings:** Instead of writing just single line of docstring write more informative docstring. If a method is fairly easy to understand one line of docstring will do but if the method has more complex logic it needs be documented properly (It'll also help code reviews for newly implemented code). A simple template
```python
def some_method(arg0: Type) -> ReturnType:
    """
    This method does something very complex.

    Example:
      >> a = Type("value")
      >> some_method(a)
      output

    :param arg0: describe argument.
    :return: value of ReturnType

    optional
    - types of exceptions it might raise
    """
```
**Inline Comments:** Inline comments will help understanding some complex part of method.