import re

with open('/Users/jck/WORK/DEV/company-crewai-amp-v2/admin/company-flow-server/frontend/src/components/ExecutionHistory.jsx', 'r') as f:
    content = f.read()

# Add crews state and API call
content = content.replace("const [runs, setRuns] = useState([]);", "const [runs, setRuns] = useState([]);\n  const [crews, setCrews] = useState([]);")

# Add fetchCrews to refreshAll
refresh_all = """const refreshAll = async () => {
      try {
        const data = await api.fetchRuns();
        setRuns(data.runs || []);
        const crewsData = await api.fetchCrews();
        setCrews(crewsData.crews || []);
      } catch(e) {
        console.error(e);
      }"""
content = re.sub(r'const refreshAll = async \(\) => \{\s*try \{\s*const data = await api\.fetchRuns\(\);\s*setRuns\(data\.runs \|\| \[\]\);\s*\} catch\(e\) \{\s*console\.error\(e\);\s*\}', refresh_all, content)

# Change delete button
delete_button = """const currentCrewData = currentRun ? crews.find(c => c.crew_id === currentRun.crew_id && c.version === currentRun.version) : null;
                const isDeleteDisabled = userType === '3' && currentCrewData && currentCrewData.owner !== userId;

                return (
                  <div style={{marginLeft: 'auto'}}>
                    <button 
                      className="btn danger" 
                      onClick={() => deleteHistory(currentRun.run_id)}
                      disabled={isDeleteDisabled}
                      title={isDeleteDisabled ? "자신이 배포한 Crew의 이력만 삭제할 수 있습니다." : ""}
                    >
                      Delete
                    </button>
                  </div>
                );
"""
# Replace the button markup
content = content.replace("""<div style={{marginLeft: 'auto'}}>
                  <button className="btn danger" onClick={() => deleteHistory(currentRun.run_id)}>Delete</button>
                </div>""", """<div style={{marginLeft: 'auto'}}>
                  <button 
                    className="btn danger" 
                    onClick={() => deleteHistory(currentRun.run_id)}
                    disabled={userType === '3' && crews.find(c => c.crew_id === currentRun.crew_id && c.version === currentRun.version)?.owner !== userId}
                    title={userType === '3' && crews.find(c => c.crew_id === currentRun.crew_id && c.version === currentRun.version)?.owner !== userId ? "자신이 배포한 Crew의 이력만 삭제할 수 있습니다." : ""}
                  >
                    Delete
                  </button>
                </div>""")

with open('/Users/jck/WORK/DEV/company-crewai-amp-v2/admin/company-flow-server/frontend/src/components/ExecutionHistory.jsx', 'w') as f:
    f.write(content)
