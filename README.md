# NoOps Command line utility

`noopsctl` is an utility which handles noops compliant repositories.

A noops compliant repository (product) exposes `noops.yaml` with multiple directives.
The devops part can be a remote resource with its own `noops.yaml` file.

`noopsctl` will provide an efficient way to handle this kind of repository for pipeline (CI/CD) or local build (Devs computer).



**Table of Contents**

   * [NoOps Command line utility](#noops-command-line-utility)
      * [NoOps](#noops)
         * [Product: Application code](#product-application-code)
            * [repository example](#repository-example)
            * [noops.yaml example](#noopsyaml-example)
            * [pipeline example](#pipeline-example)
         * [DevOps: Shared across products](#devops-shared-across-products)
         * [python-noops: connect Product and DevOps](#python-noops-connect-product-and-devops)
            * [What noopsctl does](#what-noopsctl-does)
            * [What noopsctl does NOT do](#what-noopsctl-does-not-do)
            * [noops.yaml and custom parameters](#noopsyaml-and-custom-parameters)
         * [noops.yaml](#noopsyaml)
            * [Reserved keys](#reserved-keys)
            * [features](#features)
            * [package](#package)
               * [docker](#docker)
               * [helm](#helm)
            * [service-catalog](#service-catalog)
            * [pipeline and local](#pipeline-and-local)
      * [Installation](#installation)
      * [Usage](#usage)
         * [Main help](#main-help)
         * [Continuous Integration](#continuous-integration)
         * [Continuous Integration for a Pull Request](#continuous-integration-for-a-pull-request)
         * [Continuous Deployment](#continuous-deployment)
         * [Build the product locally](#build-the-product-locally)
         * [Run the product locally](#run-the-product-locally)



## NoOps

The main target is to remove all the friction and management relative to infrastructure/operations. Despite everything that you can read about serverless, no operations etc, we still need an ecosystem to execute an application and a workflow to use it.

So the most important is **how to do it**.

NoOps is here to reduce the pain and to permit developers to focus on the application code only. That sound like the promise of DevOps, CI/CD pipeline etc. In reality, DevOps, CI/CD... are still needed but will be hidden or simplified as much as possible. Some external tools like Service Catalog with openbroker api will help to handle the ecosystem required to run the application (eg: storage, database, ... provisioning).

All those practices and tools together permit to achieve the NoOps target.

### Product: Application code

The product is the application code where the value is important.

To be compliant with NoOps a product needs to define a `noops.yaml` file.

Everything else like DevOps stuff, Pipelines scripts etc are not part of the product repository. Of course to trigger some actions, a pipeline file needs to be set. The main difference with a common DevOps approach is that this file will be really small and will not define how to do a CI or a CD for the product.

#### repository example

A bitbucket pipeline is used for this example

```bash
# ls -1

.git                       # git repository
src                        # source code
noops.yaml                 # provides context about this application
bitbucket-pipeline.yml     # pipeline file
```

#### noops.yaml example

This is the minimal configuration required.

```yaml
metadata:
  version: 1

devops:
  git:
    clone: git@bitbucket.org:scaffold-devops.git    # the DevOps part shared between multiple products in a dedicated repository
    branch: main
```

#### pipeline example

We are using a bitbucket pipeline and we are just triggering a CI for all branches to simplify this example.

It is possible to use any other pipelines that are able to run shell and python scripts (inside a docker image can be better but it is not mandatory).

```yaml
image: pipelines-builder-noops:v1

pipelines:
  default:
  - step:
      name: ci only
      script:
      - noopsctl -vv -p . pipeline image --ci
      services:
      - docker
```

Previously, we said that the pipeline of a product repository do **NOT** describe how to do a CI or a CD. As you can see this is the case because we only invocate `noopsctl`.

### DevOps: Shared across products

As a developer you don't need to take care about this section in a NoOps target.

Most of the time a product should start from a scaffold to **do not** reinvent the wheel each time.
By doing so, multiple products can share the same DevOps portion without any effort and in a safe manner.

The DevOps repository defines **how to do** Docker image, packaging for deployment, CI, CD, local build, local run, service catalog requests and whatever you need.

### python-noops: connect Product and DevOps

This is the purpose of this repository. python-noops provides `noopsctl` used by the product pipeline. It is doing the glue between a product repository and a DevOps repository.

![workflow](https://raw.githubusercontent.com/croixbleueqc/python-noops/main/docs/noopsctl-workflow.png)

The main workflow is:

1. load `noops.yaml` from *product*
2. read *devops section*
3. git clone the devops repository linked with this product in a *noops_workdir*
4. load `noops.yaml` from *devops*
5. merge both `noops.yaml` together. Product noops.yaml will **override** DevOps noops.yaml.
6. Store the merged result to the *noops_workdir*
7. execute the request based on parameters provided on the command line



The execution workflow is:

1. call the main workflow (caching can be involved and some steps can be skipped)
2. convert some `noops.yaml parameters` (eg: Service Catalog, Helm parameters, etc) to enhance some components used by the DevOps repository **(optional)**
3. read the script path to use (eg: `pipeline.image.ci` for `noopsctl -p . pipeline image --ci`)
4. execute the script


#### What noopsctl does

- Compute the final `noops.yaml` based on product and devops definitions
- Built-in understanding of few `noops.yaml` keys (eg: `service-catalog`, `package.helm`)
- Create values.yaml files based on `package.helm.parameters`
- Create service catalog files based on `service-catalog`
- Select and execute external scripts to do a CI, CD, local build, local run, etc

#### What noopsctl does NOT do

- Define a CI/CD strategy
- Define how to build a product
- Communicate directly with a service provider

#### noops.yaml and custom parameters

`noopsctl` is able to do few tings but does **NOT** restrict developers or DevOps teams. Some keys in `noops.yaml` are *reserved* **but** you are free to define whatever extra keys you need.

Custom keys can be handled by custom scripts to run a CI, CD, local build/run etc.

`noopsctl` will execute a script by passing 2 environments variables that will permit to read computed `noops.yaml` values:

- NOOPS_GENERATED_JSON (computed noops.yaml as json format)
- NOOPS_GENERATED_YAML (computed noops.yaml)

```bash
# Example to read the Dockerfile path
DOCKERFILE=$(cat $NOOPS_GENERATED_JSON | jq -r .package.docker.dockerfile)
```

### noops.yaml

#### Reserved keys

The next example defines some reserved keys and custom keys.

reserved keys are:

- features
- package.docker.dockerfile
- package.helm.{chart,preprocessor,parameters}
- pipeline.image.{ci,pr,cd}
- pipeline.deploy.default
- local.build
- local.run
- service-catalog

custom keys are everything else

```yaml
metadata:
  version: 1

features:
  service-catalog: true

package:
  docker:
    dockerfile: docker/Dockerfile

  helm:
    chart: helm/chart
    preprocessor: helm

    parameters:
      default:
        replicaCount: 1
      prod:
        replicaCount: 2

pipeline:
  image:
    ci: ./scripts/image-ci.sh
    pr: ./scripts/image-pr.sh
    cd: ./scripts/image-cd.sh

  deploy:
    default: ./scripts/deploy.sh

local:
  build:
    posix: ./scripts/local-image-build.sh
  run:
    posix: ./scripts/local-image-run.sh

service-catalog:
- name: example
  class: a_class
  plan: a_plan
  instance:
    parameters: {}
  binding:
    parameters: {}

bootstrap:
  scaffold:
    default: scaffold-instanciation.sh
```

#### features

Controls which features are enabled or disabled.

Default settings are:

```yaml
features:
  service-catalog: true
```

#### package

##### docker

```yaml
package:
  docker:
    dockerfile: <relative path to a Dockerfile (eg: docker/Dockerfile)>
```

`package.docker.dockerfile` can be overridden and a *custom* Dockerfile can be used directly in the product repository.

##### helm

```yaml
package:
  helm:
    chart: <relative path to a chart. (eg: helm/chart)>
    preprocessor: <relative path to the base dir of a chart. (eg: helm)>

    parameters:
      default:
        # common values.yaml
      prod:
        # override some values for prod
      # env:
      #   override some values for this env
```

`package.helm.chart` and `package.helm.preprocessor` can be overridden and a *custom* chart can be used directly in the product repository. **You should probably prefer a diff-patch approach, or better, to contribute upstream to the devops resource used by your product.**

Everything else in parameters will use a deep merge strategy.

`noopsctl` will create `values-<scope>.yaml` files for each environment and default parameters. Those files are stored in `./noops_workdir/helm/`.

`package.helm.preprocessor` provides the path where some helm files needs pre-processing (*eg: to replace some variables from a vault in yaml files*). This is not mandatory to use it as this is your deploy script which will do this task.

#### service-catalog

```yaml
service-catalog:
- name: example
  class: a_class
  plan: a_plan
  instance:
    parameters: {}
  binding:
    parameters: {}
```

By default, `noopsctl` will create compatible objects with [Kubernetes Service Catalog](https://svc-cat.io/) in the `{pakage.helm.chart}/templates/svcat.yaml` and binding secrets available in `./noops_workdir/helm/values-svcat.yaml`.

This implementation is compatible with [Open Service Broker API](https://www.openservicebrokerapi.org/).

#### pipeline and local

```yaml
pipeline:
  image:
    ci: ./scripts/image-ci.sh
    pr: ./scripts/image-pr.sh
    cd: ./scripts/image-cd.sh

  deploy:
    default: ./scripts/deploy.sh

local:
  build:
    posix: ./scripts/local-image-build.sh
    nt: ./scripts/local-image-build.ps1
  run:
    posix: ./scripts/local-image-run.sh
    nt: ./scripts/local-image-run.ps1
```

`noopsctl` does **NOT** define how to do a CI, CD, etc. It relies on external executable scripts or binaries.

To do so, `noopsctl` is using this mapping:

| command                                 | main script                | target                                                     |
| --------------------------------------- | -------------------------- | ---------------------------------------------------------- |
| `noopsctl -vv -p . pipeline image --ci` | image-ci.sh                | Continuous Integration                                     |
| `noopsctl -vv -p . pipeline image --pr` | image-pr.sh                | Continuous Integration for a Pull Request                  |
| `noopsctl -vv -p . pipeline image --cd` | image-cd.sh                | Prepare for deployment (eg: build and push a docker image) |
| `noopsctl -vv -p . pipeline deploy`     | deploy.sh                  | Continuous Deployment                                      |
| `noopsctl -vv -p . local build`         | local-image-build.{sh,ps1} | Build the product on a developers computer                 |
| `noopsctl -vv -p . local run`           | local-image-run.{sh,ps1}   | Run the product on a developers computer                   |

**About posix and nt:**

If the pipeline is running in a controlled context, this is not necessary the case in a local (eg: developers computer) context. The operating system is important and so `noopsctl` will run the script or binary corresponding to the local operating system category (**posix** or **nt**).

## Installation

```bash
pip3 install --user .
```

## Usage

### Main help

```bash
$ noopsctl
usage: noopsctl [-h] -p file [-c name] [-d] [-s] [-r] [-v] {pipeline,output,local} ...

NoOps translator

optional arguments:
-h, --help            show this help message and exit
-p file, --product file
                        product directory
-c name, --chart-name name
                        override chart name autodetection [helm]
-d, --dry-run         dry run
-s, --show            show noops final configuration
-r, --rm-cache        remove the workdir cache
-v                    warning (-v), info (-vv), debug (-vvv), error only if unset

main commands:
{pipeline,output,local}
```

### Continuous Integration

```bash
noopsctl -vv -p . pipeline image --ci
```

### Continuous Integration for a Pull Request

```bash
noopsctl -vv -p . pipeline image --pr
```

### Continuous Deployment

```bash
noopsctl -vv -p . pipeline image --cd
noopsctl -vv -p . pipeline deploy
```

### Build the product locally

```bash
noopsctl -vv -p . local build
```

### Run the product locally

```bash
noopsctl -vv -p . local run
```

