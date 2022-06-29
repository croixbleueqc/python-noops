# NoOps Helm Package

NoOps Helm Package is a **regular** Helm Package but with few inclusions :

- all environment presets
  (from `package.helm.parameters` in `noops.yaml`)
- profiles
  (from `package.helm.definitions.profiles` in `noops.yaml` or `noopsctl` built-in)
- targets
  (from `package.helm.definitions.targets` in `noops.yaml` or `noopsctl` built-in)
- kustomize
  (folder content referenced by `package.helm.kustomize` in `noops.yaml`)
- noops.yaml (`Chart kind`)

`noopsctl` can easly install this kind of package and select requested environment, profile, target, kustomization and pre-processing.

A NoOps Helm Package is a standalone package to deploy a specific product version.

## Kind

### Chart

```yaml
apiVersion: noops.local/v1alpha1
kind: Chart
spec:
  package:
    helm:
      pre-processing: []
    supported:
      profile-classes:
        canary: true
        services-only: true
      target-classes:
        active-standby: true
        multi-cluster: true
        one-cluster: true

```

chart set a subset of `noops.yaml` to define how to install it (`pre-processing`) and what is supported (`supported`).

`kustomize` is not declared but if a kustomize folder exists, it will be automatically used.

## Cli

```bash
PRODUCT=/product/path

# create a NoOps Helm Package (help)
$ noopsctl -p $PRODUCT package create -h
  
# install a NoOps Helm Package (help)
$ noopsctl -p $PRODUCT package install helm -h
  
# publish a NoOps Helm Package to a local helm repository (help)
$ noopsctl -p $PRODUCT package push -h
```

