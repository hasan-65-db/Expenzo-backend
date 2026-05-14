from passlib.context import CryptContext
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
def get_password_hash(pwd:str):
    return pwd_context.hash(pwd)
def get_password_verify(plain_pwd:str, hashed_pwd:str):
    return pwd_context.verify(plain_pwd, hashed_pwd)

def create_access_token(user_id: int):
    refresh = RefreshToken()
    refresh["user_id"] = user_id
    return str(refresh.access_token)

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if user_id is None:
            raise InvalidToken("Invalid Token")
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise InvalidToken("User Not Found")
        
        
 