#!/usr/bin/env python

import sys
import os
from datetime import datetime
import json
import subprocess
import getpass
from pprint import pprint
import argparse

def trace_links(path):
  path = os.path.abspath(path)
  while os.path.islink(path):
    link = os.readlink(path)
    if os.path.isabs(link):
      path = link
    else:
      path = os.path.join(os.path.dirname(path), link)
  return path

def read_file(path):
  with open(path) as f:
    return f.read()

def write_file(path, data):
  with open(path, 'w') as f:
    f.write(data)

def read_json_file(path):
  if os.path.exists(path):
    return json.loads(read_file(path))
  return {}

def write_json_file(path, value):
  write_file(path, json.dumps(value, indent=2))

def opt_to_str(value):
  if value != None:
    return str(value)
  return None

def join_lines(*lines):
  return '\n'.join(lines)

def p(line, newline=True):
  sys.stdout.write(line)
  if newline:
    sys.stdout.write('\n')

def ask(line, default=None):
  if default != None:
    line = '{} ({})'.format(line, default)
  p(line + ': ', newline=False)
  res = raw_input()
  if res == '' and default != None:
    res = default
  return res

class AppConfig:
  def __init__(self, path):
    self.path = path
    json = read_json_file(path)
    self.json = json

    self.remote_host = opt_to_str(json.get('remote_host'))
    if self.remote_host == None:
      raise Exception('remote_host is None')
    self.remote_path = opt_to_str(json.get('remote_path'))
    if self.remote_path == None:
      raise Exception('remote_path is None')

  def save(self):
    json = self.json
    json['remote_host'] = self.remote_host
    json['remote_path'] = self.remote_path
    write_json_file(self.path, json)

class AppVars:
  def __init__(self, path):
    self.path = path
    json = read_json_file(path)
    self.json = json
    self.user_name = opt_to_str(json.get('user_name'))
    self.worktree_version = opt_to_str(json.get('worktree_version'))

  def save(self):
    json = self.json
    json['user_name'] = self.user_name
    json['worktree_version'] = self.worktree_version
    write_json_file(self.path, json)


