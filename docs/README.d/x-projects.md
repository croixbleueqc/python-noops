# Projects [Experimental]

Project combine [Target](x-targets.md),  [Version](x-versions.md) and eventually parameters from a pipeline.

Profile class to use per version will be determined at this stage and it will be possible to test the profile class compatibility against  `package.supported.profile-classes.{class}` from [NoOps Helm Package](x-noops-helm-package.md).

## Kind

```yaml
apiVersion: noops.local/v1alpha1
kind: Project
metadata:
    namespace: ns
    name: exp
spec:
    package:
        install:
            chart: # chart name                     => from pipeline
            env: # dev, qa, prod, ...               => from pipeline
            target: # one-cluster, multi-cluster, active, standby => from TargetPlan
            services-only: # true or false          => from TargetPlan
            white-label:
              marketer: # Marketer Inc              => from pipeline
              rebrand:  # rebrand                   => from pipeline
            args: [] # list of additional arguments => from pipeline
            envs: # Environment variables to use    => from pipeline
                VARIABLE: <value>
    versions:
        # spec from Version.noops.local/v1alpha1    => from Version
```

## Improvements 

Project should be improved in the future with information relative to the project itself like:

- sccs url (git)
- owner/sla
- support email
- documentation
- service dependencies
- ...

## Plan

Target, cluster, version and project are used to create a `noopsctl` internal ProjectPlan.

This project plan defines all what is required to deploy a product and on which cluster. The project plan permit to create a `Project Kind` used to deploy products on a specific cluster.

## Reconciliation

As multiple versions can be deployed, a reconciliation needs to be done. To do a reconciliation, it is necessary to know the previous state and the expected state.

`noopsctl` will take care to delete/create/update what is required.

## Cli

```bash
# Create a project plan
$ noopsctl x projects plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml -v docs/examples/versions.yaml -p docs/examples/projects.yaml

# Create a project plan and store it
$ noopsctl x projects plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml -v docs/examples/versions.yaml -p docs/examples/projects.yaml -o /tmp/projectplan.yaml

# Reconciliation in selected cluster
$ noopsctl x projects cluster-apply -h

# Delete everything controlled by this project in selected cluster
$ noopsctl x projects cluster-delete -h

# execute a project plan
$ noopsctl x projects apply -h
```

## NoOps Operator for Kubernetes

`Project` can be handle by `noopsctl` or `NoOps Operators` inside kubernetes

[Kubernetes Operators](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) is a way to manage custom resource definitions (CRDs) and to interact with them.

`project.noops.local/v1alpha1` will be the main resource responsible to define the deployment strategy inside the cluster. The NoOps Operator will do the **reconciliation**.

`status` field will be used to track reconciliation operations inside a `project.noops.local` CRD.

By doing so we don't need to put the deployment logic outside *(eg: from a deployment pipeline)*
