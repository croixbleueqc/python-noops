# noops.yaml: Reserved keys

You are free to add any extra keys to a `noops.yaml` file. But some keys are **reserved** :

- features.*

- package.docker.dockerfile *(DEPRECATED)*
- package.lib.dockerfile *(DEPRECATED)*
- package.helm.chart
- package.helm.preprocessor *(DEPRECATED)*
- package.helm.pre-processing
- package.helm.parameters
- package.helm.targets-parameters
- package.helm.definitions
- package.helm.kustomize
- package.supported
- pipeline.deploy
- pipeline.*.ci
- pipeline.*.cd
- pipeline.*.pr
- local.build.posix
- local.build.nt
- local.run.posix
- local.run.nt
- service-catalog
- white-label