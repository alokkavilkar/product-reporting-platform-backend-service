from jose import jwt
from urllib.request import urlopen
import json
import os
from django.http import JsonResponse
from django.conf import settings

print("settings.DEV =", settings.DEV) 

def get_token_auth_header(request):

    if settings.DEV:
        request.auth = {
            "sub": "test-user",
            "http://myapp.com/roles": ["admin", "worker"]
        }
        return "test-token"
    
    auth = request.META.get('HTTP_AUTHORIZATION', None)
    if not auth:
        raise Exception("Authorization header is expected.")

    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise Exception("Authorization header must start with Bearer.")
    elif len(parts) == 1:
        raise Exception("Token not found.")
    elif len(parts) > 2:
        raise Exception("Authorization header must be Bearer token.")

    return parts[1]


def requires_auth(view_func):
    def wrapper(request, *args, **kwargs):
        token = get_token_auth_header(request)
        
        if settings.DEV:
            request.auth = {
                "sub": "test-user",
                "http://myapp.com/roles": ["worker", "admin"]
            }
            return view_func(request, *args, **kwargs)
        
        jsonurl = urlopen(f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }

        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=settings.ALGORITHMS,
                    audience=settings.API_IDENTIFIER,
                    issuer=f"https://{settings.AUTH0_DOMAIN}/"
                )
            except jwt.ExpiredSignatureError:
                return JsonResponse({"message": "token is expired"}, status=401)
            except jwt.JWTClaimsError:
                return JsonResponse({"message": "incorrect claims, check audience and issuer"}, status=401)
            except Exception as e:
                return JsonResponse({"message": str(e)}, status=401)

            request.auth = payload
            return view_func(request, *args, **kwargs)
        return JsonResponse({"message": "Unable to find appropriate key"}, status=400)

    return wrapper
