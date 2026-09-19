import { apiFetch } from "@/lib/api/client";
import type {
  CareGoal,
  CareGoalCreate,
  CareGoalUpdate,
  CarePlan,
  CarePlanUpdate,
  DashboardSummary,
  PatientCreate,
  PatientDetail,
  PatientList,
  PatientUpdate,
} from "@/lib/api/types";

export function patientsApi() {
  return {
    list(params: { status?: string; q?: string; limit?: number; offset?: number } = {}) {
      const query = new URLSearchParams();
      if (params.status) query.set("status", params.status);
      if (params.q) query.set("q", params.q);
      if (params.limit !== undefined) query.set("limit", String(params.limit));
      if (params.offset !== undefined) query.set("offset", String(params.offset));
      const qs = query.toString();
      return apiFetch<PatientList>(`/api/v1/patients${qs ? `?${qs}` : ""}`);
    },

    get(patientId: string): Promise<PatientDetail> {
      return apiFetch<PatientDetail>(`/api/v1/patients/${patientId}`);
    },

    create(payload: PatientCreate): Promise<PatientDetail> {
      return apiFetch<PatientDetail>("/api/v1/patients", {
        method: "POST",
        body: payload,
      });
    },

    update(patientId: string, payload: PatientUpdate): Promise<PatientDetail> {
      return apiFetch<PatientDetail>(`/api/v1/patients/${patientId}`, {
        method: "PATCH",
        body: payload,
      });
    },

    updateCarePlan(patientId: string, payload: CarePlanUpdate): Promise<CarePlan> {
      return apiFetch<CarePlan>(`/api/v1/patients/${patientId}/care-plan`, {
        method: "PUT",
        body: payload,
      });
    },

    createCareGoal(patientId: string, payload: CareGoalCreate): Promise<CareGoal> {
      return apiFetch<CareGoal>(`/api/v1/patients/${patientId}/care-plan/goals`, {
        method: "POST",
        body: payload,
      });
    },

    updateCareGoal(patientId: string, goalId: string, payload: CareGoalUpdate): Promise<CareGoal> {
      return apiFetch<CareGoal>(`/api/v1/patients/${patientId}/care-plan/goals/${goalId}`, {
        method: "PATCH",
        body: payload,
      });
    },
  };
}

export function dashboardApi() {
  return {
    summary(): Promise<DashboardSummary> {
      return apiFetch<DashboardSummary>("/api/v1/dashboard/summary");
    },
  };
}