# ARTEMiS Production mode
ARTEMiS is designed to run in one of two ways. Developmen/local mode, which assumes you're just trying to set up something to save your scores and make the games work, and have patched your games to disable SSL and cert checks and encryption and the like, and production mode. In production mode, artemis assumes you have a proxy server, such as nginx or apache, standing in front of artemis doing HTTPS and port management. This document will cover how to properly set up a production instance of ARTEMiS.

## ARTEMiS configuration
Step 1 is to edit your artemis configuration. Some recomended changes:
### `server`
- `listen_address` -> `127.0.0.1`
- `is_develop` -> `False`
- `is_using_proxy` -> `True`
- `port` -> The port nginx will send proxied requests to. If you're using the example config, set this to 8080.
- `proxy_port` -> The port your proxy will be accepting title server connections on. If you're using the example config, set this to 80.
- `proxy_port_ssl` -> The port your proxy will be accepting secure title server connections on. If you're using the example config, set this to 443.
- `allow_unregistered_serials` -> `False`
### `billing`
- `standalone` -> `False`
### `allnet`
- `standalone` -> `False`
### `frontend`
- `enable` -> `True` if you want the frontend
- `port` -> `8090` if you're using the default nginx config, otherwise whatever port your proxy will be sending requests to
### `aimedb`
- `listen_address` -> `0.0.0.0` unless you're proxying aimedb requests (not recomended at this time), in which case, leave this option unchanged

If you plan to serve artemis behind a VPN, these additional settings are also recomended
- `check_arcade_ip` -> `True`
- `strict_ip_checking` -> `True`

## Nginx Configuration
For most cases, the config in `example_config` will suffice. It makes the following assumptions
- ARTEMiS is running on port 8080
- Billing is set to not be standalone
- You're not using cloudflare in front of your frontend

If this describes you, your only configuration needs are to edit the `server_name` and `certificate_*` directives. Otherwise, please see nginx configuration documentation to configure it to best suit your setup.

## Standalone e-amusement service

When `eamuse.enable` and `eamuse.standalone` are enabled, Artemis listens on
`eamuse.port` (5730 by default). A public HTTPS hostname can proxy to that port:

```nginx
server {
    listen 443 ssl;
    server_name eamuse.example.com;

    ssl_certificate /etc/letsencrypt/live/eamuse.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/eamuse.example.com/privkey.pem;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://127.0.0.1:5730;
    }
}
```

Set Bemanitools' `eamuse.server` to the public hostname, for example
`https://eamuse.example.com`, not the private port.
