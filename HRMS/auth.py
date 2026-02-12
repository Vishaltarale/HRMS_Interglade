import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from Employee.models import Employee, TokenBlacklist
from bson import ObjectId
from bson.errors import InvalidId


class MongoJWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication for MongoEngine ODM.
    Handles token validation, blacklist checking, and user retrieval.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.headers.get("Authorization")

        # If no Authorization header, return None (not an error, just not authenticated)
        if not auth_header:
            return None

        # Validate Authorization header format
        if not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Invalid Authorization header format. Expected 'Bearer <token>'")

        # Extract token
        token = auth_header.split(" ")[1].strip()
        
        if not token:
            raise AuthenticationFailed("Token not provided.")

        # Check if token is blacklisted
        try:
            blacklisted_token = TokenBlacklist.objects(token=token).first()
            if blacklisted_token is not None:
                raise AuthenticationFailed("Token has been revoked. Please login again.")
        except Exception as e:
            # Log the error but don't expose internal details to client
            print(f"Error checking token blacklist: {e}")
            # Continue with authentication even if blacklist check fails
            pass

        # Decode and validate JWT token
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired. Please login again.")
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f"Invalid token: {str(e)}")
        except Exception as e:
            raise AuthenticationFailed(f"Token validation failed: {str(e)}")

        # Extract employee ID from payload
        emp_id = payload.get("empId")
        if not emp_id:
            raise AuthenticationFailed("Token payload is invalid. Missing employee ID.")

        # Retrieve employee from MongoDB
        try:
            emp = Employee.objects.get(id=ObjectId(emp_id))
        except InvalidId:
            raise AuthenticationFailed("Invalid employee ID format.")
        except Employee.DoesNotExist:
            raise AuthenticationFailed("User not found. Account may have been deleted.")
        except Exception as e:
            print(f"Error retrieving employee: {e}")
            raise AuthenticationFailed("Authentication failed. Please try again.")

        # Check if employee account is active
        if hasattr(emp, 'status') and emp.status != 'active':
            raise AuthenticationFailed("Account is inactive. Please contact administrator.")

        # Return user and token (DRF expects a tuple)
        return (emp, token)

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthenticated response.
        """
        return 'Bearer realm="api"'

class OptionalMongoJWTAuthentication(MongoJWTAuthentication):
    """
    Optional authentication - doesn't fail if no token provided.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            # If authentication fails, return None instead of raising error
            return None