# Service Catalog

Service Catalog is useful to provision external services (eg: storage, database, vault, ...).

By relying on it, developers can focus on product code and declare required services in an efficient way.

Of course, service availables will depend of your infrastructure.

## Quick example

I'm coding my product and I need a dedicated redis instance and to have access in read only to the table T of the database D during runtime.

You will be able to declare it (this is an abstract example):

```yaml
features:
  service-catalog: true

service-catalog:
# redis dedicated instance
- name: redis
  class: redis-instance
  plan: dedicated
# read-only to database D for table T
- name: database
  class: databases
  plan: existing
  permissions:
  - database: D
    tables:
    - T
    access: read-only
```

`noopsctl` will take care to translate service catalog requests to something compatible with your own infrastructure.

At runtime, all access will be created and exposed to your product. If the product or a service is removed, access will be automatically removed.

## Features

Service-Catalog is enabled by default but can be controlled by an associated feature:

```yaml
features:
  service-catalog: true
```

## DevOps

By default, `noopsctl` will create objects in the `{pakage.helm.chart}/templates/svcat.yaml` and binding secrets available in `./noops_workdir/helm/values-svcat.yaml`.

### Open Service Broker

By default, `noopsctl` will create compatible objects with [Kubernetes Service Catalog](https://svc-cat.io/).

This implementation is compatible with [Open Service Broker API](https://www.openservicebrokerapi.org/).

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

### Custom (Operator, Open Service Broker, ...)

`noopsctl` can handle any kind of service by using external service catalog processing scripts/binaries.

```yaml
service-catalog:
- name: example
  class: a_class
  plan: a_plan
  # anything else that you needs
```

#### Handler

Handler is a processing scripts/binaries that will read a `service request` (an entry in service-catalog) and provide an `object list`.

The processing directory is declared with an environment variable:

```bash
# declare service catalog directory (before invoking noopsctl)
NOOPS_SVCAT_PROCESSING=/path/to/service-catalog-processing
```

In the processing directory, you can set all your custom scripts with the structure `/path/to/service-catalog-processing/class/plan` (eg: /processing/**a_class/a_plan**).

`plan` script has to be executable and has to define those options:

```bash
Usage: <plan> [OPTIONS] COMMAND [ARGS]...

  Create objects for <class>/<plan>

Options:
  -n, --name TEXT     metadata.name used  [required]
  -r, --request PATH  service request (yaml)  [required]
  -o, --objects PATH  service catalog objects (yaml)  [required]
  -h, --help          Show this message and exit.
```

A processing script will read a yaml service request (**-r**), create an object **list** (for an Operator, Service Catalog etc) without metadata and write them as a yaml file (**-o**) 

Handler implementation example:

```python
from noops.external.processing import Processing

class ProcessingUnittest(Processing):
    """Unittest processing"""
    def convert(self, service_request: dict, name: str) -> List[dict]:
        """Convert a service requests to an object list"""
        return [
            {
                "apiVersion": "unittest.local/v1",
                "kind": "Test",
                "spec": {
                    "key": service_request.get("key")
                }
            }
        ]

ProcessingUnittest().run()

```

