#!/bin/bash

# Remove all logs. If you use docker, try sudo ./scripts/clean.sh

rm ./propius_controller/monitor/log/* -f
rm ./propius_controller/monitor/plot/* -f
rm ./evaluation/monitor/client/* -f
rm ./evaluation/monitor/executor/* -f
rm ./evaluation/monitor/job/* -f