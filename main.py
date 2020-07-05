import os
import sys
from http import HTTPStatus
from typing import Optional, Tuple

import requests

GITHUB_API_BASE_URL = 'https://api.github.com'


def escape(v: str) -> str:
    return repr(v)[1:-1]


def set_action_output(name: str, value: str):
    sys.stdout.write(f'::set-output name={name}::{escape(value)}\n')


def print_action_error(msg: str):
    sys.stdout.write(f'::error file={__name__}::{escape(msg)}\n')


def print_action_debug(msg: str):
    sys.stdout.write(f'::debug file={__name__}::{escape(msg)}\n')


def get_action_input(
    name: str, required: bool = False, default: Optional[str] = None
) -> str:
    v = os.environ.get(f'INPUT_{name.upper()}', '')
    if v == '' and default:
        v = default
    if required and v == '':
        print_action_error(f'input required and not supplied: {name}')
        exit(1)
    return v


def create(token, repo, body, issue_number) -> Tuple[str, str]:
    headers = {
        'Authorization': f'token {token}',
    }
    data = {
        'body': body,
    }
    resp = requests.post(
        f'{GITHUB_API_BASE_URL}/repos/{repo}/issues/{issue_number}/comments',
        headers=headers,
        json=data,
    )
    if resp.status_code != HTTPStatus.CREATED:
        print_action_error(f'cannot create comment')
        print_action_debug(f'status code: {resp.status_code}')
        print_action_debug(f'response body: {resp.text}')
        exit(1)

    json = resp.json()
    return str(json['id']), body


def edit(token, repo, body, comment_id) -> Tuple[str, str]:
    headers = {
        'Authorization': f'token {token}',
    }
    data = {
        'body': body,
    }
    resp = requests.patch(
        f'{GITHUB_API_BASE_URL}/repos/{repo}/issues/comments/{comment_id}',
        headers=headers,
        json=data,
    )
    if resp.status_code != HTTPStatus.OK:
        print_action_error(f'cannot edit comment')
        print_action_debug(f'status code: {resp.status_code}')
        print_action_debug(f'response body: {resp.text}')
        exit(1)

    json = resp.json()
    return str(json['id']), body


def delete(token, repo, comment_id) -> Tuple[str, str]:
    headers = {
        'Authorization': f'token {token}',
    }
    resp = requests.delete(
        f'{GITHUB_API_BASE_URL}/repos/{repo}/issues/comments/{comment_id}',
        headers=headers,
    )
    if resp.status_code != HTTPStatus.NO_CONTENT:
        print_action_error(f'cannot delete comment')
        print_action_debug(f'status code: {resp.status_code}')
        print_action_debug(f'response body: {resp.text}')
        exit(1)

    return '', ''


def main():
    repo = os.environ['GITHUB_REPOSITORY']
    action_type = get_action_input('type', required=True)
    token = get_action_input('token', required=True)
    body = get_action_input('body')
    comment_id = get_action_input('comment_id')
    issue_number = get_action_input('issue_number')

    _id, _body = '', ''
    if action_type == 'create':
        _id, _body = create(token, repo, body, issue_number)
    elif action_type == 'edit':
        _id, _body = edit(token, repo, body, comment_id)
    elif action_type == 'delete':
        _id, _body = delete(token, repo, comment_id)

    set_action_output('id', _id)
    set_action_output('body', _body)


if __name__ == '__main__':
    main()
