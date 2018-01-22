#!/usr/bin/env bash
set -e -E

apt-get update
apt-get install -y build-essential chrpath libssl-dev libxft-dev
apt-get install -y libfreetype6 libfreetype6-dev
apt-get install -y libfontconfig1 libfontconfig1-dev
cd ~
PHANTOM_ARTIFACT="phantomjs-2.1.1-linux-x86_64"
wget http://cdn.bitbucket.org/ariya/phantomjs/downloads/"$PHANTOM_ARTIFACT".tar.bz2
tar xvjf "$PHANTOM_ARTIFACT".tar.bz2

mv "$PHANTOM_ARTIFACT" /usr/local/share
ln -sf /usr/local/share/"$PHANTOM_ARTIFACT"/bin/phantomjs /usr/local/bin
phantomjs --version
