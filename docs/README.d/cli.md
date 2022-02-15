# Cli references

[TOC]

## Main

```bash
$ noopsctl -h
Usage: noopsctl [OPTIONS] COMMAND [ARGS]...

  noopsctl controls NoOps pipeline and package

Options:
  -p, --product path  product directory
  -r, --rm-cache      remove the workdir cache
  -v, --verbose       warning (-v), info (-vv), debug (-vvv)  [default:
                      (error)]
  -d, --dry-run       dry-run
  -h, --help          Show this message and exit.

Commands:
  local     build and run locally
  output    display few informations
  package   manage packages
  pipeline  pipeline control
  version   print the client version information
  x         experimental
```

## Output

Display effective `noops.yaml` computed from product and devops definitions.
All files path are absolute and permit to determine what will be used by `noopsctl`.

```bash
# yaml output (take care about !path)
$ noopsctl -p . output

# json output (usable with jq)
$ noopsctl -p . output --json
```

## Local

Build and run locally (eg: Developer computer) a product

### build

```bash
# help (if implemented by the build script)
$ noopsctl -p . local build -- -h

# build (without options)
$ noopsctl -p . local build
```

### run

```bash
# help (if implemented by the run script)
$ noopsctl -p . local run -- -h

# run (without options)
$ noopsctl -p . local run
```

## Pipeline

CI, CD, Deployment from a pipeline

```bash
# ci
$ noopsctl -p . pipeline ci $TARGET

# pull request
$ noopsctl -p . pipeline pr $TARGET

# cd (eg: from master branch)
$ noopsctl -p . pipeline cd $TARGET

# deploy - default
$ noopsctl -p . pipeline deploy

# deploy custom target
$ noopsctl -p . pipeline deploy $TARGET
```

## Package

Package is useful to create and managed a NoOps Helm Package. A NoOps Helm Package is a <u>regular</u> Helm Package but with an extended structure.

### create

Create a helm package (`helm package`)

```bash
$ noopsctl -p . package create -h
Usage: noopsctl package create [OPTIONS]

  create a package

Options:
  -a, --app-version TEXT  Application version
  -b, --build TEXT        Build number  [required]
  -d, --description TEXT  One line description about this new version
  -c, --chart-name TEXT   Override chart name auto detection
  -f, --values PATH       override image/tag/... in chart values.yaml
  -h, --help              Show this message and exit.
```

```bash
# -a/-d are used to set corresponding informations in Charts.yaml
# -b is a build number used to define the Charts version (do NO confuse with appVersion)
# -f is used to override at least image and tag from values.yaml. A package should deploy a specific image version.
```

### install

Install a helm package (`helm upgrade`)

```bash
$ noopsctl -p . package install helm -h
Usage: noopsctl package install helm [OPTIONS] [-- [-h] [CARGS]]

  install a NoOps helm package

  CARGS are passed directly to helm

Options:
  -n, --namespace TEXT            namespace scope
  -r, --release TEXT              release name
  -c, --chart TEXT                chart keyword or local tgz package
  -e, --env TEXT                  Environment  [default: dev]
  -z, --pre-processing-path PATH  Pre-processing scripts/binaries path
                                  [required]
  -t, --target [one-cluster|multi-cluster|active|standby]
  -p, --profile [default|canary|canary-endpoints-only|canary-dedicated-endpoints|services-only]
  -h, --help                      Show this message and exit.

```

### push

Copy a helm package to a directory and index it (`helm repo index`)

```bash
$ noopsctl -p . package push -h
Usage: noopsctl package push [OPTIONS]

  push to a repository

Options:
  -d, --directory PATH  repository directory  [required]
  -u, --url TEXT        url of chart repository  [default:
                        http://0.0.0.0:8000]
  -h, --help            Show this message and exit.
```

### serve

Start a webserver to serve packages. Do **NOT** use in production.

```bash
$ noopsctl -p . package serve -h
Usage: noopsctl package serve [OPTIONS]

  Serve packages (not recommended for production)

Options:
  -d, --directory DIRECTORY  alternate directory [default:current directory]
  -b, --bind ADDRESS         alternate bind address [default: 0.0.0.0]
  -p, --port INTEGER         alternate port  [default: 8000]
  -h, --help                 Show this message and exit.
```

## Experimental

This subcommand expose experimental features. Please refer to cli help.

```bash
$ noopsctl -p . x -h
```

