#!/bin/sh
# Polite mirror of listed pages plus their page requisites (CSS, JS, images).
cd /home/ubuntu/Projects/railcore-dozuki/backup/html
wget --input-file=../html_urls.txt --page-requisites --span-hosts \
  --domains=railcore.dozuki.com,d3015z1jd0uox2.cloudfront.net,d3t0tbmlie281e.cloudfront.net \
  --reject-regex='/(Edit|History|Login|Logout|Register|Signup)(/|\?|$)' \
  --convert-links --adjust-extension --restrict-file-names=windows \
  --wait=0.5 --random-wait --tries=5 --waitretry=10 --timeout=60 \
  --user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36' \
  --no-verbose --output-file=../html_wget.log
echo "wget exit $?"
