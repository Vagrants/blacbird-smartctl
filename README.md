blackbird-smartctl
===============

[![Build Status](https://travis-ci.org/Vagrants/blackbird-smartctl.png?branch=development)](https://travis-ci.org/Vagrants/blackbird-smartctl)

get disk information of S.M.A.R.T using 'smartctl'

## Install

You can install by pip.

```
$ pip install git+https://github.com/Vagrants/blackbird-smartctl.git
```

Or you can also install rpm package from [blackbird repository](https://github.com/Vagrants/blackbird/blob/master/README.md).

```
$ sudo yum install blackbird-smartctl --enablerepo=blackbird
```

## notice

You need `/usr/sbin/smartctl` for `blackbird-smartctl`.  
And `blackbird` needs root privilege for executing `/usr/sbin/smartctl`.  
So you should add bbd entry in the sudoers flie like this.

```
# /etc/sudoers.d/bbd
bbd ALL=(ALL) NOPASSWD:/usr/sbin/smartctl
Defaults:bbd !requiretty
```
