# bsr
rsync based binary sharing tool

# install

```bash
$ curl -s https://raw.githubusercontent.com/omochi/bsr/master/installer.bash | bash 
```

# uninstall

```bash
$ rm -rf /usr/local/bin/bsr /usr/local/lib/bsr
```

# status

show your worktree version.

```bash
$ bsr status
```

# versions

show all versions in repository.

```bash
$ bsr versions
```

# checkout

checkout specified version.
if not specified, checkout latest version.

```bash
$ bsr checkout 3
```

# push

push new version.
you need to checkout latest version before push.

```bash
$ bsr push
```

