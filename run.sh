#!/bin/bash
#

RANCHER_URL="${RANCHER_URL:-"https://rancher.192.168.0.131.sslip.io"}"
RANCHER_VERSION_URL="${RANCHER_URL}/rancherversion"

TEST_LIST=(
  "harvester_e2e_tests/integrations/rancher/test_9_rancher_integration.py"
#  "harvester_e2e_tests/integrations/rancher/test_rke1.py"
  "harvester_e2e_tests/integrations/rancher/test_rke2.py"
  "harvester_e2e_tests/integrations/rancher/test_k3s.py"
# "harvester_e2e_tests/integrations/rancher/test_terraform_rancher.py"
)

K8S_LIST=(
#  "v1.27"
#  "v1.28"
#  "v1.29"
  "v1.30"
#  "v1.31"
#  "v1.32"
)

RANCHER_VERSION="$(curl -sk "${RANCHER_VERSION_URL}" | jq .Version | tr -d "\"")"

for k8s in "${K8S_LIST[@]}" ; do
  name="Test Report Rancher ${RANCHER_VERSION}xRKE2 ${k8s}"

  if [ -d "${name}" ] ; then
    save="$(mktemp -u -p . -t "${name}.save.XXXX")"
    mv "${name}" "${save}"
  fi

  yq eval -i ".k8s-version = \"$k8s\"" config.yml
  tox \
    -e py311 \
    --result-json=test_result.json -- \
      -vvl "${TEST_LIST[@]}" \
      --html="${name}/test_result.html" \
      "${@}"
done
