DB-API X
========

**dbapix** is a unification of, and extension to, several DB-API 2.0 drivers.

[Read the docs](https://mikeboers.github.io/dbapix/), and have fun.


Testing
-------

For first time setup (on macOS):

```
brew install postgresql
createdb dbapix

brew install mariadb
mysql.server start
sudo mysql <<EOF
    create database dbapix;
    create user dbapix@localhost identified by 'dbapix';
    grant all on dbapix.* to dbapix@localhost;
EOF
```

In each session:

```
source env.sh
```
