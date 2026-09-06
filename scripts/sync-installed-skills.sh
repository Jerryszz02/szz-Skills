#!/bin/sh

set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
install_root=${1:-${SZZ_SKILLS_INSTALL_ROOT:-$HOME/.agents/skills}}

mkdir -p "$install_root"

synced=0
for skill_dir in "$repo_root"/*; do
    if [ ! -f "$skill_dir/SKILL.md" ]; then
        continue
    fi

    skill_name=${skill_dir##*/}
    destination="$install_root/$skill_name"
    mkdir -p "$destination"
    rsync -a --delete --exclude='.DS_Store' "$skill_dir/" "$destination/"
    printf 'Synced %s -> %s\n' "$skill_name" "$destination"
    synced=$((synced + 1))
done

if [ "$synced" -eq 0 ]; then
    printf 'No repository skills found under %s\n' "$repo_root"
fi
