# JSON Schema for noops.yaml

`noopsctl` has built-in reference JSON Schema to validate a `noops-generated.json` file.

The schema validation will only occurs during the workflow cache creation ([Connecting Product and DevOps](workflow.md)).

The schema file name is `noops.schema.yaml`. It is located at the same level than `noops.yaml` in the product and/or DevOps repositories.

`noopsctl` will load the schema with the highest priority to validate the `noops-generated.json` file from the `noops_workdir`.

| schema location                                              | Priority order   |
| ------------------------------------------------------------ | ---------------- |
| `noops.schema.yaml` in the product repository                | Highest priority |
| `noops.schema.yaml` in the DevOps repository (or local to the product) |                  |
| `noops.schema.yaml` built in the `noopsctl`                  | Lower priority   |

## Override the schema

The built-in schema is covering all regular features but it will not validate the content of few keys :

- `package.helm.parameters`
- `package.helm.targets-parameters`
- `package.helm.definitions`
- your custom keys

The reason behind is that those key/values will depend on what is supported by the product and DevOps part. As you are owner of them, this is up to you to create the schema to validate those values.

So if you want more control on the validation, you will need to duplicate the built-in schema and adapt it in the DevOps part (preferred) or in the Product part (override).

You can use all JSON Schema features to do it (move the schema to a web server, use `$ref`, etc). `noopsctl` use [python-jsonschema](https://python-jsonschema.readthedocs.io/en/stable/).

## Built-in schema

Use `noopsctl` to get the built-in JSON Schema.

```bash
# standard output
$ noopsctl assist jsonschema

# copy in a file
$ noopsctl assist jsonschema -o noops.schema.yaml
```

