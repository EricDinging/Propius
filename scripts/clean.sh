#!/bin/bash

# Remove all logs. If you use docker, try sudo ./scripts/clean.sh

rm ./propius/monitor/log/*
rm ./propius/monitor/plot/*
rm ./evaluation/monitor/client/*
rm ./evaluation/monitor/executor/*
rm ./evaluation/monitor/job/*