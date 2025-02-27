from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.computer_resume_action import ComputerResumeAction
from ...models.http_validation_error import HTTPValidationError
from ...models.resume_computer_computer_resume_post_response_resume_computer_computer_resume_post import (
    ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost,
)
from ...types import Response


def _get_kwargs(
    *,
    body: ComputerResumeAction,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/computer/resume",
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
        ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost,
    ]
]:
    if response.status_code == 200:
        response_200 = ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost.from_dict(
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
        HTTPValidationError,
        ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost,
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
    body: ComputerResumeAction,
) -> Response[
    Union[
        HTTPValidationError,
        ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost,
    ]
]:
    """Resume Computer

    Args:
        body (ComputerResumeAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost]]
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
    body: ComputerResumeAction,
) -> Optional[
    Union[
        HTTPValidationError,
        ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost,
    ]
]:
    """Resume Computer

    Args:
        body (ComputerResumeAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: ComputerResumeAction,
) -> Response[
    Union[
        HTTPValidationError,
        ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost,
    ]
]:
    """Resume Computer

    Args:
        body (ComputerResumeAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: ComputerResumeAction,
) -> Optional[
    Union[
        HTTPValidationError,
        ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost,
    ]
]:
    """Resume Computer

    Args:
        body (ComputerResumeAction):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, ResumeComputerComputerResumePostResponseResumeComputerComputerResumePost]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
