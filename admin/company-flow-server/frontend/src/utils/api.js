
function getHeaders(customHeaders = {}) {
  const token = localStorage.getItem('access_token');
  return {
    ...customHeaders,
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
}

function fetchWithAuth(url, options = {}) {
  const headers = getHeaders(options.headers || {});
  return fetch(url, { ...options, headers });
}

export const api = {
  login: (user_id, password) => fetchWithAuth('/api/v1/auth/login', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ user_id, password })
  }).then(async r => { if (!r.ok) throw new Error(await r.text()); return r.json(); }),
  signup: (payload) => fetchWithAuth('/api/v1/auth/signup', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
  }).then(async r => { if (!r.ok) throw new Error(await r.text()); return r.json(); }),
  fetchUsers: () => fetchWithAuth('/api/v1/auth/users').then(r => r.json()),
  approveUser: (user_id) => fetchWithAuth(`/api/v1/auth/users/${user_id}/approve`, { method: 'PUT' }).then(r => r.json()),

  fetchCrews: () => fetchWithAuth('/api/v1/crews').then(r => r.json()),
  fetchGraph: (crew_id, version) => fetchWithAuth(`/api/v1/crews/${encodeURIComponent(crew_id)}/${version}/graph?t=${Date.now()}`, { headers: { 'Cache-Control': 'no-cache' } }).then(r => r.json()),
  fetchRuns: () => fetchWithAuth('/api/v1/runs').then(r => r.json()),
  fetchRun: (id) => fetchWithAuth('/api/v1/runs/'+id).then(r => r.json()),
  fetchMcpTools: () => fetchWithAuth('/api/v1/mcp/tools').then(r => r.json()),
  testMcpTool: (tool_name, args) => fetchWithAuth('/api/v1/mcp/test', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ tool_name, arguments: args || {} })
  }).then(r => r.json()),
  kickoff: (crew_id, version, payload) => fetchWithAuth(`/api/v1/crews/${encodeURIComponent(crew_id)}/${version}/kickoff`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
  }).then(r => r.json()),
  deleteRun: (id) => fetchWithAuth(`/api/v1/runs/${id}?confirm=true`, { method: 'DELETE' }),
  deleteCrew: (crew_id, version) => fetchWithAuth(`/api/v1/crews/${encodeURIComponent(crew_id)}/${version}?confirm=true`, { method: 'DELETE' }),
  saveCrewSettings: (crew_id, body) => fetchWithAuth(`/api/v1/crews/${encodeURIComponent(crew_id)}/settings`, {
    method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  }),
  updateCrewNode: (crew_id, version, node_type, node_id, body) => fetchWithAuth(`/api/v1/crews/${encodeURIComponent(crew_id)}/${version}/nodes/${node_type}/${node_id}`, {
    method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  }),
  generateCrew: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchWithAuth('/api/v1/crews/generate', {
      method: 'POST',
      body: formData
    }).then(async r => { if(!r.ok) throw new Error(await r.text()); return r.json(); });
  }
};
