# Pipeline and Local

As mentionned previously, `noopsctl` does **NOT**:

- Define a CI/CD strategy
- Define how to build a product

But `noopsctl` can select and execute external scripts/binaries to do a CI, CD, local build, local run, etc.

## Quick example

```yaml
pipeline:
  {target}: # eg: image 
    ci: ./scripts/image-ci.sh
    pr: ./scripts/image-pr.sh
    cd: ./scripts/image-cd.sh

  deploy: # reserved target
    default: ./scripts/deploy.sh # default target but can be anything else
    # other deployment targets
  
  # other targets

local:
  build:
    posix: ./scripts/local-build.sh
    nt: ./scripts/local-build.ps1
  run:
    posix: ./scripts/local-run.sh
    nt: ./scripts/local-run.ps1
```

## About posix and nt

If the pipeline is running in a controlled context, this is not necessary the case in a local (eg: developers computer) context. The operating system is important and so `noopsctl` will run the script or binary corresponding to the local operating system category (**posix** or **nt**).

## Mapping

`noopsctl` is using a dynamic mapping and will expose what is supported from the command line.

| command                                  | noops.yaml key           | purpose                                                    |
| ---------------------------------------- | ------------------------ | ---------------------------------------------------------- |
| `noopsctl -p . pipeline ci {target}`     | pipeline.{target}.ci     | Continuous Integration                                     |
| `noopsctl -p . pipeline pr {target}`     | pipeline.{target}.pr     | Continuous Integration for a Pull Request                  |
| `noopsctl -p . pipeline cd {target}`     | pipeline.{target}.cd     | Prepare for deployment (eg: build and push a docker image) |
| `noopsctl -p . pipeline deploy`          | pipeline.deploy.default  | Continuous Deployment (default target)                     |
| `noopsctl -p . pipeline deploy {target}` | pipeline.deploy.{target} | Continuous Deployment                                      |
| `noopsctl -p . local build`              | local.build.{posix,nt}   | Build the product on a developers computer                 |
| `noopsctl -p . local run`                | local.run.{posix,nt}     | Run the product on a developers computer                   |

All those `noopsctl` commands can use extra arguments passed directly to the script/binary referenced by the `noops.yaml key`

```bash
noopsctl -p . [...] [-- -any -extra -arguments]
```

## Deprecated commands

| command                                   | noops.yaml key          | purpose                                                    |
| ----------------------------------------- | ----------------------- | ---------------------------------------------------------- |
| `noopsctl -p . pipeline image --ci`       | pipeline.image.ci       | Continuous Integration                                     |
| `noopsctl -p . pipeline image --pr`       | pipeline.image.pr       | Continuous Integration for a Pull Request                  |
| `noopsctl -p . pipeline image --cd`       | pipeline.image.cd       | Prepare for deployment (eg: build and push a docker image) |
| `noopsctl -p . pipeline lib --ci`         | pipeline.lib.ci         | Continuous Integration                                     |
| `noopsctl -p . pipeline lib --pr`         | pipeline.lib.pr         | Continuous Integration for a Pull Request                  |
| `noopsctl -p . pipeline lib --cd`         | pipeline.lib.cd         | Prepare for deployment (eg: build and push a docker image) |
| `noopsctl -p . pipeline deploy --default` | pipeline.deploy.default | Continuous Deployment (default target)                     |