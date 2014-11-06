#
#    Copyright (C) 2014 Alexandre Viau <alexandre@alexandreviau.net>
#
#    This file is part of python-pass.
#
#    python-pass is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    python-pass is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with python-pass.  If not, see <http://www.gnu.org/licenses/>.
#

import click
import os
import subprocess
import sys


@click.group()
@click.option('--PASSWORD_STORE_DIR',
              envvar='PASSWORD_STORE_DIR',
              default=os.path.join(os.getenv("HOME"), ".password-store"),
              type=click.Path(file_okay=False, resolve_path=True))
@click.pass_context
def main(ctx, password_store_dir):
    config = {}
    config['password_store_dir'] = password_store_dir

    gpg_id_file = os.path.join(password_store_dir, '.gpg-id')
    if os.path.isfile(gpg_id_file):
        config['gpg-id'] = open(gpg_id_file, 'r').read()

    ctx.obj = config


@main.command()
@click.option('--path', '-p',
              type=click.Path(file_okay=False, resolve_path=True),
              default='~/.password-store',
              help='Where to create the password store.')
@click.argument('gpg-id', type=click.STRING)
def init(path, gpg_id):
    # Create a folder at the path
    if not os.path.exists(path):
        os.makedirs(path)

    # Create .gpg_id and put the gpg id in it
    with open(os.path.join(path, '.gpg-id'), 'w') as gpg_id_file:
        gpg_id_file.write(gpg_id)


@main.command()
@click.argument('path', type=click.STRING)
@click.pass_obj
def insert(config, path):
    passfile_path = os.path.realpath(
        os.path.join(
            config['password_store_dir'],
            path + '.gpg'
        )
    )

    password = click.prompt(
        'Enter the password',
        type=str,
        confirmation_prompt=True
    )

    gpg = subprocess.Popen(
        [
            'gpg',
            '-R', config['gpg-id'],
            '--batch',
            '--no-tty',
            '-o', passfile_path,
            '-e',
        ],
        shell=False,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    gpg.stdin.write(password.encode())
    gpg.stdin.close()
    gpg.wait()

    # Check for gpg errors
    if gpg.returncode != 0:
        click.echo("GPG error:")
        click.echo(gpg.stderr.read())
        sys.exit(1)


if __name__ == '__main__':
    main()