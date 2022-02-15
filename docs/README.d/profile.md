# Profiles

By following NoOps initiative, a product depends on a scaffold and shared DevOps part.

But sometime, a product needs some small variations of the DevOps part. To simplify DevOps work and Developers upgrade, profile has been introduced to avoid scaffold and/or DevOps forks.

Profile will simply **override** some defaut settings of a product in an easy way.

As an example, if you want to move your product to a distroless packaging, it will be possible for Dev or DevOps to create a distroless profile without the need to fork something. Products sharing the same DevOps part will be able to use it or after a while DevOps can switch distroless as the default profile for every product.

## Quick example

### Product side

```yaml
profile: distroless
```

### DevOps side

```yaml
profiles:
  distroless: # custom key representing the name of the profile.
  	# everything that you can set in a noops.yaml
    package:
      docker:
        app:
          dockerfile: docker/Dockerfile.distroless
  # other profiles
```

