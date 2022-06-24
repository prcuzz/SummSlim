#!/bin/sh
set -e

# first arg is `-f` or `--some-option`
if [ "${1#-}" != "$1" ]; then
        set -- apache2-foreground "$@"    # 如果第一个参数不是`-f` 或 `--some-option`，就把apache2-foreground设置为第一个参数？
fi

exec "$@"
