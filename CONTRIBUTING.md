## Select the default Interpreter
During the container post creation process a Python venv is created and activated, and it's configured in the `.vscode/settings.json` that this is the default interpreter path - but you still need to instruct VS Code to actually use that setting.

`Command Pallette...` >> `Python: Select Interpreter` >> `Use Python from 'python.defaultInterpreterPath' setting ` 

## Work those unit tests
If you alter the code you should create/update the corresponding unit tests

## Any commit headed for `main` must explicitly reference an issue in GitHub with a closing keyword

eg.

```shell
git commit -m "Fixed stuff - resolves #14"
git commit -m "Added a file - close #15"
```

