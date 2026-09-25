#!/bin/zsh
set -e
printf 'FEJL: Manuel deploy er deaktiveret. Merge til main og lad .github/workflows/deploy-sites.yml udgive de tre Pages-domæner.\n' >&2
exit 2
