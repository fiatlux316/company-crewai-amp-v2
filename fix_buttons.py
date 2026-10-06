import re

with open('/Users/jck/WORK/DEV/company-crewai-amp-v2/admin/company-flow-server/frontend/src/components/CrewProcess.jsx', 'r') as f:
    content = f.read()

# 1. Update CrewDiagram signature
content = content.replace("function CrewDiagram({ graph, crewId, version, onUpdate }) {", "function CrewDiagram({ graph, crewId, version, onUpdate, isReadOnly }) {")

# 2. Update 수정 사항 저장 button in CrewDiagram
# Find the button disabled={isSaving} ... > {isSaving ? '저장 중...' : '수정 사항 저장'} </button>
save_node_btn = """                  <button 
                    disabled={isReadOnly || isSaving}
                    style={{ padding: '8px 16px', background: isReadOnly || isSaving ? '#9ca3af' : '#3b82f6', color: '#fff', border: 'none', borderRadius: '4px', cursor: isReadOnly || isSaving ? 'not-allowed' : 'pointer' }}
                    onClick={async () => {"""
content = re.sub(r'<button \s*disabled=\{isSaving\}\s*style=\{\{ padding: \'8px 16px\', background: \'#3b82f6\', color: \'#fff\', border: \'none\', borderRadius: \'4px\', cursor: \'pointer\' \}\}\s*onClick=\{async \(\) => \{', save_node_btn, content)

# 3. In CrewProcess, define isReadOnly
content = content.replace("export default function CrewProcess({ onNavigateHistory, initialCrewId, userType, userId }) {\n  const [crews, setCrews] = useState([]);", "export default function CrewProcess({ onNavigateHistory, initialCrewId, userType, userId }) {\n  const [crews, setCrews] = useState([]);\n  const isReadOnly = userType === '3' && selectedCrew?.owner !== userId;")

# 4. Use isReadOnly in delete button
content = content.replace("disabled={userType === '3' && selectedCrew.owner !== userId}", "disabled={isReadOnly}")
content = content.replace("title={userType === '3' && selectedCrew.owner !== userId ? \"자신이 배포한 Crew만 삭제할 수 있습니다.\" : \"\"}", "title={isReadOnly ? \"자신이 배포한 Crew만 삭제할 수 있습니다.\" : \"\"}")

# 5. Disable Save buttons
# button className="btn secondary" onClick={saveSettings}>Save Schedule</button>
content = content.replace('<button className="btn secondary" onClick={saveSettings}>Save Schedule</button>', 
'<button className="btn secondary" onClick={saveSettings} disabled={isReadOnly} title={isReadOnly ? "자신이 배포한 Crew만 수정할 수 있습니다." : ""}>Save Schedule</button>')

content = content.replace('<button className="btn secondary" onClick={saveSettings}>Save Metadata</button>', 
'<button className="btn secondary" onClick={saveSettings} disabled={isReadOnly} title={isReadOnly ? "자신이 배포한 Crew만 수정할 수 있습니다." : ""}>Save Metadata</button>')

content = content.replace('<button className="btn secondary" onClick={saveSettings}>Save Defaults</button>', 
'<button className="btn secondary" onClick={saveSettings} disabled={isReadOnly} title={isReadOnly ? "자신이 배포한 Crew만 수정할 수 있습니다." : ""}>Save Defaults</button>')

# 6. Pass isReadOnly to CrewDiagram
content = content.replace("<CrewDiagram graph={graph} crewId={selectedCrew.crew_id} version={selectedCrew.version} onUpdate={() => showCrew(selectedCrew)} />", "<CrewDiagram graph={graph} crewId={selectedCrew.crew_id} version={selectedCrew.version} onUpdate={() => showCrew(selectedCrew)} isReadOnly={isReadOnly} />")


with open('/Users/jck/WORK/DEV/company-crewai-amp-v2/admin/company-flow-server/frontend/src/components/CrewProcess.jsx', 'w') as f:
    f.write(content)
