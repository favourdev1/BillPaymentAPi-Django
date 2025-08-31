from rest_framework.response import Response
from rest_framework import status
from .response_utils import success_response, error_response, validation_error_response


class StandardResponseMixin:
    """
    A reusable mixin that provides standardized response methods for API views.
    This mixin encapsulates common response functionality while remaining flexible
    for customization across different contexts.
    """
    
    def success_response(self, message="Operation successful", data=None, status_code=status.HTTP_200_OK):
        """
        Return a standardized success response.
        
        Args:
            message (str): Success message
            data (dict): Response data
            status_code (int): HTTP status code
            
        Returns:
            Response: Standardized success response
        """
        return success_response(message=message, data=data, status_code=status_code)
    
    def error_response(self, message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Return a standardized error response.
        
        Args:
            message (str): Error message
            errors (list or dict, optional): Error details
            status_code (int): HTTP status code
            
        Returns:
            Response: Standardized error response
        """
        return error_response(message=message, errors=errors, status_code=status_code)
    
    def validation_error_response(self, serializer_errors):
        """
        Create a standardized validation error response.
        
        Args:
            serializer_errors (dict): Django REST framework serializer errors
            
        Returns:
            Response: Standardized validation error response
        """
        return validation_error_response(serializer_errors)
    
    def handle_serializer_errors(self, serializer, message="Validation failed"):
        """
        Handle serializer validation errors and return standardized response.
        
        Args:
            serializer: Django REST framework serializer with errors
            message (str): Custom error message (not used in current implementation)
            
        Returns:
            Response: Standardized validation error response
        """
        return self.validation_error_response(serializer.errors)
    
    def handle_exception_response(self, exception, message=None, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
        """
        Handle exceptions and return standardized error response.
        
        Args:
            exception: Exception instance
            message (str): Custom error message (optional)
            status_code (int): HTTP status code
            
        Returns:
            Response: Standardized error response
        """
        if message is None:
            message = str(exception) if str(exception) else "An unexpected error occurred"
        
        return self.error_response(message=message, status_code=status_code)
    
    def paginated_response(self, queryset, serializer_class, request, message="Data retrieved successfully"):
        """
        Return a standardized paginated response.
        
        Args:
            queryset: Django queryset
            serializer_class: Serializer class to use
            request: HTTP request object
            message (str): Success message
            
        Returns:
            Response: Standardized paginated response
        """
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(page, many=True, context={'request': request})
            paginated_data = self.get_paginated_response(serializer.data)
            
            # Wrap paginated response in our standard format
            return self.success_response(
                message=message,
                data={
                    'results': paginated_data.data['results'],
                    'pagination': {
                        'count': paginated_data.data.get('count'),
                        'next': paginated_data.data.get('next'),
                        'previous': paginated_data.data.get('previous')
                    }
                }
            )
        
        serializer = serializer_class(queryset, many=True, context={'request': request})
        return self.success_response(message=message, data={'results': serializer.data})