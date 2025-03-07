from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_screenshot_observation_screenshot_get_format import (
    GetScreenshotObservationScreenshotGetFormat,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.screenshot_observation import ScreenshotObservation
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    display_id: Union[Unset, int] = 0,
    format_: Union[
        Unset, GetScreenshotObservationScreenshotGetFormat
    ] = GetScreenshotObservationScreenshotGetFormat.PIL,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["display_id"] = display_id

    json_format_: Union[Unset, str] = UNSET
    if not isinstance(format_, Unset):
        json_format_ = format_.value

    params["format"] = json_format_

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/observation/screenshot",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, ScreenshotObservation]]:
    if response.status_code == 200:
        response_200 = ScreenshotObservation.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, ScreenshotObservation]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    display_id: Union[Unset, int] = 0,
    format_: Union[
        Unset, GetScreenshotObservationScreenshotGetFormat
    ] = GetScreenshotObservationScreenshotGetFormat.PIL,
) -> Response[Union[HTTPValidationError, ScreenshotObservation]]:
    """Get Screenshot

    Args:
        display_id (Union[Unset, int]):  Default: 0.
        format_ (Union[Unset, GetScreenshotObservationScreenshotGetFormat]):  Default:
            GetScreenshotObservationScreenshotGetFormat.PIL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, ScreenshotObservation]]
    """

    kwargs = _get_kwargs(
        display_id=display_id,
        format_=format_,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    display_id: Union[Unset, int] = 0,
    format_: Union[
        Unset, GetScreenshotObservationScreenshotGetFormat
    ] = GetScreenshotObservationScreenshotGetFormat.PIL,
) -> Optional[Union[HTTPValidationError, ScreenshotObservation]]:
    """Get Screenshot

    Args:
        display_id (Union[Unset, int]):  Default: 0.
        format_ (Union[Unset, GetScreenshotObservationScreenshotGetFormat]):  Default:
            GetScreenshotObservationScreenshotGetFormat.PIL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, ScreenshotObservation]
    """

    return sync_detailed(
        client=client,
        display_id=display_id,
        format_=format_,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    display_id: Union[Unset, int] = 0,
    format_: Union[
        Unset, GetScreenshotObservationScreenshotGetFormat
    ] = GetScreenshotObservationScreenshotGetFormat.PIL,
) -> Response[Union[HTTPValidationError, ScreenshotObservation]]:
    """Get Screenshot

    Args:
        display_id (Union[Unset, int]):  Default: 0.
        format_ (Union[Unset, GetScreenshotObservationScreenshotGetFormat]):  Default:
            GetScreenshotObservationScreenshotGetFormat.PIL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, ScreenshotObservation]]
    """

    kwargs = _get_kwargs(
        display_id=display_id,
        format_=format_,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    display_id: Union[Unset, int] = 0,
    format_: Union[
        Unset, GetScreenshotObservationScreenshotGetFormat
    ] = GetScreenshotObservationScreenshotGetFormat.PIL,
) -> Optional[Union[HTTPValidationError, ScreenshotObservation]]:
    """Get Screenshot

    Args:
        display_id (Union[Unset, int]):  Default: 0.
        format_ (Union[Unset, GetScreenshotObservationScreenshotGetFormat]):  Default:
            GetScreenshotObservationScreenshotGetFormat.PIL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, ScreenshotObservation]
    """

    return (
        await asyncio_detailed(
            client=client,
            display_id=display_id,
            format_=format_,
        )
    ).parsed
