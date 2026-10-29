ssh vezuroll "docker exec -i foodtech-backend python -c 'import urllib.request; print(urllib.request.urlopen(\"http://localhost:8000/api/v1/vk/connections/1/diagnostics\").read().decode())'"
