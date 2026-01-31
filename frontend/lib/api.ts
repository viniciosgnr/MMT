const API_URL = "http://localhost:8000";

// Equipment API (M1)
export async function fetchEquipments() {
  const res = await fetch(`${API_URL}/equipment/`);
  if (!res.ok) {
    throw new Error("Failed to fetch equipments");
  }
  return res.json();
}

export async function createEquipment(data: any) {
  const res = await fetch(`${API_URL}/equipment/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error("Failed to create equipment");
  }
  return res.json();
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

export async function fetchSamples(campaignId?: number, status?: string) {
  const params = new URLSearchParams();
  if (campaignId) params.append("campaign_id", campaignId.toString());
  if (status) params.append("status", status);

  const res = await fetch(`${API_URL}/api/chemical/samples?${params}`);
  if (!res.ok) throw new Error("Failed to fetch samples");
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

export async function updateSampleStatus(sampleId: number, status: string) {
  const res = await fetch(`${API_URL}/api/chemical/samples/${sampleId}/status?status=${status}`, {
    method: "PUT",
  });
  if (!res.ok) throw new Error("Failed to update sample status");
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

export async function updateMaintenanceRecord(recordId: number, data: any) {
  const res = await fetch(`${API_URL}/api/maintenance/records/${recordId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update maintenance record");
  return res.json();
}
