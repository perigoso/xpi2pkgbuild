#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Rafael Silva
#
# SPDX-License-Identifier: MIT

import re
import argparse
import requests

MOZ_PRODUCTION_API = "https://addons.mozilla.org/api/v5/"
ADDON_API_PATH = "addons/addon/"

DEFAULT_PKGNAME = "firefox-extension-{slug}-xpi"

PROGNAME = "xpi2pkgbuild"


def gen_pkgbuild(extension_data, pkgname, maintainer):
    name = extension_data["slug"]

    version = extension_data["current_version"]["version"]

    source_file_id = extension_data["current_version"]["file"]["id"]

    source = extension_data["current_version"]["file"]["url"]
    source = re.sub(str(source_file_id), "${_source_file_id}", source)
    source = re.sub(str(version), "${pkgver}", source)

    sum = extension_data["current_version"]["file"]["hash"]
    sum_type, sum_value = sum.split(":")

    license = extension_data["current_version"]["license"]["slug"]
    if extension_data["current_version"]["license"]["is_custom"] is True:
        license = f"custom:{license}"

    pkgbuild_str = ""

    pkgbuild_str += f"# This file was generated by {PROGNAME}\n"
    if maintainer is not None:
        pkgbuild_str += f"# Maintainer: {maintainer}\n"

    pkgbuild_str += "\n"

    pkgbuild_str += f"pkgname='{pkgname.format(slug=name)}'\n"
    pkgbuild_str += f"pkgver={version}\n"
    pkgbuild_str += f"pkgrel=1\n"
    pkgbuild_str += f"pkgdesc='{extension_data['summary']['en-US']}'\n"
    pkgbuild_str += f"arch=('any')\n"
    pkgbuild_str += f"url='{extension_data['homepage']['url']['en-US']}'\n"
    pkgbuild_str += f"license=('{license}')\n"

    pkgbuild_str += f"depends=('firefox')\n"

    pkgbuild_str += f"_source_file_id={source_file_id}\n"
    pkgbuild_str += f"source=('{name}.xpi'::\"{source}\")\n"
    pkgbuild_str += f"noextract=('{name}.xpi')\n"
    pkgbuild_str += f"{sum_type}sums=('{sum_value}')\n"

    pkgbuild_str += "\n"

    pkgbuild_str += "package() {\n"
    pkgbuild_str += f"  install -Dm644 '{name}.xpi' \"${{pkgdir}}/usr/lib/firefox/browser/extensions/{name}.xpi\"\n"
    pkgbuild_str += "}\n"

    pkgbuild_str += "\n"

    return pkgbuild_str


def main():
    parser = argparse.ArgumentParser(
        description="PKGBUILD generator for Firefox extensions",
        prog=PROGNAME,
        usage="%(prog)s [options] id",
    )
    parser.add_argument("--output", "-o", type=str, help="File to output to (default: stdout)")
    parser.add_argument(
        "--pkgname",
        "-n",
        type=str,
        default=DEFAULT_PKGNAME,
        help="Name to use in pkgname, use {slug} as a placeholder for extension slug (default: %(default)s)",
    )
    parser.add_argument(
        "--maintainer",
        "-m",
        type=str,
        help="Maintainer to add as comment",
    )
    parser.add_argument(
        "--api",
        type=str,
        default=MOZ_PRODUCTION_API,
        help="API URL to use (default: %(default)s)",
    )
    parser.add_argument("id", type=str, help="Extension identifier (int:id|string:slug|string:guid)")

    args = parser.parse_args()

    url = requests.compat.urljoin(args.api, ADDON_API_PATH)
    url = requests.compat.urljoin(url, args.id)

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to get addon data, reason: {response.status_code} - {response.reason}")
        exit(1)

    extension_data = response.json()
    pkgbuild = gen_pkgbuild(extension_data, args.pkgname, args.maintainer)

    if args.output is not None:
        with open(args.output, "w") as f:
            f.write(pkgbuild)
    else:
        print(pkgbuild)


if __name__ == "__main__":
    main()
