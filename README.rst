NoOps Command line utility
==========================

noopsctl is an utility which handles noops compliant repository.

A noops compliant repository (product) exposes noops.yaml with multiple directives.
The devops part can be a remote resource with its own noops.yaml file.

noopsctl will provide an efficient way to handle this kind of repository for pipeline (CI/CD) or local build (Devs computer).

Installation
------------

.. code:: bash

    pip3 install --user .

Usage
-----

.. code:: bash

    $ noopsctl
    usage: noopsctl [-h] -p file [-c name] [-d] [-s] [-r] [-v] {pipeline,output,local} ...

    NoOps translator

    optional arguments:
    -h, --help            show this help message and exit
    -p file, --product file
                            product directory
    -c name, --chart-name name
                            override chart name autodetection [helm]
    -d, --dry-run         dry run
    -s, --show            show noops final configuration
    -r, --rm-cache        remove the workdir cache
    -v                    warning (-v), info (-vv), debug (-vvv), error only if unset

    main commands:
    {pipeline,output,local}

