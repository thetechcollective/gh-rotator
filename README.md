# Configuration Rotator
#### Used to support a product repository, which defines and _rotates_ a configuration of a product with a composite product structure — a _multi repo_ product.

>[!NOTE]
>**The "configuration rotator" concept is used to forward and update a _composite_ product. _Composite_ defined as a product that is essentially stitched together as a _dependency map_ of individually released components. Every time a new version of _any_ of the components that contribute to the composite product is release, this _rotator_  workflow is triggered to manifest, deploy and test, wether or not this new dependency map is compliant or not – and marks it accordingly.**

This repo contains the documentation for how to set up the configuration rotaor in a seperate product repoistory, and most importantly at GitGub Command Line extension which will allow you to automate the process.

## The basics
This is an oppiniated flavor of a solution. Others could have done this differently but here's how we work this.

### A logical map and a manifest 
Think of how `npm`, `pipenv`, `uv` or `bundle` works

- There's a _configuration_ which describes the generic or logical concept of the product.
- There's a _manifest_ of how that configuration was interpreted into concrete selection of virsioned components. 

The concept in Config Rotator is similar but now tranfered to a git repository context. So the basic trigger is that _a git repo included in the dependency map is updated_.

The generic map is implemented in a `config-rotator.json` file in the root of the product repository. In python's uv this corresponds to the `dependencies` described in a `pyproject.toml`:

It contains a set of configurations — in our case `dev`, `qa` and `prod`.

Each component is defind by the fully qulified `repo` name, the `ref_type` that should trigger the flow (`branch`|`tag`), and `ref_name` which is a regular expression, which that actual `ref_name` must be match against.

```json
{
    "dev": [
      {
        "repo": "config-rotator/iac-component",
        "ref_type": "branch",
        "ref_name": "main"
      },
      {
        "repo": "config-rotator/iac-frontend",
        "ref_type": "branch",
        "ref_name": "main"
      },
      {
        "repo": "config-rotator/iac-backend",
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
        "repo": "config-rotator/iac-frontend",
        "ref_type": "tag",
        "ref_name": "\\d+\\.\\d+\\.\\d+rc"
      },
      {
        "repo": "config-rotator/iac-backend",
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
        "repo": "config-rotator/iac-frontend",
        "ref_type": "tag",
        "ref_name": "\\d+\\.\\d+\\.\\d+"
      },
      {
        "repo": "config-rotator/iac-backend",
        "ref_type": "tag",
        "ref_name": "\\d+\\.\\d+\\.\\d+"
      }
    ]
  }
```

The example above is quite generic (and oppinionated)  and you can probably use it as it is, only renaming the `repo` elements and leaving everything else as it is.

The concepts is that the `dev` configuration is rotated by any new commit to `main`. The `qa` configuration is more stable, it's  triggered by releasae candidate SemVer tags with an `rc` suffix (e.g. `1.0.12rc`, `1.0.13rc`. `2.1.23rc` etc) and the `prod` config is triggered by SemVer tags ((e.g. `1.0.0`, `1.0.13`. `2.1.0` etc))

When the dependency map is interpreted it results in a concrete manifest where the trigger is replaced with the SHA1 and a note to indicate what resloved the SHA1

Showing the `dev` manifest as an example - staying with the comparison to Python's uv tool this is then the equvivalent to the `uv.lock` file.

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
            "repo": "config-rotator/iac-frontend",
            "version": "dad544ed1e6700917f55e35565cda803630c739a",
            "ref_type": "branch",
            "ref_name": "main"
            "last_update": "2025-05-06 (13:25:40) [UTC]"
        },
        {
            "repo": "config-rotator/iac-backend",
            "version": "3d093a743ab527927e1d956a9114a624d353a6cc",
            "ref_type": "branch",
            "ref_name": "main"
            "last_update": "2025-05-06 (13:03:45) [UTC]"
        }
    ]
}
```

The manifest files are created by the workflow in the product repo at<br/> `./configurations/<CONFIGURATION>/config-<CONFIGURATION>-manifest.json`

So conseqently `dev`, `qa` or `prod` configurations will be created as:

- `./configurations/dev/config-dev-manifest.json`
- `./configurations/qa/config-qa-manifest.json`
- `./configurations/prod/config-prod-manifest.json`

### One flow to trigger everything
The rotator is implemented by using a genric flow (`.github/workflows/rotator.yml`)

This flow takes a set of predefined mandatory parameters and have dispatch enabled, which enables that it can be triggered either manually or programatically by using `gh workflow run ...`). 

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

The flow then passes the four parameters to `gh rotator manifest ...` a subcommand in this GitHub CLI extension. It will check that validity of the parameters according to the a given config. And if a match is found in any of the configurations it will update the corresponding maifest with the instantiated configuration, check it in and pust back to origin.

## Infrastructure as code 

After the manifest is updated and stored, contoll is passed on to a generid script, which will read and utilitlise the data in the updated manifest to deploy the infrastructure and run the according automated test.

We implement this as another GitHub CLI extension; which is a simple wrapper to serve as a generic interface to start our Pulumi scripts and initiate tests.

## Setup

All the repos mentioned in the product configuration could be setup as callers, which essentially means that they can trigger a configuration rotation.

Using the examples from above we could setup a product repository at `thetechcollective/product-sample`

### Product repo: `thetechcollective/product-sample`

Required configuration

- `./product-rotator.json`

Required workflows

- `.github/workflows/rotator.yml`
- `.github/workflows/product-rotator-dev.yml`<br/>
- `.github/workflows/product-rotator-qa.yml`<br/>
- `.github/workflows/product-rotator-prod.yml`<br/> 
- ...you should set up a job for each configuration defined in `product-rotator.json`

The following dirs/files will be create automatically

- `./configurations`
  - `dev`
    - `config-dev-manifest.json`
  - `qa`
    - `config-qa-manifest.json`
  - `prod`
    - `config-peod-manifest.json`
  - ...one subfolders with corresponding manifest will be created for each config defined in the `prodcut-rotator.json`



### Caller repos:
In the example the following repos are defined in the dependency map `product-rotator.json`

- `thetechcollective/gh-tt`
- `lakruzz/gh-semver`
- `thetechcollective/gh-downstream`

These are all candidates to be set up as _callers_ so they can trigger the `rotator.yml` job in the 

The template flow is [rotate-config](./templates/caller/.github/workflows/rotate-config.yml)

The conceptual ideas in an _individually releaseble component_  structure (as opposed to a mone-repo) is that each componnet must define a trust-worthy _self-test_ which — if successful — defines a _potentially shippable_  state and the repos should then trigger the product config rotator to verify the shippableness (cool word eh?)

So the entire `rotate-config.yml` may not actually be needed but the steps described cond be incorporated as post steps in a successfule self-test workflow, whatever that looks like in the given context.







