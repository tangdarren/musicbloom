"""Azure DevOps API schemas."""

from musicbloom.models.devops import DevOpsRunsSnapshot, DevOpsStatusSnapshot

DevOpsStatusResponse = DevOpsStatusSnapshot
DevOpsRunsResponse = DevOpsRunsSnapshot
