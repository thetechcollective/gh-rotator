# Configuration Rotator
#### Used to suppart a product repository, which define and _rotate_ a configuration of a product with a composite product structure — a _multi repo_ product.

>[!NOTE]
>**The "configuration rotator" concept is used to forward and update a _composite_ product. _Composite_ defined as a product that is essentially stitched together as a _dependency map_ of individually released components. Every time a new version of _any_ of the components that contribute to the composite product is release, this "rotator" repo is triggered to setup, deploy and test, wether or not this new dependency map is compliant or not – and marks it accordingly.**

This repo contains the documentation for how to set up the configuration rotaor in a seperate product repoistory, and most importantly at GitGub Command Line extension which will allow you to outomate the process.

## The basics
This is an oppiniated flavor of a solution. Others could have done this differently but here's how we work this.

### A logical map and a manifest 
Think of how `npm`, `pipenv`, `uv` or `bundle` works

- There's a _configuration_ which describes the generic or logical concept of the product.
- There's a _manifest_ of how that configuration was interpreted into concrete composite product. 

This concept is similar but now tranfered to a git repository context. So the basic trigger is that _a git repo included in the dependency map is updated_.


The generic map looks like this (in python's uv this corresponds to the `dependencies` described in a `pyproject.toml`):

```json
#FILE: product-config.json
{
    "dev": [
      {
        "repo": "thetechcollective/gh-tt",
        "trigger": "main/LATEST"
      },
      {
        "repo": "lakruzz/gh-semver",
        "trigger": "main/LATEST"
      },
      {
        "repo": "thetechcollective/gh-downstream",
        "trigger": "main/LATEST"
      }
    ],
    "qa": [
      {
        "repo": "thetechcollective/gh-tt",
        "trigger": "tag:\\d+\\.\\d+\\.\\d+rc"
      },
      {
        "repo": "lakruzz/gh-semver",
        "trigger": "tag:\\d+\\.\\d+\\.\\d+rc"
      },
      {
        "repo": "thetechcollective/gh-downstream",
        "trigger": "tag:\\d+\\.\\d+\\.\\d+rc"
      }
    ],
    "prod": [
      {
        "repo": "thetechcollective/gh-tt",
        "trigger": "tag:\\d+\\.\\d+\\.\\d+"
      },
      {
        "repo": "lakruzz/gh-semver",
        "trigger": "tag:\\d+\\.\\d+\\.\\d+"
      },
      {
        "repo": "thetechcollective/gh-downstream",
        "trigger": "tag:\\d+\\.\\d+\\.\\d+(rc){0,1}"
      }
    ]
  }
```

The `dev` configuration is rotated by any new commit to `main` but the `qa` configuration is more stable, it's only triggered by SemVer tags with an `rc` suffix (e.g. `1.0.12rc`, `1.0.13rc`. `2.1.23rc` etc)

When the dependency map is interpreted it results in a concrete manifest where the trigger is replaced with the SHA1 and a note to indicate what ressloved the SHA1

Showing the `dev` manifest as an example - staying with Pythnon's uv tool this is then the equvivalent to the `uv.lock` file.

```json
#FILE: /configurations/dev/condif-dev-manifest.json
{
    "dev": [
        {
            "repo": "thetechcollective/gh-tt",
            "version": "67e0847ed6dcceb279ad6dfbac5225d753f68500",
            "event": "main/LATEST",
            "last_update": "2025-05-06 (14:06:11) [UTC]"
        },
        {
            "repo": "lakruzz/gh-semver",
            "version": "dad544ed1e6700917f55e35565cda803630c739a",
            "event": "main/LATEST",
            "last_update": "2025-05-06 (13:25:40) [UTC]"
        },
        {
            "repo": "thetechcollective/gh-downstream",
            "version": "3d093a743ab527927e1d956a9114a624d353a6cc",
            "event": "main/LATEST",
            "last_update": "2025-05-06 (13:03:45) [UTC]"
        }
    ]
}
```

### Each config has it's own flow - mapped by configration name
The rotator is implemented by using four flows (`.github/workflows/*.yml`)

The first one is the `rotator.yml` this flow contains a job wichi is dispatch enabled (can be triggered manually or programatically by using `gh workflow run ...`). The dispatch job takes four requireed parameters:

```yml
on:
  workflow_dispatch:
    inputs:
      triggering_repo:
        description: 'Repo that triggered the run (e.g., owner/repo)'
        required: true
        type: string
        # Accessible at the caller as ${{github.repository}}
      triggering_event:
        description: 'Event that triggered the run'
        required: true
        type: string
        # Accessible at the caller as ${{github.event_name}}
      component_sha:
        description: 'SHA of the commit in the triggering repo'
        required: true
        type: string
        # Accessible at the caller as ${{github.sha}}
      configuration:
        description: 'Configuration to use for the deployment'
        required: true
        type: string
        # Must be a configuration defined in the product-rotator.json
        # defaults are [dev|qa|prod]
```
See the entire flow in the [`rotator.yml` template](./templates/product-repo/.github/workflows/rotator.yml)


The flow then passes the four parameters to `gh rotator manifest ...` which will check that validity according to the config, and if a roatation is required it will update the maifest for corresponding configuration, check it in and pust back to origin.

The manifests are divided up into a seperate file for each configuration. Each has it's own workflow:  

`dev`  = `.github/workflows/product-rotator-dev.yml`<br/>
`qa` = `.github/workflows/product-rotator-qa.yml`<br/>
`prod` = `.github/workflows/product-rotator-prod.yml`<br/>

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







