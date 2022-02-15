# Workflow

[TOC]

## NoOps repositories structure

### Product (Application code)

The product is the application code where the business value is important.

To be compliant with NoOps a product needs to define a `noops.yaml` file.

Everything else like DevOps stuff, Pipelines scripts etc are not part of the product repository. Of course to trigger some actions, a pipeline needs to be set. The main difference with a common DevOps approach is that pipeline part will be really small and will not define how to do a CI or a CD for the product.

#### Example

##### Repository

A bitbucket pipeline is used for this example

```bash
# ls -1

.git                       # git repository
src                        # source code
noops.yaml                 # provides context about this application
bitbucket-pipeline.yml     # pipeline file
```

##### noops.yaml

This is the minimal configuration required.

```yaml
devops:
  git:
    clone: git@bitbucket.org:scaffold-devops.git    # the DevOps part shared between multiple products in a dedicated repository
    branch: main
```

##### Pipeline

We are using a bitbucket pipeline and we are just triggering a CI for all branches to simplify this example.

It is possible to use any other pipelines that are able to run shell and python scripts (inside a docker image can be better but it is not mandatory).

```yaml
image: pipelines-builder-noops:v1

pipelines:
  default:
  - step:
      name: ci only
      script:
      - noopsctl -vv -p . pipeline ci image
      services:
      - docker
```

Previously, we said that the pipeline of a product repository do **NOT** describe how to do a CI or a CD. As you can see this is the case because we only invocate `noopsctl`.

### DevOps

#### Shared across products

As a developer you don't need to take care about this section in a NoOps target.

Most of the time a product should start from a scaffold to **do not** reinvent the wheel each time.
By doing so, multiple products can share the same DevOps portion without any effort and in a safe manner.

The DevOps repository defines **how to do**:

- Docker image
- packaging for deployment
- CI
- CD
- local build
- local run
- ...

#### Dedicated to one product ONLY

In some specific cases, you may want to have a dedicated devops structure for one product only. Despite it is always possible to have a dedicated DevOps repository with 1:1 relationship, it can be useful to have everything in the product repository.

To do so you can use this `noops.yaml` minimal configuration:

```yaml
devops:
  local:
    path: noops    # the DevOps part (eg: noops folder) in the product repository
```

The content of the DevOps folder is **exactly** the same locally than in a dedicated DevOps repository.

#### Partial override in product

In some cases, it can be useful to partially override `noops.yaml` set in DevOps part.

Product `noops.yaml` file is merged in DevOps `noops.yaml` file with the highest priority. This is the merged `noops.yaml` result that is used by `noopsctl`. 

This behaviour permit to avoid DevOps fork due to a new product request. This is up to you to determine if this new request can be later upstreamed to your own DevOps scaffold or if you really need to fork it as a possible base for new products. At the first place, partial override help to have an iterative approach and to try experimental features.

Profiles supported in `noops.yaml` are using this partial override mecanism.

## Connecting Product and DevOps

This is the purpose of this repository. **python-noops** provides `noopsctl` used by the product pipeline. It is doing the glue between a product repository and a DevOps repository.

The connecting workflow is:

1. load `noops.yaml` from *product*
2. read *devops section*
3. git clone or copy the devops repository linked with this product in a *noops_workdir*
4. load `noops.yaml` from *devops*
5. merge both `noops.yaml` together. Product noops.yaml will **override** DevOps noops.yaml.
6. merge profile settings on top
7. Store the final merged result to the *noops_workdir*
8. Pull helm chart **(optional)**

At this stage, the cache directory *noops_workdir* is populate and any `noopsctl` subcommand can be used.
All files path set in `noops.yaml` are now using an absolute path (there were set with relative path in product or DevOps).

### Merge strategies

Globally, a deep merge strategy is applied on yaml.

#### value

| Product (noops.yaml)  | DevOps (noops.yaml)   | noops_workdir (noops-generated.yaml) |
| --------------------- | --------------------- | ------------------------------------ |
| key1: value1          | key1: value2          | key1: value1                         |
|                       | key1: value2          | key1: value2                         |
| deep.path.key: value1 | deep.path.key: value2 | deep.path.key: value1                |

The value from product replace the value from DevOps if it is set.

#### value (list)

A list is considered as a value and so the same merge strategy apply for them. There is **NO** deep merge inside a list.

| Product (noops.yaml) | DevOps (noops.yaml) | noops_workdir (noops-generated.yaml) |
| -------------------- | ------------------- | ------------------------------------ |
| key1: [v1, v2]       | key1: [v3]          | key1: [v1, v2]                       |

#### value (path)

A path is considered as a value and so the same merge strategy apply for them. But a path is set with a relative path in a Product or DevOps `noops.yaml`. During the merge, `noopsctl` will store the resulting path with an absolute path and will check if the file exist at the right location !

Product `noops.yaml` can refer to a file available in the Product or in the DevOps structure.

DevOps `noops.yaml` can refer **ONLY** to a file available in the DevOps structure.

Here is an overriding table for reference where:

- both.sh exists in Product and DevOps
- devops-only.sh exists in DevOps ONLY
- product-only.sh exists in Product ONLY
- error.sh does NOT exist in Product and DevOps

| Product (noops.yaml)  | DevOps (noops_workdir/noops.yaml) | noops_workdir (noops-generated.yaml)                         |
| --------------------- | --------------------------------- | ------------------------------------------------------------ |
|                       | file: both.sh                     | file: $PRODUCT_PATH/**noops_workdir**/both.sh                |
| file: both.sh         |                                   | file: $PRODUCT_PATH/both.sh                                  |
| file: both.sh         | file: both.sh                     | file: $PRODUCT_PATH/both.sh                                  |
| file: devops-only.sh  | file: both.sh                     | file: $PRODUCT_PATH/**noops_workdir**/devops-only.sh         |
| file: product-only.sh | file: both.sh                     | file: $PRODUCT_PATH/product-only.sh                          |
| file: error.sh        | file: both.sh                     | $PRODUCT_PATH/error.sh and $PRODUCT_PATH/**noops_workdir**/error.sh do NOT exist |
|                       | file: error.sh                    | $PRODUCT_PATH/**noops_workdir**/error.sh does NOT exist      |
|                       | file: product-only.sh             | $PRODUCT_PATH/**noops_workdir**/product-only.sh does NOT exist |

## Pipeline or Local executions

1. call the connecting Product and DevOps workflow (caching can be involved and some steps can be skipped)
2. convert some `noops.yaml parameters` (eg: Service Catalog, Helm parameters, etc) **(optional)**
3. execute the script/binary (eg: `pipeline.image.ci` for `noopsctl -p . pipeline ci image`) **(optional)**

