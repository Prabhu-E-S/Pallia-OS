import { apiFetch } from "@/lib/api/client";
import type {
  CareTask,
  CareTaskCreate,
  CareTaskList,
  CareTaskUpdate,
  Observation,
  ObservationCreate,
  ObservationList,
  TimelineResponse,
  Visit,
  VisitCreate,
  VisitList,
  VisitUpdate,
} from "@/lib/api/types";

export function visitsApi() {
  return {
    list(params: { patientId?: string; status?: string } = {}) {
      const query = new URLSearchParams();
      if (params.patientId) query.set("patient_id", params.patientId);
      if (params.status) query.set("status", params.status);
      const qs = query.toString();
      return apiFetch<VisitList>(`/api/v1/visits${qs ? `?${qs}` : ""}`);
    },

    forPatient(patientId: string): Promise<VisitList> {
      return apiFetch<VisitList>(`/api/v1/patients/${patientId}/visits`);
    },

    get(visitId: string): Promise<Visit> {
      return apiFetch<Visit>(`/api/v1/visits/${visitId}`);
    },

    create(payload: VisitCreate): Promise<Visit> {
      return apiFetch<Visit>("/api/v1/visits", { method: "POST", body: payload });
    },

    update(visitId: string, payload: VisitUpdate): Promise<Visit> {
      return apiFetch<Visit>(`/api/v1/visits/${visitId}`, {
        method: "PATCH",
        body: payload,
      });
    },
  };
}

export function tasksApi() {
  return {
    list(params: { patientId?: string; status?: string; priority?: string } = {}) {
      const query = new URLSearchParams();
      if (params.patientId) query.set("patient_id", params.patientId);
      if (params.status) query.set("status", params.status);
      if (params.priority) query.set("priority", params.priority);
      const qs = query.toString();
      return apiFetch<CareTaskList>(`/api/v1/tasks${qs ? `?${qs}` : ""}`);
    },

    forPatient(patientId: string): Promise<CareTaskList> {
      return apiFetch<CareTaskList>(`/api/v1/patients/${patientId}/tasks`);
    },

    get(taskId: string): Promise<CareTask> {
      return apiFetch<CareTask>(`/api/v1/tasks/${taskId}`);
    },

    create(payload: CareTaskCreate): Promise<CareTask> {
      return apiFetch<CareTask>("/api/v1/tasks", { method: "POST", body: payload });
    },

    update(taskId: string, payload: CareTaskUpdate): Promise<CareTask> {
      return apiFetch<CareTask>(`/api/v1/tasks/${taskId}`, {
        method: "PATCH",
        body: payload,
      });
    },
  };
}

export function observationsApi() {
  return {
    forPatient(patientId: string): Promise<ObservationList> {
      return apiFetch<ObservationList>(`/api/v1/patients/${patientId}/observations`);
    },

    create(payload: ObservationCreate): Promise<Observation> {
      return apiFetch<Observation>("/api/v1/observations", {
        method: "POST",
        body: payload,
      });
    },

    record(
      payload: Omit<ObservationCreate, "patient_id"> & { patient_id: string },
    ): Promise<Observation> {
      return this.create(payload);
    },
  };
}

export function timelineApi() {
  return {
    forPatient(patientId: string): Promise<TimelineResponse> {
      return apiFetch<TimelineResponse>(`/api/v1/patients/${patientId}/timeline`);
    },
  };
}