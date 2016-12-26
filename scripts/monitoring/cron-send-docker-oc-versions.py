#!/usr/bin/python
'''
  Send openshift and docker versions with miq_metric tag to metric_sender

  Example:
  ./cron-send-docker-oc-versions.py -u oc_username -p oc_password
'''
# Disabling invalid-name because pylint doesn't like the naming conention we have.
# pylint: disable=invalid-name,import-error

from docker import AutoVersionClient
import argparse
from openshift_tools.monitoring.metric_sender import MetricSender
import os
import requests


def parse_args():
    '''Parse the arguments for this script'''
    parser = argparse.ArgumentParser(description="Tool to send docker and openshift versions")
    parser.add_argument('-u', '--username', action="store", help="openshift username")
    parser.add_argument('-p', '--password', action="store", help="openshift password")
    parser.add_argument('-d', '--debug', default=False, action="store_true", help="debug mode")
    parser.add_argument('-v', '--verbose', default=False, action="store_true", help="Verbose?")
    parser.add_argument('-s', '--host', help='specify openshift host name')

    args = parser.parse_args()
    return args


def main():
    '''get docker and openshift versions and send to metric sender
    '''

    args = parse_args()

    mts = MetricSender(verbose=args.verbose, debug=args.debug)

    # Get docker version
    cli = AutoVersionClient(base_url='unix://var/run/docker.sock', timeout=120)
    docker_version = cli.version()["Version"]
    mts.add_metric({"docker.version": docker_version}, key_tags={'miq_metric': 'true'})

    # Get openshift version
    if args.username:
        creds = (args.username, args.password)
    else:
        creds = None

    hostname = args.host or os.environ['HOSTNAME']
    url = "https://{0}:8443/version/openshift".format(hostname)
    r = requests.get(url, auth=creds, verify=False)
    if r.status_code == 200:
        oc_version = r.json()["gitVersion"]
        mts.add_metric({"oc.version": oc_version}, key_tags={'miq_metric': 'true'})
    else:
        print ("Failed to get openshift version: ", r.status_code)

    mts.send_metrics()


if __name__ == '__main__':
    main()
