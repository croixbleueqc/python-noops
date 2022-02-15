# Targets [Experimental]

Target defines a structure to declare what a product needs, to select which servers/clusters will be used to run it.

A workload should define what it needs like:

- a GPGPU
- ODA access with low latency
- ODA access with preferred low latency (so high latency will be fine too)
- ...

In the same time, target permits to define in which way, a product will run :

- One cluster only
- HA (multi-cluster)
- Active (from active/standby strategy)
- Standby (from active/standby strategy)
- Service only (to support communication in the istio mesh from a cluster where the workload is not running)

## Kind

### Cluster

Cluster is not yet set as a kind.

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

### clusterAffinity

Similar to [podAffinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#an-example-of-a-pod-that-uses-pod-affinity) with only **requiredDuringSchedulingIgnoredDuringExecution** support.
clusterAffinity will permit to select clusters to use based on some expressions (labels filtering)

```yaml
# Example
clusterAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    clusterSelectorTerms:
    - matchExpressions: # service active with low latency
      - key: service/status
        operator: In
        values:
        - active
      - key: service/latency
        operator: In
        values:
        - low
    - matchExpressions: # service active whatever the latency
      - key: service/status
        operator: In
        values:
        - active
```



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

##### Restrictions

- clusterCount is a special key that permit to set an integer (number of clusters to use) or a directive (All, Remaining)
- active has to be greater than one (1)

## Plan

Target and cluster are used to create a `noopsctl` internal TargetPlan.

This plan will define which target class will be used (one-cluster, multi-cluster, active-standby).
Target class needs to be supported by the [NoOps Helm Package](x-noops-helm-package.md) as declared by `package.supported.target-classes.{class}`.

## Cli

```bash
# Example
$ noopsctl x targets plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml
$ noopsctl x targets plan -c docs/examples/clusters.yaml -t docs/examples/targets.yaml -o /tmp/targetplan.yaml
```

