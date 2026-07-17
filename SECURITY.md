# Security policy

## Credentials

Never report a leaked credential in a public issue. Revoke it first, then contact
the repository owner privately through the GitHub account. The repository should
contain no token, key, credential JSON, `.env` file, or signed private URL.

## Data exposure

Treat row-level training/test manifests, speaker identifiers, transcripts,
submission predictions, and raw audio as non-public unless the source owner
explicitly permits redistribution. Public bug reports should use synthetic examples.

## Supported release

Security fixes target the current default branch. Model and dataset issues may
also need to be reported to their upstream owners.

