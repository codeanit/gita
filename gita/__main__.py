'''
Gita manages multiple git repos. It has two functionalities

   1. display the status of multiple repos side by side
   2. delegate git commands/aliases from any working directory

Examples:
    gita ls
    gita fetch
    gita stat myrepo2
    gita super myrepo1 commit -am 'add some cool feature'
'''

import os
import argparse
import pkg_resources

from . import utils


def f_add(args: argparse.Namespace):
    utils.add_repos(args.repo)


def f_ls(args: argparse.Namespace):
    repos = utils.get_repos()
    if args.repo:  # one repo, show its path
        print(repos[args.repo])
    else:
        for line in utils.describe(repos):
            # commit message contains \n already
            print(line, end='')


def f_rm(args: argparse.Namespace):
    """
    Unregister a repo from gita
    """
    path_file = utils.get_path_fname()
    if os.path.isfile(path_file):
        repos = utils.get_repos()
        del repos[args.repo]
        with open(path_file, 'w') as f:
            f.write(os.pathsep.join(repos.values()))


def f_git_cmd(args: argparse.Namespace):
    """
    Delegate git command/alias defined in `args.cmd`
    """
    repos = utils.get_repos()
    if args.repo:  # with user specified repo(s)
        repos = {k: repos[k] for k in args.repo}
    for path in repos.values():
        utils.exec_git(path, args.cmd)


def f_super(args):
    """
    Delegate git command/alias defined in `args.man`, which may or may not
    contain repo names.
    """
    names = []
    repos = utils.get_repos()
    for i, word in enumerate(args.man):
        if word in repos:
            names.append(word)
        else:
            break
    args.cmd = args.man[i:]
    args.repo = names
    f_git_cmd(args)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog='gita',
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__)
    subparsers = p.add_subparsers(
        title='sub-commands', help='additional help with sub-command -h')

    version = pkg_resources.require('gita')[0].version
    p.add_argument(
        '-v', '--version', action='version', version=f'%(prog)s {version}')

    # bookkeeping sub-commands
    p_add = subparsers.add_parser('add', help='add repo(s)')
    p_add.add_argument('repo', nargs='+', help="add repo(s)")
    p_add.set_defaults(func=f_add)

    p_rm = subparsers.add_parser('rm', help='remove repo')
    p_rm.add_argument(
        'repo', choices=utils.get_repos(), help="remove the chosen repo")
    p_rm.set_defaults(func=f_rm)

    p_ls = subparsers.add_parser('ls', help='display summaries of all repos')
    p_ls.add_argument(
        'repo',
        nargs='?',
        choices=utils.get_repos(),
        help="show path of the chosen repo")
    p_ls.set_defaults(func=f_ls)

    # superman mode
    p_super = subparsers.add_parser(
        'super',
        help=
        'superman mode: delegate any git command/alias in specified or all repo(s).\n'
        'Examples:\n \t gita super myrepo1 commit -am "fix a bug"\n'
        '\t gita super repo1 repo2 repo3 checkout new-feature')
    p_super.add_argument(
        'man',
        nargs=argparse.REMAINDER,
        help="execute arbitrary git command/alias for specified or all repos "
        "Example: gita super myrepo1 diff --name-only --staged "
        "Another: gita super checkout master ")
    p_super.set_defaults(func=f_super)

    # sub-commands that fit boilerplate
    cmds = utils.get_cmds_from_files()
    for name, data in cmds.items():
        help = data.get('help')
        cmd = data.get('cmd') or name
        if data.get('allow_all'):
            choices = utils.get_choices()
            nargs = '*'
            help += ' for all repos or'
        else:
            choices = utils.get_repos()
            nargs = '+'
        help += ' for the chosen repo(s)'
        sp = subparsers.add_parser(name, help=help)
        sp.add_argument('repo', nargs=nargs, choices=choices, help=help)
        sp.set_defaults(func=f_git_cmd, cmd=cmd.split())

    args = p.parse_args(argv)

    if 'func' in args:
        args.func(args)
    else:
        p.print_help()  # pragma: no cover


if __name__ == '__main__':
    main()  # pragma: no cover
