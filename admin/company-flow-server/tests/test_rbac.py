from company_flow_server.auth.rbac import Principal
def test_viewer_read_only():
 p=Principal("u",("viewer",),())
 assert p.allowed("crew:read")
 assert not p.allowed("crew:delete")
def test_platform_admin_all():
 assert Principal("a",("platform_admin",),()).allowed("anything:anywhere")
def test_explicit_scope_extends_role():
 assert Principal("u",("viewer",),("flow:write",)).allowed("flow:write")
