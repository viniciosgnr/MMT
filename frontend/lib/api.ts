const API_URL = "http://localhost:8000";

async function fetchApi(path: string, options: RequestInit = {}) {
  const url = `${API_URL}${path}`;
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      const errorText = await res.text();
      console.error(`API Error [${res.status}] ${url}:`, errorText);
      throw new Error(`API Error: ${res.statusText}`);
    }
    return res.json();
  } catch (err) {
    console.error(`Network or Parsing Error ${url}:`, err);
    throw err;
  }
}

// Equipment API (M1)
export async function fetchEquipments(params?: { serial_number?: string; equipment_type?: string }) {
  const queryParams = new URLSearchParams();
  if (params?.serial_number) queryParams.append("serial_number", params.serial_number);
  if (params?.equipment_type) queryParams.append("equipment_type", params.equipment_type);
  const query = queryParams.toString();
  return fetchApi(`/api/equipment/${query ? `?${query}` : ""}`);
}

export async function createEquipment(data: any) {
  return fetchApi("/api/equipment/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function fetchInstrumentTags(params?: { tag_number?: string }) {
  const queryParams = new URLSearchParams();
  if (params?.tag_number) queryParams.append("tag_number", params.tag_number);
  const query = queryParams.toString();
  return fetchApi(`/api/equipment/tags${query ? `?${query}` : ""}`);
}

export async function fetchEquipmentHistory(equipmentId: number) {
  return fetchApi(`/api/equipment/${equipmentId}/history`);
}

export async function fetchTagHistory(tagId: number) {
  return fetchApi(`/api/equipment/tags/${tagId}/history`);
}

export async function installEquipment(data: { equipment_id: number; tag_id: number; installed_by: string }) {
  return fetchApi("/api/equipment/install", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function removeEquipment(installationId: number) {
  return fetchApi(`/api/equipment/remove/${installationId}`, {
    method: "POST",
  });
}

// Calibration API (M2)
export async function fetchCalibrationCampaigns(fpsoName?: string, status?: string) {
  const params = new URLSearchParams();
  if (fpsoName) params.append("fpso_name", fpsoName);
  if (status) params.append("status", status);

  const res = await fetch(`${API_URL}/api/calibration/campaigns?${params}`);
  if (!res.ok) throw new Error("Failed to fetch campaigns");
  return res.json();
}

export async function createCalibrationCampaign(data: any) {
  const res = await fetch(`${API_URL}/api/calibration/campaigns`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create campaign");
  return res.json();
}

export async function fetchCalibrationTasks(campaignId?: number, status?: string) {
  const params = new URLSearchParams();
  if (campaignId) params.append("campaign_id", campaignId.toString());
  if (status) params.append("status", status);

  const res = await fetch(`${API_URL}/api/calibration/tasks?${params}`);
  if (!res.ok) throw new Error("Failed to fetch tasks");
  return res.json();
}

export async function createCalibrationTask(data: any) {
  const res = await fetch(`${API_URL}/api/calibration/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create task");
  return res.json();
}

export async function submitCalibrationResults(taskId: number, data: any) {
  const res = await fetch(`${API_URL}/api/calibration/tasks/${taskId}/results`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to submit results");
  return res.json();
}

// M2 MVP: Calibration Workflow API
export async function planCalibration(taskId: number, planData: { procurement_ids?: number[], notes?: string }) {
  return fetchApi(`/api/calibration/tasks/${taskId}/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(planData),
  });
}

export async function executeCalibration(taskId: number, execData: {
  execution_date: string,
  completion_date: string,
  calibration_type: string,
  seal_number: string,
  seal_date: string,
  seal_location: string,
  seal_type?: string
}) {
  return fetchApi(`/api/calibration/tasks/${taskId}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(execData),
  });
}

export async function uploadCertificate(taskId: number, certData: {
  certificate_number: string,
  issue_date: string,
  uncertainty?: number,
  standard_reading?: number,
  equipment_reading?: number
}) {
  return fetchApi(`/api/calibration/tasks/${taskId}/certificate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(certData),
  });
}

export async function validateCertificate(taskId: number) {
  return fetchApi(`/api/calibration/tasks/${taskId}/certificate/validate`, {
    method: "POST",
  });
}

// M2 MVP: Seal Management API
export async function recordSealInstallation(sealData: {
  tag_id: number,
  seal_number: string,
  seal_type: string,
  seal_location: string,
  installation_date: string,
  installed_by: string,
  removal_reason?: string
}) {
  return fetchApi(`/api/calibration/seals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sealData),
  });
}

export async function getTagSealHistory(tagId: number) {
  return fetchApi(`/api/calibration/tags/${tagId}/seals`);
}

export async function getActiveSeals(tagIds?: number[]) {
  const params = tagIds ? `?tag_ids=${tagIds.join(",")}` : "";
  return fetchApi(`/api/calibration/seals/active${params}`);
}

// Chemical Analysis API (M3)
export async function fetchSamplingCampaigns(fpsoName?: string, status?: string) {
  const params = new URLSearchParams();
  if (fpsoName) params.append("fpso_name", fpsoName);
  if (status) params.append("status", status);

  const res = await fetch(`${API_URL}/api/chemical/campaigns?${params}`);
  if (!res.ok) throw new Error("Failed to fetch sampling campaigns");
  return res.json();
}

export async function createSamplingCampaign(data: any) {
  const res = await fetch(`${API_URL}/api/chemical/campaigns`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create sampling campaign");
  return res.json();
}

export async function fetchSamplePoints(fpsoName?: string) {
  const params = new URLSearchParams();
  if (fpsoName) params.append("fpso_name", fpsoName);
  const res = await fetch(`${API_URL}/api/chemical/sample-points?${params}`);
  if (!res.ok) throw new Error("Failed to fetch sample points");
  return res.json();
}

export async function createSamplePoint(data: any) {
  const res = await fetch(`${API_URL}/api/chemical/sample-points`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create sample point");
  return res.json();
}

export async function fetchSamples(fpsoName?: string, status?: string) {
  const params = new URLSearchParams();
  if (fpsoName) params.append("fpso_name", fpsoName);
  if (status) params.append("status", status);

  const res = await fetch(`${API_URL}/api/chemical/samples?${params}`);
  if (!res.ok) throw new Error("Failed to fetch samples");
  return res.json();
}

export async function fetchSampleDetails(sampleId: number) {
  const res = await fetch(`${API_URL}/api/chemical/samples/${sampleId}`);
  if (!res.ok) throw new Error("Failed to fetch sample details");
  return res.json();
}

export async function createSample(data: any) {
  const res = await fetch(`${API_URL}/api/chemical/samples`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create sample");
  return res.json();
}

export async function updateSampleStatus(sampleId: number, data: {
  status: string;
  comments?: string;
  user?: string;
  event_date?: string;
  url?: string;
  validation_status?: string;
}) {
  const res = await fetch(`${API_URL}/api/chemical/samples/${sampleId}/update-status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update sample status");
  return res.json();
}

export async function validateSampleResults(sampleId: number) {
  const res = await fetch(`${API_URL}/api/chemical/samples/${sampleId}/validate`);
  if (!res.ok) throw new Error("Failed to validate sample results");
  return res.json();
}

export async function addSampleResult(sampleId: number, data: any) {
  const res = await fetch(`${API_URL}/api/chemical/samples/${sampleId}/results`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to add sample result");
  return res.json();
}

export async function checkSamplingSlas() {
  const res = await fetch(`${API_URL}/api/chemical/check-slas`, {
    method: "POST"
  });
  if (!res.ok) throw new Error("Failed to check SLAs");
  return res.json();
}

// Maintenance API (M4)
export async function fetchMaintenanceRecords(status?: string) {
  const params = new URLSearchParams();
  if (status) params.append("status", status);

  const res = await fetch(`${API_URL}/api/maintenance/records?${params}`);
  if (!res.ok) throw new Error("Failed to fetch maintenance records");
  return res.json();
}

export async function createMaintenanceRecord(data: any) {
  const res = await fetch(`${API_URL}/api/maintenance/records`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create maintenance record");
  return res.json();
}

// Configuration API (M11)
export async function fetchHierarchyTree() {
  console.log("fetchHierarchyTree called");
  try {
    const data = await fetchApi("/api/config/hierarchy/tree");
    console.log("fetchHierarchyTree response received:", data);
    return data;
  } catch (err) {
    console.error("fetchHierarchyTree failed:", err);
    throw err;
  }
}

export async function createHierarchyNode(data: any) {
  return fetchApi("/api/config/hierarchy/nodes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteHierarchyNode(id: number) {
  return fetchApi(`/api/config/hierarchy/nodes/${id}`, {
    method: "DELETE",
  });
}

export async function fetchAttributeDefinitions(entityType?: string) {
  const params = new URLSearchParams();
  if (entityType) params.append("entity_type", entityType);
  return fetchApi(`/api/config/attributes?${params}`);
}

export async function createAttributeDefinition(data: any) {
  return fetchApi("/api/config/attributes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function fetchAttributeValues(entityId: number) {
  return fetchApi(`/api/config/values/${entityId}`);
}

export async function setAttributeValue(data: any) {
  return fetchApi("/api/config/values", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function fetchWells(fpso?: string) {
  const params = new URLSearchParams();
  if (fpso) params.append("fpso", fpso);
  return fetchApi(`/api/config/wells?${params}`);
}

export async function createWell(data: any) {
  return fetchApi("/api/config/wells", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function fetchHolidays(fpso?: string) {
  const params = new URLSearchParams();
  if (fpso) params.append("fpso", fpso);
  return fetchApi(`/api/config/holidays?${params}`);
}

export async function createHoliday(data: any) {
  return fetchApi("/api/config/holidays", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function fetchStockLocations(fpso?: string) {
  const params = new URLSearchParams();
  if (fpso) params.append("fpso", fpso);
  return fetchApi(`/api/config/stock-locations?${params}`);
}

export async function createStockLocation(data: any) {
  return fetchApi("/api/config/stock-locations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function fetchParameters(fpso?: string) {
  const params = new URLSearchParams();
  if (fpso) params.append("fpso", fpso);
  return fetchApi(`/api/config/parameters?${params}`);
}

export async function setParameter(data: any) {
  return fetchApi("/api/config/parameters", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function updateMaintenanceRecord(recordId: number, data: any) {
  const res = await fetch(`${API_URL}/api/maintenance/records/${recordId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update maintenance record");
  return res.json();
}
// Phase 1: Audit Simulation (Gap Closure)
export async function runAuditSimulation() {
  return fetchApi("/api/audit/simulate", {
    method: "POST"
  });
}

export async function runFCVerificationSimulation() {
  return fetchApi("/api/audit/fc-verification-simulate", {
    method: "GET",
  });
}





