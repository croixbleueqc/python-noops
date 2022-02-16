# Package

`noopsctl` has built-in package support.

Supported package tools are:

- `helm`
- `docker`

In the current implementation `docker` is never called from `noopsctl` directly but as it is a common tool, we are providing facilities to declare some Dockerfiles and relative settings.

`helm` can be called directly from `noopsctl`. This is fully integrated to create packages, values and deploy them (with or without kustomize post renderer).

[TOC]

## Docker

Facilities to select the right Dockerfile to build a custom target. `docker cli` is never called from `noopsctl` but should be from your own pipeline scripts.

```yaml
package:
  docker:
    app: # this is a custom target.
      dockerfile: <relative path to a Dockerfile (eg: docker/Dockerfile)>
    # any other custom target
```

`package.docker.dockerfile` and `package.lib.dockerfile` are **deprecated** !

### Simple pipeline script example

```bash
DOCKERFILE=$(cat $NOOPS_GENERATED_JSON | jq -r .package.docker.app.dockerfile)

docker build --tag demo:latest \
-f $DOCKERFILE .
```

### Advanced example with custom keys

In this example, we will use a custom key `extraOsPkgs` to install additional packages to the base image.

#### noops.yaml

```yaml
package:
  docker:
    app:
      dockerfile: docker/Dockerfile
      extraOsPkgs: 'pkg1 pkg2'
```

#### pipeline script

```bash
DOCKERFILE=$(cat $NOOPS_GENERATED_JSON | jq -r .package.docker.app.dockerfile)
EXTRA_OS_PKGS=$(cat $NOOPS_GENERATED_JSON | jq -r .package.docker.app.extraOsPkgs)

docker build --tag demo:latest \
--build-arg EXTRA_OS_PKGS="$EXTRA_OS_PKGS" \
-f $DOCKERFILE .
```

#### Dockerfile

```dockerfile
FROM ubuntu:latest

ARG EXTRA_OS_PKGS

RUN set -e && if [ -n "$EXTRA_OS_PKGS" ]; then \
        apt-get update; \
        apt-get install -y $EXTRA_OS_PKGS; \
        rm -rf /var/lib/apt/lists/*; \
    fi
```

## Helm

Permit to control everything relative to a helm packaging and/or deployment.

### Chart

