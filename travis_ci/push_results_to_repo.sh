#!/bin/sh

setup_git() {
  git config --global user.email "travis@travis-ci.org"
  git config --global user.name "Travis CI"
}

commit_website_files() {
  git checkout ${TRAVIS_BRANCH}
#  touch scaliability_result_${TRAVIS_BUILD_NUMBER}.csv
  git add bee_scalability_test_result_build_${TRAVIS_BUILD_NUMBER}.csv
  git commit --message "Travis build: ${TRAVIS_BUILD_NUMBER} [skip ci]"
}

upload_files() {
  git remote add remote_repo https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git
  git push --quiet --set-upstream remote_repo ${TRAVIS_BRANCH} 
}

setup_git
commit_website_files
upload_files