#!/bin/sh

setup_git() {
  git config --global user.email "travis@travis-ci.org"
  git config --global user.name "Travis CI"
}

commit_website_files() {
  git checkout -b ${TRAVIS_BRANCH}
  touch scaliability_result_${TRAVIS_BUILD_NUMBER}.csv
  git add scaliability_result_${TRAVIS_BUILD_NUMBER}.csv
  git commit --message "Travis build: $TRAVIS_BUILD_NUMBER"
}

upload_files() {
  git remote add origin https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git > /dev/null 2>&1
  git push --quiet --set-upstream origin ${TRAVIS_BRANCH} 
}

setup_git
commit_website_files
upload_files