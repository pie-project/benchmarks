set -u
BIN=$1
OUT=$2
REPOS=$3
HERE=$(cd "$(dirname "$0")" && pwd)
CHECK="python3 -m unittest -q"
mkdir -p "$OUT" "$REPOS"

passes() {
    local tree
    tree=$(ls -d "$REPOS/$1"/.etude/army/*/"$2" 2>/dev/null | head -1)
    if [ -z "$tree" ]; then echo "no $2 tree"; return; fi
    (cd "$tree" && python3 -m unittest -v 2>&1) | grep -c ' \.\.\. ok$'
}

scenario() {
    local name=$1 limit=$2 start status
    shift 2
    python3 "$HERE/fixture.py" "${name%%-*}" "$REPOS/$name"
    start=$(date +%s)
    (cd "$REPOS/$name" && perl -e 'alarm shift; exec @ARGV' "$limit" "$BIN" "$@") > "$OUT/$name.txt" 2>&1
    status=$?
    echo "exit $status after $(( $(date +%s) - start )) s" >> "$OUT/$name.txt"
    pkill -f "$ETUDE_AGENT_PATTERN" || true
    sleep 3
    mkdir -p "$OUT/$name-logs"
    rsync -a --exclude 'w*/' --exclude 'merged/' --exclude 'agent/' --include '*/' --include '*.log' --exclude '*' "$REPOS/$name/.etude/" "$OUT/$name-logs/" 2>/dev/null || true
    echo "::group::$name"
    cat "$OUT/$name.txt"
    echo "::endgroup::"
}

scenario median 1800 --check "$CHECK" "The test suite fails. Find and fix the bug in stats.py so every test passes. Do not change the tests."
scenario best 1800 --mode best --n 3 --check "$CHECK" "The test suite fails. Find and fix the bug in stats.py so every test passes. Do not change the tests."
scenario escalate 3600 --escalate-after 30 --check "$CHECK" "Implement every function in the units package as its docstring says. Do not change the tests."
scenario library-team 5400 --keep --check "$CHECK" "Implement every function in the geometry package as its docstring says so all tests pass. Do not change the tests."
echo "library-team passing tests: $(passes library-team merged)/64" | tee -a "$OUT/library-team.txt"
scenario library-single 5400 --mode single --keep --check "$CHECK" "Implement every function in the geometry package as its docstring says so all tests pass. Do not change the tests."
echo "library-single passing tests: $(passes library-single w1)/64" | tee -a "$OUT/library-single.txt"

{
    echo "| scenario | decision | result | time |"
    echo "|---|---|---|---|"
    for name in median best escalate library-team library-single; do
        decision=$(grep -m1 -E '^(auto|split):' "$OUT/$name.txt" | sed 's/|/\\|/g')
        result=$(grep -E '^(Merged|Winner|No worker|library-)' "$OUT/$name.txt" | tr '\n' ' ' | sed 's/|/\\|/g')
        echo "| $name | ${decision:--} | ${result:--} | $(grep -m1 '^exit ' "$OUT/$name.txt" | sed 's/^exit [0-9]* after //') |"
    done
} > "$OUT/summary.md"
cat "$OUT/summary.md"
