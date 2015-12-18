#!/bin/bash
pushd `dirname $0` > /dev/null
DIR=`pwd -P`
popd > /dev/null

cat $DIR/general.config > $DIR/raspimjpeg.config
cat $DIR/annotation.config >> $DIR/raspimjpeg.config
