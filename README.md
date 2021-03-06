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

# using

- make repository directory in server.

```bash
$ ssh <remote-host>
$ mkdir <remote-path>
```

- make local worktree.

```bash
$ mkdir <local-path>
$ cd <local-path>
$ bsr init
```

- now you can use bsr subcommands.

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

# deploy

upload to any server.

```bash
$ bsr deploy <src-path> <remote-host>::<remote-path>
```

arguments are passed to rsync command.

# architecture

it users rsync `--link-dest` option.
so the same file in some versions consumes disk once.
