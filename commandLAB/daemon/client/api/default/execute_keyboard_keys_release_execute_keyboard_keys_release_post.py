from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.execute_keyboard_keys_release_execute_keyboard_keys_release_post_response_execute_keyboard_keys_release_execute_keyboard_keys_release_post import (
    ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.keyboard_keys_release_action import KeyboardKeysReleaseAction
from ...types import Response


def _get_kwargs(
    *,
    body: KeyboardKeysReleaseAction,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/execute/keyboard/keys_release",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost,
        HTTPValidationError,
    ]
]:
    if response.status_code == 200:
        response_200 = ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost.from_dict(
            response.json()
        )

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost,
        HTTPValidationError,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: KeyboardKeysReleaseAction,
) -> Response[
    Union[
        ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost,
        HTTPValidationError,
    ]
]:
    """Execute Keyboard Keys Release

    Args:
        body (KeyboardKeysReleaseAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: KeyboardKeysReleaseAction,
) -> Optional[
    Union[
        ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost,
        HTTPValidationError,
    ]
]:
    """Execute Keyboard Keys Release

    Args:
        body (KeyboardKeysReleaseAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: KeyboardKeysReleaseAction,
) -> Response[
    Union[
        ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost,
        HTTPValidationError,
    ]
]:
    """Execute Keyboard Keys Release

    Args:
        body (KeyboardKeysReleaseAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: KeyboardKeysReleaseAction,
) -> Optional[
    Union[
        ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost,
        HTTPValidationError,
    ]
]:
    """Execute Keyboard Keys Release

    Args:
        body (KeyboardKeysReleaseAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePostResponseExecuteKeyboardKeysReleaseExecuteKeyboardKeysReleasePost, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
