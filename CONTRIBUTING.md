```
gh workflow run rotator.yml --ref 3-Create_the_basic_workflows --repo Arla-OMB/product-rotator -f triggering_repo='Arla-OMB/omb-frontend' -f triggering_event='main/LATEST' -f component_sha='23ad45' -f configuration=dev
```

## Select the default Interpreter
During the container post creation process a Python venv is created and activated, and it's configured in the `.vscode/settings.json` that this is the default interpreter path - but you still need to instruct VS Code to actually use that setting.

`Command Pallette...` >> `Python: Select Interpreter` >> `Use Python from 'python.defaultInterpreterPath' setting ` 