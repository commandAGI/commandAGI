from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.drag_action import DragAction
from ...models.execute_drag_execute_drag_post_response_execute_drag_execute_drag_post import (
    ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: DragAction,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/execute/drag",
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
        ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost,
        HTTPValidationError,
    ]
]:
    if response.status_code == 200:
        response_200 = (
            ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost.from_dict(
                response.json()
            )
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
        ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost,
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
    body: DragAction,
) -> Response[
    Union[
        ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost,
        HTTPValidationError,
    ]
]:
    """Execute Drag

    Args:
        body (DragAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost, HTTPValidationError]]
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
    body: DragAction,
) -> Optional[
    Union[
        ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost,
        HTTPValidationError,
    ]
]:
    """Execute Drag

    Args:
        body (DragAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: DragAction,
) -> Response[
    Union[
        ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost,
        HTTPValidationError,
    ]
]:
    """Execute Drag

    Args:
        body (DragAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: DragAction,
) -> Optional[
    Union[
        ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost,
        HTTPValidationError,
    ]
]:
    """Execute Drag

    Args:
        body (DragAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ExecuteDragExecuteDragPostResponseExecuteDragExecuteDragPost, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