A [chart](https://helm.sh/docs/topics/charts/) is a collection of files that describe a related set of Kubernetes resources. This chart can be set locally (inside product or devops) or from a remote helm repository.

#### built-in

```yaml
package:
  helm:
    chart: # <relative path to a chart (eg: helm/chart)>
```

`helm/chart` has to exist in product or devops

#### remote

```yaml
package:
  helm:
    chart:
      name: # (eg: sonatype/nexus-iq-server)
      version: # (eg: '127.0.0')
      url:	# (eg: https://sonatype.github.io/helm3-charts/nexus-iq-server-125.0.0.tgz)
      destination: # (eg: helm/chart) - as if it is built-in
```

if `name` is set, it will have the highest priority over `url`.
if `version` is unset, the latest one will be pulled (**only if** `name` **is set**).

### Pre-processing

Sometime it is useful to run pre-processing steps before helm templating. This is the opposite target of [helm post rendering](https://helm.sh/docs/topics/advanced/#post-rendering).

```yaml
package:
  helm:
    pre-processing:
    - replace-vault-values.py # eg
```

`package.helm.preprocessor` is **deprecated** !

`pre-processing` is an ordered list of scripts to run. Those scripts have to be part of your pipeline build image. **No** scripts are embedded in a helm package **for security purpose**.

#### Create a pre-processing script

```python
"""
Example to replace a value with a Vault secret
"""
from noops.external.preprocessing import PreProcessing

class ReplaceVaultValues(PreProcessing):
    def apply(self, env, chart, values, templates, kustomize):
        # replace some values with vault secrets
        pass

ReplaceVaultValues().run()

```

#### cli compliance

```bash
Usage: replace-vault-values.py [OPTIONS] COMMAND [ARGS]...

  Pre-processing Helm files before templating

Options:
  -e, --env TEXT        environment  [required]
  -c, --chart PATH      chart path  [required]
  -f, --values PATH     values.yaml files  [required]
  -t, --template PATH   template file
  -k, --kustomize PATH  kustomize path
  -h, --help            Show this message and exit.
```

### Kustomize

[Kustomize](https://kustomize.io/) is a powerful tool for post rendering. As it is not integrated natively with helm, we provide an efficiant way to do it for you with `noopshpr` command line.

You just need to focus on :

- defining kustomize structure

  ```bash
  # eg under helm/kustomize
  base/kustomization.yaml
  $ENVIRONMENT/kustomization.yaml
  ```

- declare kustomize in `noops.yaml`

  ```yaml
  package:
    helm:
      kustomize: # <relative path to a kustomize folder (eg: helm/kustomize)>
  ```

**IMPORTANT:** kustomize folder can be set directly under the helm chart but it is preferable to move it outside. The packaging will take care to copy it inside the chart. This is easier if you want to override kustomize from a product.

### Parameters

Parameters are exactly what you will set on [values files](https://helm.sh/docs/chart_template_guide/values_files/).

Parameters are applied in this order (lower to highest priority):

- default chart values.yaml
- default
- environment

#### default

```yaml
package:
  helm:
    parameters:
      default:
        # common values.yaml
```

#### environment (env)

```yaml
package:
  helm:
    parameters:
      {env}: # eg: prod, dev, IhaveALotOfImagination, ...
        # common values.yaml for this environment
      # other environments
```

### Targets parameters

Targets parameters are applied with the highest priority. They should mainly control the behaviour of the product based on execution target.

| target        | purpose                                                      |
| ------------- | ------------------------------------------------------------ |
| one-cluster   | product will run on one cluster only                         |
| multi-cluster | product will run accross multiple clusters                   |
| active        | product will run as an active instance (active/standby strategy) |
| standby       | product instance will be in standby mode (active/standby strategy) |



```yaml
package:
  helm:
    targets-parameters:
      one-cluster:
        default:
          # common values for one-cluster deployment
       	{env}:
       	  # common values for one-cluster deployment for this environment
      multi-cluster:
        # as one-cluster but for multi-cluster deployment
      active:
        # as one-cluster but for active deployment
      standby:
        # as one-cluster but for standby deployment
```



### Definitions

NoOps defines default settings about what a NoOps Helm Package should be. To reduce opinionated position, it is possible to override those settings with `definitions` key.

By default, NoOps is using the root key `noops` in values.yaml to expose settings for profiles, targets, white-label, canary, etc.

#### targets

```yaml
package:
  helm:
    definitions:
      # Define targets based on target classes supported
      # class one-cluster uses one-cluster
      # class multi-cluster uses multi-cluster
      # class active-standby uses active,standby
      targets:
        one-cluster:
          noops:
            target: one-cluster
        multi-cluster:
          noops:
            target: multi-cluster
        active:
          noops:
            target: active
        standby:
          noops:
            target: standby
```

#### profiles

```yaml
package:
  helm:
    definitions:
      # Define profiles based on profile classes supported
      # class canary uses canary, canary-endpoints-only and canary-dedicated-endpoints
      # class blue-green uses canary class definition
      # class services-only uses services-only
      profiles:
        default: # this is a "regular" deployment
          noops:
            canary:
              enabled: false
              instances: []
            endpoints: true
            canaryEndpointsOnly: false
            servicesOnly: false
        canary: # canary deployment. No ingress endpoints
          noops:
            canary:
              enabled: true
            endpoints: false
        canary-dedicated-endpoints: # canary deployment with dedicated ingress endpoints
          noops:
            canary:
              enabled: true
        canary-endpoints-only: # canary ingress endpoints ONLY
          noops:
            canary:
              enabled: true
            canaryEndpointsOnly: true
        services-only: # services ONLY (mainly for multi-cluster solution like istio)
          noops:
            endpoints: false
            servicesOnly: true
```

#### keys

```yaml
package:
  helm:
    definitions:
      keys:
        canary: noops.canary
        white-label: noops.white-label
```



## Supported

A product can be compatible with a subset of targets and profiles.

```yaml
package:
  supported:
    target-classes:
      one-cluster: true
      multi-cluster: true
      active-standby: false
    profile-classes:
      canary: true
      services-only: true
```



## Quick examples

### Minimal

- chart exists locally
- dockerfile declared for app target

```yaml
package:
  docker:
    app:
      dockerfile: docker/Dockerfile
  
  helm:
    chart: helm/chart
```

### Kustomize a remote chart

- remote chart
- kustomize

```yaml
package:
  docker: {}
  
  helm:
    chart:
      url: https://sonatype.github.io/helm3-charts/nexus-iq-server-125.0.0.tgz
      destination: helm/chart
    
    kustomize: helm/kustomize
```

### Values with pre-processing

- chart exists locally
- values with some secrets
- pre-processing to replace secrets before templating

```yaml
package:
  docker: {}
  
  helm:
    chart: helm/chart
    
    parameters:
      default:
        password: {{vault:/my/secret/{{env:ENV}}/path/}}
    
    pre-processing:
    - replace-env-values.py
    - replace-vault-values.py
```

**Explanation:**

`noopsctl` will create values-default.yaml as set in `package.helm.parameters.default`. This file will be copied in the NoOps Helm Package if you want to build a helm package.

At this stage, there is **NO** secrets exposed by pre-processing directive and it is safe to publish the package publicly.

This is only during the deployment process that the package will be pulled and pre-processing scripts executed.

In this case `replace-env-values.py` will replace `{{env:ENV}}` with "something" and `replace-vault-values.py` will replace `{{vault:/my/secret/something/path/}}`  with a vault secret.

Of course this is an abstract example and there is no limitation on the syntax except that the content needs to be compliant with yaml specifications.

Remainder: pre-processing scripts need to be available in your pipeline environment. pre-processing scripts are **never** embedded to a NoOps Helm Package.