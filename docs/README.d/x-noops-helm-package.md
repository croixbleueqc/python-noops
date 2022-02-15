# NoOps Helm Package [Experimental]

NoOps Helm Package is a **regular** Helm Package but with few inclusions :

- all environment presets
- profiles
- targets
- kustomize
- noops.yaml (`chart.noops.local`)

`noopsctl` can easly install this kind of package and select requested environment, profile, target, kustomization and pre-processing.

## Kind: chart.noops.local/v1alpha1

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

chart define a subset of `noops.yaml` to define how to install it (`pre-processing`) and what is supported (`supported`).

`kustomize` is not declared but if a kustomize folder exists, it will be automatically used.