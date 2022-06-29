# Targets [Experimental]

Target is used to declare on which clusters a product/workload can run and in which way (`one cluster only`, `multi-cluster`, `services-only`, etc).

This is **not** a direct declaration like **"run on cluster 1 and 3"**.

The product will declare some conditions (`with labels`) and clusters will expose some possibilities (`with labels`).

A workload can define some conditions like:

- a GPGPU
- service access with low latency
- service access with preferred low latency (so high latency will be fine too)
- ...

In the same time, target permits to define in which way, a product will run :

- One cluster only
- HA (multi-cluster)
- Active (from active/standby strategy)
- Standby (from active/standby strategy)
- Service only (to support communication in the istio mesh from a cluster where the workload is not running)

## Kinds

### Cluster

IMPORTANT: Cluster is not yet set as a kind and should be rewritten.

```yaml
# Example
- name: c1   # cluster name
  labels:    # cluster labels
    service/status: active
    service/latency: low
- name: c2
  labels:
    service/status: active
    service/latency: low
- name: c3
  labels:
    service/status: active
    service/latency: high
- name: c4
  labels:
    service/status: standby
    service/latency: low
```

This is a list of cluster (`name`) where `labels` are set to declare all capabilities of a cluster. Later, we will use those values to select compatible clusters for a workload.

### Target

```yaml
apiVersion: noops.local/v1alpha1
kind: Target
metadata:
    name: exp
spec:
    active:
        clusterAffinity: # ...
        clusterCount: # 1..N|All

    standby:
        clusterAffinity: # ...
        clusterCount: # 0..N|Remaining

    service-only:
        clusterAffinity: # ...
        clusterCount: # 0..N|Remaining
```

#### spec

##### active

`active` key is used to deploy and run a product.

`active` structure is set with:

```yaml
active:
  # please read dedicated chapter on clusterAffinity
  clusterAffinity:
  # should be 1 or more. This is the number of clusters where the product will run. If set to 'All', the product will run on all compatible clusters.
  clusterCount: 
```

##### standby

`standby` key is used to deploy a product and to optionnaly run it (but in a standby mode). The product will just be available to take the lead on active one when required.

Switching strategy between standby and active mode is not managed by `noopsctl` and this is up to you to set it.

`standby` structure is set with:

```yaml
standby:
  # please read dedicated chapter on clusterAffinity
  clusterAffinity:
  # should be 0 or more. If set to 'Remaining', the product will be deployed on all compatible clusters where an instance is not 'active'
  clusterCount: 
```

##### service-only

`service-only` key is used to deploy services involved in your product. This is mandatory to declare [DNS in kubernetes when you are using multiple clusters with Istio Service Mesh](https://istio.io/latest/docs/ops/deployment/deployment-models/#dns-with-multiple-clusters) and if you need to contact a service that is running outside of a cluster but inside the mesh.

The structure is the same than `standby` one.

#### clusterAffinity spec

clusterAffinity will permit to select clusters to use based on some expressions (labels filtering).

The product is responsible to define what is needed to run it.

The DevOps team is responsible to publish and document which labels can be used to target clusters.

`clusterAffinity` is similar to [podAffinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#an-example-of-a-pod-that-uses-pod-affinity) with only **requiredDuringSchedulingIgnoredDuringExecution** support.

```yaml
# Example
clusterAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    clusterSelectorTerms: # list of match expression (OR)
    - matchExpressions: # service active with low latency (AND)
      - key: service/status
        operator: In
        values:
        - active
      - key: service/latency
        operator: In
        values:
        - low
    - matchExpressions: # service active whatever the latency (AND)
      - key: service/status
        operator: In
        values:
        - active
```

#### Restrictions

- `clusterCount` is a special key that permit to set an integer (number of clusters to use) or a directive (All, Remaining)
- `active` has to be greater than one (1)

## Plan

Plan is used to create a `noopsctl` internal `TargetPlan`.

This plan permit to :

- determine the list of clusters to use respectively for `action`, `standby` and `services-only`
- target class for the product (`one-cluster`, `multi-cluster`, `active-standby`)
- if we can fulfill the request (in other word, can we run the product on our infrastructure based on it requirements)


Target class needs to be supported by the [NoOps Helm Package](x-noops-helm-package.md) as declared by `package.supported.target-classes.{class}`.

### Example

#### Deployment in one cluster only

```bash
$ noopsctl x targets plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml
```

```yaml
active:
- c1
services_only: []
standby: []
target_class: one-cluster
```

In this case, the plan has selected cluster named `c1` to deploy the product.

As we selected only one cluster (*clusterCount: 1*), the target class will be `one-cluster`.

So the deployment process can apply custom configuration to the product because it is aware that the product will run on one cluster only. As an example, it can decide to run 2 replicaCount. In a target class of `multi-cluster` it can have decided to run only 1 replicaCount per cluster.

So, `noopsctl` will just provide some context to the deployment process. It is up to the deployment process to determine how to setup the product.

## Cli

```bash
# Output the plan on the console
$ noopsctl x targets plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml

# Create a plan file
$ noopsctl x targets plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml -o /tmp/targetplan.yaml
```

