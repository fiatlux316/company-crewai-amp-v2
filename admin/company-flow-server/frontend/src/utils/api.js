
export const api = {
  fetchCrews: () => fetch('/api/v1/crews').then(r => r.json()),
  fetchGraph: (crew_id, version) => fetch(`/api/v1/crews/${encodeURIComponent(crew_id)}/${version}/graph`).then(r => r.json()),
  fetchRuns: () => fetch('/api/v1/runs').then(r => r.json()),
  fetchRun: (id) => fetch('/api/v1/runs/'+id).then(r => r.json()),
  fetchMcpTools: () => fetch('/api/v1/mcp/tools').then(r => r.json()),
  kickoff: (crew_id, version, payload) => fetch(`/api/v1/crews/${encodeURIComponent(crew_id)}/${version}/kickoff`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
  }).then(r => r.json()),
  deleteRun: (id) => fetch(`/api/v1/runs/${id}?confirm=true`, { method: 'DELETE' }),
  deleteCrew: (crew_id, version) => fetch(`/api/v1/crews/${encodeURIComponent(crew_id)}/${version}?confirm=true`, { method: 'DELETE' }),
  saveCrewSettings: (crew_id, body) => fetch(`/api/v1/crews/${encodeURIComponent(crew_id)}/settings`, {
    method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  })
};
