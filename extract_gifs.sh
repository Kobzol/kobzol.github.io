find assets -name "*.gif" -execdir sh -c 'convert {}[0] `basename -s .gif {}`.png' \;
git add assets/**/*.png
