#!/usr/bin/env python3
"""CLI helper for ACL operations against the running server.

Usage:
  python cli_acl.py register-device --user alice --device-id id123
  python cli_acl.py grants --file-id <file_id> --user alice
  python cli_acl.py grant --file-id <file_id> --to 0x... --devices id1,id2
  python cli_acl.py revoke --file-id <file_id> --to 0x...
"""
import argparse
import requests
import sys

BASE = "http://localhost:5000"

sess = requests.Session()


def login(user):
    r = sess.post(f"{BASE}/api/login", json={"user_id": user})
    if r.ok:
        print(f"Logged in as {user}")
    else:
        print("Login failed:", r.text)
        sys.exit(1)


def register_device(device_id=None, public_key=None):
    body = {}
    if device_id: body['device_id'] = device_id
    if public_key: body['device_public_key'] = public_key
    r = sess.post(f"{BASE}/api/acl/register_device", json=body)
    print(r.status_code, r.text)


def get_grants(file_id):
    r = sess.get(f"{BASE}/api/acl/grants", params={'file_id': file_id})
    print(r.status_code)
    print(r.json())


def grant(file_id, to_addr, devices=None):
    body = {'file_id': file_id, 'user_eth_address': to_addr, 'expiry': 0}
    if devices:
        body['device_ids'] = devices.split(',')
    r = sess.post(f"{BASE}/api/acl/grant", json=body)
    print(r.status_code)
    print(r.json())


def revoke(file_id, to_addr):
    body = {'file_id': file_id, 'user_eth_address': to_addr}
    r = sess.post(f"{BASE}/api/acl/revoke", json=body)
    print(r.status_code)
    print(r.json())


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')

    sp_login = sub.add_parser('login')
    sp_login.add_argument('--user', required=True)

    sp_register = sub.add_parser('register-device')
    sp_register.add_argument('--user', required=True)
    sp_register.add_argument('--device-id')
    sp_register.add_argument('--public-key')

    sp_grants = sub.add_parser('grants')
    sp_grants.add_argument('--user', required=True)
    sp_grants.add_argument('--file-id', required=True)

    sp_grant = sub.add_parser('grant')
    sp_grant.add_argument('--user', required=True)
    sp_grant.add_argument('--file-id', required=True)
    sp_grant.add_argument('--to', required=True)
    sp_grant.add_argument('--devices')

    sp_revoke = sub.add_parser('revoke')
    sp_revoke.add_argument('--user', required=True)
    sp_revoke.add_argument('--file-id', required=True)
    sp_revoke.add_argument('--to', required=True)

    args = p.parse_args()

    if args.cmd == 'login':
        login(args.user)
    elif args.cmd == 'register-device':
        login(args.user)
        register_device(args.device_id, args.public_key)
    elif args.cmd == 'grants':
        login(args.user)
        get_grants(args.file_id)
    elif args.cmd == 'grant':
        login(args.user)
        grant(args.file_id, args.to, args.devices)
    elif args.cmd == 'revoke':
        login(args.user)
        revoke(args.file_id, args.to)
    else:
        p.print_help()
