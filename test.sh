COMMITS=$(curl -s https://api.github.com/repos/builder555/testrelease/pulls/6/commits | jq -r 'map(select(.commit.message | startswith("chore:") | not)) | .[] | "* \(.commit.message)[\(.sha[:7])](\(.html_url))"')
echo "$COMMITS"
# echo "# Changelog" > changelog.tmp
# echo "" >> changelog.tmp
# echo "## v$(cat version.txt)" >> changelog.tmp
# echo "" >> changelog.tmp
# echo "$COMMITS" >> changelog.tmp
# tail -n +2 CHANGELOG.md >> changelog.tmp
# mv changelog.tmp CHANGELOG.md
4f51d93