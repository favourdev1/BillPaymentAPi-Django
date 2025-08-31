from rest_framework.response import Response
from rest_framework import status


def success_response(message, data=None, status_code=status.HTTP_200_OK):
    """
    Create a standardized success response
    
    Args:
        message (str): Success message
        data (dict, optional): Response data
        status_code (int): HTTP status code
    
    Returns:
        Response: Standardized success response
    """
    response_data = {
        "status": True,
        "message": message,
        "data": data or {}
    }
    return Response(response_data, status=status_code)


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Create a standardized error response
    
    Args:
        message (str): Error message
        errors (list or dict, optional): Error details
        status_code (int): HTTP status code
    
    Returns:
        Response: Standardized error response
    """
    # Handle different error formats
    if errors is None:
        errors = []
    elif isinstance(errors, dict):
        # Convert serializer errors to list format
        error_list = []
        for field, field_errors in errors.items():
            if isinstance(field_errors, list):
                for error in field_errors:
                    error_list.append(f"{field}: {error}")
            else:
                error_list.append(f"{field}: {field_errors}")
        errors = error_list
    elif isinstance(errors, str):
        errors = [errors]
    
    response_data = {
        "status": False,
        "message": message,
        "errors": errors
    }
    return Response(response_data, status=status_code)


def validation_error_response(serializer_errors):
    """
    Create a standardized validation error response from serializer errors
    
    Args:
        serializer_errors (dict): Django REST framework serializer errors
    
    Returns:
        Response: Standardized validation error response
    """
    return error_response(
        message="Validation failed",
        errors=serializer_errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )