# Configuration Rotator
#### Supports a product repository by defining and _rotating_ a configuration of a product with a composite product structure — a _multi-repo_ product.

>[!NOTE]
>**The "configuration rotator" concept is used to update and manage a _composite_ product. A _composite_ product is defined as one that is essentially stitched together as a _dependency map_ of individually released components. Every time a new version of _any_ component contributing to the composite product is released, this _rotator_ workflow is triggered to manifest, deploy, and test whether this new dependency map is compliant — marking it accordingly.**

This repository contains documentation on setting up the configuration rotator in a separate product repository and, most importantly, a GitHub Command Line extension to automate the process.

## The basics
This is an opinionated solution. Others may approach this differently, but here's how we implement it.

### A logical map and a manifest 
Think of how `npm`, `pipenv`, `uv` or `bundle` works

- There's a _configuration_ which describes the generic or logical concept of the product.
- There's a _manifest_ of how that configuration was interpreted into concrete selection of versioned components. 

The concept in Config Rotator is similar but now transferred to a Git repository context. The basic trigger is that _a Git repository included in the dependency map is updated_.

The generic map is implemented in a `config-rotator.json` file in the root of the product repository. In python's uv this corresponds to the `dependencies` described in a `pyproject.toml`:

It contains a set of configurations — in our case `dev`, `qa` and `prod`.

Each component is defined by the fully qualified `repo` name, the `ref_type` that should trigger the flow (`branch`|`tag`), and `ref_name`, which is a regular expression that the actual `ref_name` must match.

```json
{
    "dev": [
      {
        "repo": "config-rotator/iac-component",
        "ref_type": "branch",
        "ref_name": "main"
      },
      {
        "repo": "config-rotator/frontend-component",
        "ref_type": "branch",
        "ref_name": "main"
      },
      {
        "repo": "config-rotator/backend-component",
        "ref_type": "branch",
        "ref_name": "main"
      }
    ],
    "qa": [
      {
        "repo": "config-rotator/iac-component",
        "ref_type": "tag",
        "ref_name": "\\d+\\.\\d+\\.\\d+rc"
      },
      {
        "repo": "config-rotator/frontend-component",
        "ref_type": "tag",
        "ref_name": "\\d+\\.\\d+\\.\\d+rc"
      },
      {
        "repo": "config-rotator/backend-component",
        "ref_type": "tag",
        "ref_name": "\\d+\\.\\d+\\.\\d+rc"
      }
    ],
    "prod": [
      {
        "repo": "config-rotator/iac-component",
        "ref_type": "tag",
        "ref_name": "\\d+\\.\\d+\\.\\d+"
      },
      {
        "repo": "config-rotator/frontend--component",
        "ref_type": "tag",
        "ref_name": "\\d+\\.\\d+\\.\\d+"
      },
      {
        "repo": "config-rotator/backend-component",
        "ref_type": "tag",
        "ref_name": "\\d+\\.\\d+\\.\\d+"
      }
    ]
  }
```

The example above is quite generic and you can probably use it as it is, only renaming the `repo` elements and leaving everything else as it is.

The concept is that the `dev` configuration is rotated by any new commit to `main`. The `qa` configuration is more stable, triggered by release candidate SemVer tags with an `rc` suffix (e.g., `1.0.12rc`, `1.0.13rc`, `2.1.23rc`, etc.), and the `prod` configuration is triggered by SemVer tags (e.g., `1.0.0`, `1.0.13`, `2.1.0`, etc.).

When the dependency map is interpreted, it results in a concrete manifest where the version is noted with the SHA and a note indicating what resolved the SHA1.

Showing the `dev` manifest as an example - staying with the comparison to Python's uv tool this is then the equivalent to the `uv.lock` file.

```json
{
    "dev": [
        {
            "repo": "config-rotator/iac-component",
            "version": "67e0847ed6dcceb279ad6dfbac5225d753f68500",
            "ref_type": "branch",
            "ref_name": "main"
            "last_update": "2025-05-06 (14:06:11) [UTC]"
        },
        {
            "repo": "config-rotator/frontend-component",
            "version": "dad544ed1e6700917f55e35565cda803630c739a",
            "ref_type": "branch",
            "ref_name": "main"
            "last_update": "2025-05-06 (13:25:40) [UTC]"
        },
        {
            "repo": "config-rotator/backend-component",
            "version": "3d093a743ab527927e1d956a9114a624d353a6cc",
            "ref_type": "branch",
            "ref_name": "main"
            "last_update": "2025-05-06 (13:03:45) [UTC]"
        }
    ]
}
```

The manifest files are created by the workflow in the product repo at<br/> `./configurations/<CONFIGURATION>/config-<CONFIGURATION>-manifest.json`

So consequently `dev`, `qa` or `prod` configurations will be created as:

- `./configurations/dev/config-dev-manifest.json`
- `./configurations/qa/config-qa-manifest.json`
- `./configurations/prod/config-prod-manifest.json`

### One flow to trigger everything
Besides the `config-rotator.json` config file, the product repo also offers a rotator flow, implemented by using a generic flow (`.github/workflows/rotator.yml`)

This flow takes a set of predefined mandatory parameters and have dispatch enabled, which enables that it can be triggered either manually or programmatically by using `gh workflow run ...`). 

The parameters are defines as:

