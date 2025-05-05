# product-rotator
#### Used to trigger a new deploy and compliance verification every time any of the components in the composite product structure changes

>[!NOTE]
>**The "product-rotator" concept is used to massage a _composite_ product. _Composite_ defined as a product that is essentially stitched together as a _dependency map_ of individually released components. Every time a new version of _any_ of the components that contribute to the composite product is release, this "rotator" repo is triggered to setup, deploy and test, wether or not this new dependency map is compliant or not – and marks it accordingly.**

## The basics
This is an oppiniated flavor of a solution. Others coulod have done this differently but here's how we work this.

### A logical map and a manifest 
Think of how `npm`, `pipenv`, `uv` or `bundle` works

- There's a _generic decription_ of the map
- There's a _manifest_ of how that map was interpreted into concrete composite product. (often with a `.lock` extenison)

This concept is similar but in a git repo context. So the trigger is that _a git repo somewhere is updated_


The generic map looks like this:

```
#FILE: omb-product.config
[dev]
  # repo                             #trigger         
  arla-OMB/python-new-dawn-graphql   main/LATEST       
  arla-OMB/omb-frontend              main/LATEST
  Arla-OMB/python-new-dawn-iac       main/LATEST

[qa]
  # repo                             #trigger         
  arla-OMB/python-new-dawn-graphql   tag:/\d+\.\d+\.\d+rc/       
  arla-OMB/omb-frontend              tag:/\d+\.\d+\.\d+rc
  Arla-OMB/python-new-dawn-iac       tag:/\d+\.\d+\.\d+[rc]

[prod]
  # repo                             #trigger         
  arla-OMB/python-new-dawn-graphql   tag:/\d+\.\d+\.\d+       
  arla-OMB/omb-frontend              tag:/\d+\.\d+\.\d+
  Arla-OMB/python-new-dawn-iac       tag:/\d+\.\d+\.\d+
```

The `dev` configuration is rotated by any new commit to `main` but the `qa` configuration is more stable, it's only triggered by SemVer tags with an `rc` suffix (e.g. `1.0.12rc`, `1.0.13rc`. `2.1.23rc` etc)

When the dependency map is interpreted it results in a concrete manifest where the trigger is replased with the SHA1 and a note to indicate what rezsloved the SHA1

```
#FILE: omb-product.dev.lock
  arla-OMB/python-new-dawn-graphql   27642a6     # main/LATEST 
  arla-OMB/omb-frontend              09d675a     # main/LATEST
  Arla-OMB/python-new-dawn-iac       3564fe1     # main/LATEST
```

or for QA:

```
#FILE: omb-product.qa.lock
  arla-OMB/python-new-dawn-graphql   27642a6     # 1.0.12rc 
  arla-OMB/omb-frontend              09d675a     # 1.0.89rc
  Arla-OMB/python-new-dawn-iac       3564fe1     # 1.0.1
```

### Each config has it's own flow - mapped by configration name
In our setup the the rotator is implemnted in GitHub Actions. There is a seperate flow for each config:

`dev`  = `.github/workflows/product-rotator-dev.yml`<br/>
`qa` = `.github/workflows/product-rotator-qa.yml`<br/>
`prod` = `.github/workflows/product-rotator-prod.yml`<br/>
```

The repo has a generic callable action `rotate.yml` (defined with `on: workflow_dispatch`) this trigger is designed to be called from any of the contributing componets (`gh workflow run ...`) when they have run their individual self-test successfully.  

The rotator simply compiles a new mainfest and checkes it in to `main` the product-rotator repo. The updated manifest will trigger the corresponding workflow.

### Each repo will do-its-thing
All componets that trigger the product-rotator flow will be responsible for prebuilding the docker image used in the infrastructure.







