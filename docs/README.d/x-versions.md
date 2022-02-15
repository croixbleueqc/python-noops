# Versions [Experimental]

Versions define a structure to declare product versions to deploy (once deployed, a product instance will be called a workload).

Those deployments can use different strategies:

- **Recreate**
  This update strategy will stop a workload and replace it with a new one. There is a downtime.
- **Rolling update**
  This update strategy will start a new workload and once it is ready, the old one will be removed. There is **no** downtime.
- **Canary**
  This update strategy will permit to execute different versions of a  workload in the same time and to load balance traffic between them. Most of the time we will use weight to redirect a consumer on a version or  another *(eg: 90% traffic on current version, 10% traffic on the new version for test purpose)*
- **Parallel versions**
  Capacity to run multiple versions of a workload in the same time. Every version will have a dedicated endpoint. Do **not** confuse with canary deployment.
  The main value is to remove the rigid notion of: one environment for one workload.
  As an example, we can have a QA for a specific feature and in the  same time a QA for a security fix that need to go on production as soon  as possible with both of them in the QA environment.
  An other example can be to create an ephemeral environment for end to end tests without impacting current developments or on-going QA  features.
  Of course this is not strictly available for a QA and can be used for any environments *(eg: dev, qa, acceptation, production, pre-production, ...)*.

## Kind

```yaml
apiVersion: noops.local/v1alpha1
kind: Version
metadata:
  name: demo
spec:
  one: # Only one version at a time
    app_version: sha-7c5a0d8

  multi: # Multiple versions + Canary support + Dedicated endpoints support
  - app_version: sha-7c5a0d8
    weight: 10
    dedicated-endpoints: true # default to false when canary is used
  - app_version: sha-8c5a0d9
    weight: 90
    args: # custom arguments for this version
    - --set
    - env.service_version=vCUSTOM
  - app_version: sha-8c5a0d9
    # version: 10.0.0  # optional
    # build: 30        # optional
```

**Restrictions**

- one and multi can be used together **ONLY** if Canary is not used. The purpose is to avoid collision on endpoints.
- sum(weight) **has to** equal 100
- AppVersion (`app_version`) is a mandatory field. It is **not** possible to deploy <u>two identical AppVersion</u>.

## Cli

```bash
$ noopsctl x versions verify -k docs/examples/versions.yaml
```