```yml
on:
  workflow_dispatch:
    inputs:
      triggering_repo:
        description: 'Repo that triggered the run (e.g., owner/repo)'
        required: true
        type: string
        # Accessible at the caller as ${{github.repository}}
      triggering_event_type:
        description: 'Event type that triggered the run (branch|tag)'
        required: true
        type: string
        # Accessible at the caller as ${{github.ref_type}}
      triggering_event_name:
        description: 'Event that triggered the run (branch or tag name)'
        required: true
        type: string
        # Accessible at the caller as ${{github.ref_name}}
      component_sha:
        description: 'SHA of the commit in the triggering repo'
        required: true
        type: string
        # Accessible at the caller as ${{github.sha}}
```
See the entire flow in the [`rotator.yml` template](./templates/product-repo/.github/workflows/rotator.yml)

The flow then passes the four parameters to `gh rotator manifest ...`, a subcommand in this GitHub CLI extension. It will validate the parameters against the given configuration. If a match is found in any of the configurations, it will update the corresponding manifest with the instantiated configuration, check it in, and push it back to the origin.

## Infrastructure as code 

After the manifest is updated and stored, control is passed on to the next job in the flow which is designed to call a generic script, which will read the data in the updated manifest and start to deploy the infrastructure and run the according automated test.

The recommendation is that you build a gh-cli extension script (much like this `gh-rotator` script) see our [py-cli-template](https://github.com/thetechcollective/py-cli-template) for inspiration.

The script should take a manifest file as parameter and build the infrastructure needed and deploy based on that.

### Alternative approach
It may be, that the IaC, deploy and test procedures for the various configurations are so divers that it makes sense to keep the `rotator.yml` flow generic and simple and then set up separate jobs to trigger on a new manifest file being committed. [`product-rotator-dev.yml`](./templates/product-repo/.github/workflows/product-rotator-dev.yml) is example of this. It's specifically designed to run when the _dev_ configuration is updated:


```yaml
name: Dev Deploy

on:
  # This is the 'dev' configuration
  workflow_dispatch:
  # trigger on push to main
  push:
    branches:
      - main
    paths:
      - 'configurations/dev/config-dev-manifest.json'   
```
You can create similar individual flows for the other manifests too.

## Setup

All the repos mentioned in the product configuration could be setup as _callers_, which essentially means that they can trigger a configuration rotation.

We have simulated a setup in 
- `config-rotator/product-sample`
- `config-rotator/iac--component`
- `config-rotator/frontend--component`
- `config-rotator/backend-component`

### Product repo: `config-rotator/product-sample`

Required configuration

- `./config-rotator.json`

Required workflows

- `.github/workflows/rotator.yml`

The following dirs/files will be create automatically

- `./configurations`
  - `dev`
    - `config-dev-manifest.json`
  - `qa`
    - `config-qa-manifest.json`
  - `prod`
    - `config-prod-manifest.json`

 
### Caller repos:
In the example the following repos are defined in the dependency map `config-rotator.json`

- `config-rotator/iac--component`
- `config-rotator/frontend--component`
- `config-rotator/backend-component`

These are all candidates to be set up as _callers_ so they can trigger the `rotator.yml` job in the product-repo 

The template flow is [rotate-config](./templates/caller/.github/workflows/rotator-config.yml)

The conceptual ideas that each repo is an _individually releasable component_  that works in a structure - as opposed to a mono-repo. 

Each component must define a trust-worthy _self-test_ which — if successful — defines a _potentially shippable_ state. Ideally this is when the commit hits main, so the test should happen as part of a delivery or pull request process. This should trigger the product config rotator to verify the shippableness (cool word eh?)

In our template workflow we have shown how that can be done in a separate workflow.

Another useful flow is [create-prerelease](./templates/caller/.github/workflows/create-prerelease.yml) which will take a sha as parameter and make it as a prerelease (create a SemVer tag bumping _patch_ with an `rc` – release candidate suffix and marking it as a prerelease in GitHub).

>[!NOTE]
>#### Generate PAT for the _caller_
>By design, one workflow can not trigger another workflow based on the standard `secrets.GITHUB_TOKEN`. To solve this the step that triggers the workflow uses `secrets.ROTATOR_TOKEN`. You must create and installer this PAT – Personal Access Token. Do the following:
>1. In you GitHub Profile define a _finer grained_ PAT - Personal Access Token
>   - As _resource owner_ select the organization that host the product-repo
>   - The _access_ can be limited to the same repo
>   - _grant_ read/write to `actions` and read to `contents`and `metadata`
>2. Capture the TOKEN in you clipboard and go to each of the caller repos and under _settings_ define a repository action secret named `ROTATOR_TOKEN`

<details><summary>Detailed screen dumps from GitHub</summary>

<img src="https://github.com/user-attachments/assets/895e30ad-f023-4ade-aeb9-adfb66c85f7f"/>
<img src="https://github.com/user-attachments/assets/e7505b10-4bbd-40d2-8c9c-32ce2d506c2f"/>
<img src="https://github.com/user-attachments/assets/53ab73a8-fa67-4cf5-ac70-0811c6de76bb"/>)

</details>

>[!NOTE]
>#### Generate COMMIT PAT for the _product repo_ (rotator.yml) and the _caller repos_ (create-prerelease.yml)
>A file checked into a repo using the built-in GitHub token `secrets.GITHUB_TOKEN` will not trigger a workflow on GitHub. This is by design. To solve this the step that checks out the repo and the step that checks in the updated manifest uses `secrets.ROTATOR_COMMIT_TOKEN` You must create an install a PAT – Personal Access Token. Do the following:
>1. In you GitHub Profile define a new _finer grained_ PAT - Personal Access Token
>   - As _resource owner_ select the organization that host the product-repo
>   - The _access_ can be limited to the repos that needs it
>   - _grant_ 
>       - read/write to `contents` 
>       - read/write to `actions` 
>       - read to `metadata`
>2. Capture the TOKEN in you clipboard and go to each of the caller repos and under _settings_ define a repository action secret named `ROTATOR_COMMIT_TOKEN`


