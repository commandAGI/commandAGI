from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.computer_stop_action import ComputerStopAction
from ...models.http_validation_error import HTTPValidationError
from ...models.stop_computer_computer_stop_post_response_stop_computer_computer_stop_post import (
    StopComputerComputerStopPostResponseStopComputerComputerStopPost,
)
from ...types import Response


def _get_kwargs(
    *,
    body: ComputerStopAction,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/computer/stop",
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
        HTTPValidationError,
        StopComputerComputerStopPostResponseStopComputerComputerStopPost,
    ]
]:
    if response.status_code == 200:
        response_200 = (
            StopComputerComputerStopPostResponseStopComputerComputerStopPost.from_dict(
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
        HTTPValidationError,
        StopComputerComputerStopPostResponseStopComputerComputerStopPost,
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
    body: ComputerStopAction,
) -> Response[
    Union[
        HTTPValidationError,
        StopComputerComputerStopPostResponseStopComputerComputerStopPost,
    ]
]:
    """Stop Computer

    Args:
        body (ComputerStopAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, StopComputerComputerStopPostResponseStopComputerComputerStopPost]]
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
    body: ComputerStopAction,
) -> Optional[
    Union[
        HTTPValidationError,
        StopComputerComputerStopPostResponseStopComputerComputerStopPost,
    ]
]:
    """Stop Computer

    Args:
        body (ComputerStopAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, StopComputerComputerStopPostResponseStopComputerComputerStopPost]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: ComputerStopAction,
) -> Response[
    Union[
        HTTPValidationError,
        StopComputerComputerStopPostResponseStopComputerComputerStopPost,
    ]
]:
    """Stop Computer

    Args:
        body (ComputerStopAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, StopComputerComputerStopPostResponseStopComputerComputerStopPost]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: ComputerStopAction,
) -> Optional[
    Union[
        HTTPValidationError,
        StopComputerComputerStopPostResponseStopComputerComputerStopPost,
    ]
]:
    """Stop Computer

    Args:
        body (ComputerStopAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, StopComputerComputerStopPostResponseStopComputerComputerStopPost]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
