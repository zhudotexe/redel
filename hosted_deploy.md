# ReDel Hosted (EMNLP Demo)

These are my notes for how to deploy the hosted version. The hosted version runs `server.py` with browsing.

## Changes from main

- viz hits `https://redel-demo.zhu.codes/` as API base instead of 127.0.0.1
- `experiments` is gitignored

## Deploy process

- build viz
- download experiment files

```shell
$ ssh arborea
$ cd redel-demo.zhu.codes
$ git pull
# viz
$ pushd viz
$ npm run build
$ popd
# service
$ systemctl restart redel-demo.zhu.codes
```

## Other infrastructure notes

- arborea: nginx target file, uvicorn service
- cf: DNS
