# Helm chart for pycsw services

Debug with:

```bash
helm install --dry-run --debug pycsw .
```
Test template rendering with:

```bash
helm template --debug .
```

Deploy with:

```bash
helm install pycsw .
```

The server should then be made available at the host/port specified by
`minikube service pycsw --url`.
