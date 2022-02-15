# White-label

White-label is used to rebrand a product.

## Quick example

```yaml
features:
  white-label: true

white-label:
- rebrand: brand1
  marketer: Marketer 1 Inc
- rebrand: brand2
  marketer: Marketer 2 Inc
# ...
```

## Features

White-label is disabled by default. To enable it:

```yaml
features:
  white-label: true
```

## DevOps

White-label can be used during `noopsctl pipeline deploy` action.

A deployment will be triggered **per brand** and so the deployment script will be called multiple times (**but** one time per brand).

Additional environment variables will be exported to the deployment script:

```bash
NOOPS_WHITE_LABEL=y
NOOPS_WHITE_LABEL_REBRAND=<the brand>
NOOPS_WHITE_LABEL_MARKETER=<the company or organization behind the brand>
```