class App:
  def rsync_args(self):
    args = [
      '--recursive',
      '--links',
      '--times',
      '--omit-dir-times',
      '--no-owner',
      '--no-group',
      '--chmod=ugo+r,ug+w,Dugo+x',
      '--delete',
      '--progress',
      '--stats',
      '--verbose',
      '--human-readable',
      '--exclude=.git',
      '--exclude=.bsr'
      ]
    return args

  def load_config(self):
    if not os.path.isdir('.bsr'):
      raise Exception('.bsr directory not exists')

    self.config = AppConfig('.bsr/config')
    self.vars = AppVars('.bsr/vars')

  def user_name(self):
    if self.vars.user_name != None:
      return self.vars.user_name
    return getpass.getuser()    

  def remote_vers_dir_path(self):
    return os.path.join(self.config.remote_path, 'vers')

  def remote_ver_path(self, version_name):   
    return os.path.join(self.remote_vers_dir_path(), version_name)

  def rsync_ver_path(self, version_name):
    return '{}:{}'.format(
      self.config.remote_host,
      self.remote_ver_path(version_name))

  def exec_script_in_remote(self, script):
    script = join_lines(
      'set -ueo pipefail',
      'cd "{}"'.format(self.config.remote_path),
      script
    )

    ssh_proc = subprocess.Popen(['ssh', self.config.remote_host, 'bash -s'], 
      stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out = ssh_proc.communicate(script)[0]
    rc = ssh_proc.returncode
    if rc != 0:
      raise Exception('return code is {}'.format(rc))
    return out

  def exec_rsync(self, args, dir_args, doConfirm):
    if doConfirm:
      cmd = ['rsync'] + args + ['--dry-run'] + dir_args
      p('====[rsync dry run]====')
      p(str(cmd))
      p('====[result]====')
      subprocess.check_call(cmd)
      p('========')

      yn = ask('are you sure to continue? [y/n]')
      if yn != 'y':
        raise Exception('cancelled')

    cmd = ['rsync'] + args + dir_args
    p('====[rsync run]====')
    p(str(cmd))
    p('====[result]====')
    subprocess.check_call(cmd)
    p('========') 

  def get_version_code_str(self, version_name):
    return version_name.split('_')[0]

  def get_version_code(self, version_name):
    code_str = self.get_version_code_str(version_name)
    try:
      return int(code_str)
    except ValueError:
      return None

  def make_version_name(self, code):
    date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return '{:03d}_{}_{}'.format(code, date_str, self.user_name())

  def compare_versions(self, a, b):
    va = self.get_version_code(a)
    vb = self.get_version_code(b)
    return va - vb

  def find_version(self, versions, key):    
    key_version_code = self.get_version_code(key)
    for v in versions:
      if ( 
        v == key or
        self.get_version_code_str(v) == key or
        ( key_version_code != None and
          self.get_version_code(v) == key_version_code )
      ):
        return v
    return None

  def fetch_versions(self):
    out = self.exec_script_in_remote(join_lines( 
      'if [[ ! -d vers ]] ; then exit ; fi',
      'ls vers'
    ))
    out_lines = out.split('\n')
    def out_lines_filter(x):
      return self.get_version_code(x) != None
    vers = filter(out_lines_filter, out_lines)
    vers = sorted(vers, self.compare_versions)
    return vers

  def run(self, args):
    self.app_path = os.path.dirname(os.path.dirname(trace_links(__file__)))

    if len(args) < 2:
      raise Exception('subcommand not specified')

    subcommand = args[1]
    subcommand_args = args[2:]

    if subcommand != 'init':
      self.load_config()

    method_name = 'run_' + subcommand
    method = getattr(self, method_name, None)
    if method == None:
      raise Exception('subcommand {} not exists'.format(subcommand))
    method(subcommand_args)

  def run_init(self, args):
    if os.path.isdir('.bsr'):
      raise Exception('already inited')

    remote_host = ask('remote host?')
    remote_path = ask('remote path?')
    user_name = ask('user name?', default=getpass.getuser())

    os.mkdir('.bsr')
    write_file('.gitignore', join_lines(
      '/*',
      '!/.bsr',
      ''))
    write_file('.bsr/.gitignore', join_lines(
      '/*',
      '!/.gitignore',
      '!/config',
      ''))
    write_json_file('.bsr/config', {
      'remote_host': remote_host,
      'remote_path': remote_path  
      })
    write_json_file('.bsr/vars', {
      'user_name': user_name  
      })

  def run_status(self, args):
    p('worktree version: {}'.format(self.vars.worktree_version))

  def run_versions(self, args):
    vers = self.fetch_versions()
    if len(vers) == 0:
      p('there are no versions')
      return
    for v in vers:
      p(v)

  def run_checkout(self, args):
    argparser = argparse.ArgumentParser(prog='bsr checkout')
    argparser.add_argument(
      '-f', '--force', action='store_true',
      help='suppress confirmation prompt'
    )
    argparser.add_argument(
      'ver_key', nargs='?', default=None,
      help='checkout version number or name'
    )
    params = argparser.parse_args(args)

    vers = self.fetch_versions()
    if len(vers) == 0:
      raise Exception('there are no versions')
    if params.ver_key != None:
      ver = self.find_version(vers, params.ver_key)
      if ver == None:
        raise Exception('version {} not found'.format(params.ver_key))
    else:
      ver = vers[-1]

    self.exec_rsync(self.rsync_args(), [
      self.rsync_ver_path(ver) + '/', '.'
    ], not params.force)
    self.vars.worktree_version = ver
    self.vars.save()

  def run_push(self, args):
    vers = self.fetch_versions()
    if len(vers) > 0:
      latest_ver = vers[-1]
      if latest_ver != self.vars.worktree_version:
        raise Exception('checkout latest version ({}) before push'.format(latest_ver))
      new_ver = self.make_version_name(self.get_version_code(latest_ver) + 1)
    else:
      new_ver = self.make_version_name(0)
      latest_ver = None
      self.exec_script_in_remote('\n'.join([
        'mkdir -p "{}"'.format(self.remote_vers_dir_path())
      ]))

    rsync_args = self.rsync_args()
    if latest_ver != None:
      rsync_args += [
        '--link-dest=../{}'.format(latest_ver)
      ]

    self.exec_rsync(rsync_args, [
      './', self.rsync_ver_path(new_ver)
    ], True)
    self.vars.worktree_version = new_ver
    self.vars.save()

  def run_deploy(self, args):
    if len(args) < 1:
      raise Exception('src path not specified')
    if len(args) < 2:
      raise Exception('dest path not specified')
    rsync_args = self.rsync_args()
    self.exec_rsync(rsync_args, args[0:2], True)

App().run(sys.argv)
