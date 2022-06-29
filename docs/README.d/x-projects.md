# Projects [Experimental]

Project combine [Target](x-targets.md),  [Version](x-versions.md) and eventually parameters from a pipeline.

A subset of project is to define what should be use to deploy a product on a cluster.

That means:

- helm chart to use
- execution environment
- rebrand (white-label)
- etc

Profile class to use per version will be determined at this stage and it will be possible to test the profile class compatibility against  `package.supported.profile-classes.{class}` from [NoOps Helm Package](x-noops-helm-package.md).

## Kind

### Project

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

#### Spec

##### package

`package` key is used to declare what to install or upgrade. It is partially linked to `noops.package` in a `noops.yaml`.

`package` structure is set with:

```yaml
package:
  # install or upgrade declaration
  install:
    # name of a helm chart
    chart:
    # environment to use like dev, qa, prod, whateverYouWant
    env:
    # target is based on the TargetPlan and if this is a project deployment for an active or standby section.
    # target can be one-cluster, multi-cluster, active, standby
    # target will be used to select values files to override some settings in the helm chart
    target:
    # services-only is a boolean that will load or not a services only profile in the helm chart
    # services-only is based on the TargetPlan and if this is a project deployment for services-only section.
    services-only:
    # white-label for rebrand
    white-label:
      marketer:
      rebrand:
    # Custom global arguments that can be used to deploy the product (override settings or add new ones)
    args: []
    # envs are used to declare some external variables during an install/upgrade deployment
    envs:
      VARIABLE: value
```

##### versions

`versions` key is used to declare product versions to deploy. Please refer to [versions](./x-versions.md).

#### Improvements 

Project should be improved in the future with information relative to the project itself like:

- sccs url (git)
- owner/sla
- support email
- documentation
- service dependencies
- ...

## Plan

Plan is used to create a `noopsctl` internal `ProjectPlan`.

[Target](x-targets.md), [Cluster](x-targets.md), [Version](x-versions.md) and Project are used to create it.

This plan permit for each cluster to define a **project template**. A project template permit to create a `Project kind`. This is like a [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) with a pod template.

### Example

#### Plan for one cluster only deployment

```bash
$ noopsctl x projects plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml -v docs/examples/versions.yaml -p docs/examples/projects.yaml
```

```yaml
apiVersion: noops.local/v1alpha1
kind: ProjectPlan
metadata:
  name: myproject
  namespace: myns
spec:
  plan:
  - clusters:
    - c1
    template:
      spec:
        package:
          install:
            args:
            - --set
            - env.service_version=v10
            chart: demo
            env: prod
            envs:
              TEST: test
            services-only: false
            target: one-cluster
            white-label:
              marketer: Test Inc
              rebrand: test
        versions:
          multi:
          - app_version: sha-7c5a0d8
            dedicated-endpoints: true
            weight: 10
          - app_version: sha-8c5a0d9
            args:
            - --set
            - env.service_version=vCUSTOM
            weight: 90
  target-class: one-cluster
```

In this case, we want to deploy a product on one cluster only (`c1`), in the namespace `myns` with a base release name `myproject`.

We will use the `demo` chart in a `prod` environment with a rebrand `test` and with a global argument `--set env.service_version=v10` to be used by helm.

We will deploy multiple versions of the product (`multi`) in a canary configuration (`weight`).

For the version `sha-8c5a0d9` we will override the global argument to set `--set env.service_version=vCUSTOM` and we will create a dedicated endpoint to access it directly. So, `sha-8c5a0d9` will be available from the canary ingress entrypoint (`90%` of the time) and `sha-7c5a0d8`, the last `10%` of the time.

### Execute a plan

A `ProjectPlan` can be executed by `noopsctl`. That means that `noopsctl` will create a `Project kind` for each template and apply the change on a cluster context. `noopsctl` will rely on helm and kubecontext.

To apply a change, the previous state needs to be known. So a reconciliation needs to be done.

## Reconciliation

As multiple versions can be deployed, a reconciliation needs to be done. To do a reconciliation, it is necessary to know the previous state and the expected state.

`noopsctl` will take care to delete/create/update what is required.

`noopsctl x projects` support arguments to store a state or to read a previous state. Please use `-h` for more details. 

## Cli

```bash
# Create a project plan
$ noopsctl x projects plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml -v docs/examples/versions.yaml -p docs/examples/projects.yaml

# Create a project plan and store it (useful to use it as a previous plan later)
$ noopsctl x projects plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml -v docs/examples/versions.yaml -p docs/examples/projects.yaml -o /tmp/projectplan.yaml

# Reconciliation in selected cluster
# This apply a project kind in the current kube context
$ noopsctl x projects cluster-apply -h

# Delete everything controlled by this project in selected cluster
# This remove a project kind in the current kube context
$ noopsctl x projects cluster-delete -h

# execute a project plan (you should pass a previous plan if there is one)
# Switching automatically between all kube contexts required to apply or delete a project kind
$ noopsctl x projects apply -h
```

## NoOps Operator for Kubernetes

Reconciliation strategy and state storage is well managed by kubernetes itself. Instead of using the cli, a `Project kind` can be handle by a `NoOps Operators` inside kubernetes.

[Kubernetes Operators](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) is a way to manage custom resource definitions (CRDs) and to interact with them.

`project.noops.local/v1alpha1` will be the main resource responsible to define the deployment strategy inside the cluster. The NoOps Operator will do the **reconciliation**.

`status` field will be used to track reconciliation operations inside a `project.noops.local` CRD.

By doing so we don't need to put the deployment logic outside *(eg: from a deployment pipeline)*

`noopsctl` is set internaly as a library to permit the creation of an operator (*Not yet available*).
