from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.rdp_stop_server_action import RdpStopServerAction
from ...models.stop_rdp_server_rdp_stop_post_response_stop_rdp_server_rdp_stop_post import (
    StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost,
)
from ...types import Response


def _get_kwargs(
    *,
    body: RdpStopServerAction,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/rdp/stop",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]
]:
    if response.status_code == 200:
        response_200 = (
            StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost.from_dict(
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
    Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]
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
    body: RdpStopServerAction,
) -> Response[
    Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]
]:
    """Stop Rdp Server

    Args:
        body (RdpStopServerAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]]
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
    body: RdpStopServerAction,
) -> Optional[
    Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]
]:
    """Stop Rdp Server

    Args:
        body (RdpStopServerAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: RdpStopServerAction,
) -> Response[
    Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]
]:
    """Stop Rdp Server

    Args:
        body (RdpStopServerAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: RdpStopServerAction,
) -> Optional[
    Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]
]:
    """Stop Rdp Server

    Args:
        body (RdpStopServerAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, StopRdpServerRdpStopPostResponseStopRdpServerRdpStopPost]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
