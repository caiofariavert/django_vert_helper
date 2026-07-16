# django-vert-helper

Base inicial de biblioteca Django para leitura de configuracoes no `settings.py`.

## Instalacao no projeto Django

1. Adicione app em `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "vert_helper.apps.VertHelperConfig",
]
```

2. Configure via bloco unico (recomendado):

```python
VERT_HELPER = {
    "ENABLED": True,
    "API_TIMEOUT": 10,
    "SERVICE_URL": "https://api.exemplo.com",
}
```

3. Ou por chaves prefixadas (sobrescreve o bloco):

```python
VERT_HELPER_API_TIMEOUT = 15
VERT_HELPER_SERVICE_URL = "https://api.exemplo.com"
```

## Uso

```python
from vert_helper import get_vert_helper_settings

cfg = get_vert_helper_settings()

if cfg.enabled:
    print(cfg.api_timeout)
    print(cfg.service_url)
```
