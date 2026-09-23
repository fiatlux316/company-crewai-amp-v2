import unittest
from company_flow_server.mcp.registry import invoke_mcp_tool

class TestMcpInvoke(unittest.TestCase):
    def test_invoke_mcp_tool_jira(self):
        res = invoke_mcp_tool("jira.get_issue", {"issue_key": "PROJ-123"})
        self.assertEqual(res["status"], "success")
        self.assertIn("PROJ-123", res["response"])

    def test_invoke_mcp_tool_rds(self):
        res = invoke_mcp_tool("rds.execute_query", {"db_identifier": "main-db", "query": "SELECT * FROM users"})
        self.assertEqual(res["status"], "success")
        self.assertIn("main-db", res["response"])

    def test_invoke_mcp_tool_datadog_with_string_limit(self):
        res = invoke_mcp_tool("datadog.logs.search", {
            "query": "service:erody-mp status:error",
            "time_range": "last 1hours",
            "limit": "5"
        })
        self.assertEqual(res["status"], "success")
        self.assertTrue("ERROR" in res["response"] or "Logs" in res["response"])

if __name__ == "__main__":
    unittest.main()
