from __future__ import annotations
from dataclasses import dataclass
import os, jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ROLE_PERMISSIONS={
 "viewer":{"crew:read","run:read","mcp:read","flow:read"},
 "developer":{"crew:read","crew:deploy","crew:kickoff:dev","run:read","mcp:read","flow:read"},
 "crew_owner":{"crew:read","crew:deploy","crew:kickoff:dev","crew:settings","run:read","mcp:read","flow:read"},
 "operator":{"crew:read","crew:kickoff:dev","crew:kickoff:prod","run:read","mcp:read","flow:read","flow:run"},
 "flow_admin":{"crew:read","run:read","mcp:read","flow:read","flow:write","flow:run"},
 "platform_admin":{"*"},
}
security=HTTPBearer(auto_error=False)

@dataclass(frozen=True)
class Principal:
 subject:str
 roles:tuple[str,...]
 scopes:tuple[str,...]
 environment:str|None=None
 def allowed(self,permission:str)->bool:
  perms=set(self.scopes)
  for r in self.roles:perms.update(ROLE_PERMISSIONS.get(r,set()))
  return "*" in perms or permission in perms

def decode_token(token:str)->Principal:
 alg=os.getenv("AUTH_JWT_ALGORITHM","HS256")
 kwargs={"algorithms":[alg],"options":{"verify_aud":bool(os.getenv("AUTH_JWT_AUDIENCE"))}}
 if os.getenv("AUTH_JWT_AUDIENCE"):kwargs["audience"]=os.getenv("AUTH_JWT_AUDIENCE")
 if os.getenv("AUTH_JWT_ISSUER"):kwargs["issuer"]=os.getenv("AUTH_JWT_ISSUER")
 key=os.getenv("AUTH_JWT_PUBLIC_KEY") or os.getenv("AUTH_JWT_SECRET","dev-secret-change-me")
 try: claims=jwt.decode(token,key,**kwargs)
 except jwt.PyJWTError as e: raise HTTPException(401,f"invalid access token: {e}")
 roles=claims.get("roles",[])
 if isinstance(roles,str):roles=roles.split()
 scopes=claims.get("scope",claims.get("scopes",[]))
 if isinstance(scopes,str):scopes=scopes.split()
 return Principal(str(claims.get("sub","unknown")),tuple(roles),tuple(scopes),claims.get("environment"))

def current_principal(credentials:HTTPAuthorizationCredentials|None=Depends(security))->Principal:
 if os.getenv("AUTH_DISABLED","false").lower()=="true":
  return Principal("dev-admin",("platform_admin",),())
 if not credentials:raise HTTPException(401,"bearer token required")
 return decode_token(credentials.credentials)

def require(permission:str):
 def dep(p:Principal=Depends(current_principal))->Principal:
  if not p.allowed(permission):raise HTTPException(403,f"permission required: {permission}")
  return p
 return dep

def require_owner_or(permission:str, crew_id:str, owner:str, p:Principal):
 if p.allowed(permission):return
 if "crew_owner" in p.roles and p.subject==owner:return
 raise HTTPException(403,"crew owner or elevated permission required")
