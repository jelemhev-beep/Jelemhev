import argparse
import asyncio
import sys

from . import report, scope
from .runner import run_recon


def cmd_scope_add(args: argparse.Namespace) -> int:
    scope.add(args.domain)
    print(f"'{args.domain}' ajoute au scope autorise.")
    return 0


def cmd_scope_remove(args: argparse.Namespace) -> int:
    scope.remove(args.domain)
    print(f"'{args.domain}' retire du scope.")
    return 0


def cmd_scope_list(args: argparse.Namespace) -> int:
    domains = scope.list_scope()
    if not domains:
        print("Aucun domaine dans le scope. Ajoute-en un avec: huntkit scope add <domaine>")
        return 0
    for d in domains:
        print(d)
    return 0


def cmd_recon(args: argparse.Namespace) -> int:
    try:
        summary = asyncio.run(
            run_recon(args.domain, max_concurrency=args.concurrency, requests_per_second=args.rps)
        )
    except scope.NotInScopeError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1

    print(f"Recon terminee pour {summary['domain']}:")
    print(f"  sous-domaines trouves : {summary['subdomains_found']}")
    print(f"  hotes scannes         : {summary['hosts_scanned']}")
    print(f"  trouvailles           : {summary['findings']}")
    print("Genere le rapport avec: huntkit report", args.domain)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    text = report.generate(args.domain)
    if args.output:
        with open(args.output, "w") as f:
            f.write(text)
        print(f"Rapport ecrit dans {args.output}")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="huntkit",
        description="Automatisation de recon et scan de vulnerabilites pour bug bounty, sur cibles autorisees uniquement.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scope_parser = sub.add_parser("scope", help="Gerer le scope autorise")
    scope_sub = scope_parser.add_subparsers(dest="scope_command", required=True)

    p_add = scope_sub.add_parser("add", help="Ajouter un domaine au scope")
    p_add.add_argument("domain")
    p_add.set_defaults(func=cmd_scope_add)

    p_remove = scope_sub.add_parser("remove", help="Retirer un domaine du scope")
    p_remove.add_argument("domain")
    p_remove.set_defaults(func=cmd_scope_remove)

    p_list = scope_sub.add_parser("list", help="Lister le scope autorise")
    p_list.set_defaults(func=cmd_scope_list)

    p_recon = sub.add_parser("recon", help="Lancer la reconnaissance sur un domaine du scope")
    p_recon.add_argument("domain")
    p_recon.add_argument("--concurrency", type=int, default=10, help="Requetes concurrentes max")
    p_recon.add_argument("--rps", type=float, default=5.0, help="Requetes par seconde max")
    p_recon.set_defaults(func=cmd_recon)

    p_report = sub.add_parser("report", help="Generer le rapport Markdown d'un domaine")
    p_report.add_argument("domain")
    p_report.add_argument("-o", "--output", help="Fichier de sortie (sinon stdout)")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
