import { apiFetch } from "@/lib/api/client";
import type {
  CaregiverReport,
  CaregiverReportCreate,
  CaregiverReportList,
  CaregiverReportUpdate,
  ExtractionOut,
  ObservationConfirmOut,
  ObservationConfirmPayload,
  RecentChangesOut,
  VoiceTranscriptOut,
} from "@/lib/api/types";

export function reportsApi() {
  return {
    list(patientId: string): Promise<CaregiverReportList> {
      return apiFetch<CaregiverReportList>(`/api/v1/patients/${patientId}/caregiver-reports`);
    },

    create(patientId: string, payload: CaregiverReportCreate): Promise<CaregiverReport> {
      return apiFetch<CaregiverReport>(`/api/v1/patients/${patientId}/caregiver-reports`, {
        method: "POST",
        body: payload,
      });
    },

    update(
      patientId: string,
      reportId: string,
      payload: CaregiverReportUpdate,
    ): Promise<CaregiverReport> {
      return apiFetch<CaregiverReport>(
        `/api/v1/patients/${patientId}/caregiver-reports/${reportId}`,
        { method: "PATCH", body: payload },
      );
    },

    cancel(patientId: string, reportId: string, reason?: string): Promise<CaregiverReport> {
      const query = reason ? `?reason=${encodeURIComponent(reason)}` : "";
      return apiFetch<CaregiverReport>(
        `/api/v1/patients/${patientId}/caregiver-reports/${reportId}/cancel${query}`,
        { method: "POST" },
      );
    },

    transcribe(patientId: string, reportId: string, audio: Blob): Promise<VoiceTranscriptOut> {
      const formData = new FormData();
      formData.append("report_id", reportId);
      formData.append("audio", audio, "report.mp3");
      return apiFetch<VoiceTranscriptOut>(`/api/v1/patients/${patientId}/voice/transcribe`, {
        method: "POST",
        formData,
      });
    },

    extract(patientId: string, reportId: string): Promise<ExtractionOut> {
      return apiFetch<ExtractionOut>(`/api/v1/patients/${patientId}/voice/extract`, {
        method: "POST",
        body: { report_id: reportId },
      });
    },

    confirm(patientId: string, payload: ObservationConfirmPayload): Promise<ObservationConfirmOut> {
      return apiFetch<ObservationConfirmOut>(
        `/api/v1/patients/${patientId}/observations/confirm`,
        { method: "POST", body: payload },
      );
    },

    recentChanges(patientId: string): Promise<RecentChangesOut> {
      return apiFetch<RecentChangesOut>(`/api/v1/patients/${patientId}/observations/recent`);
    },
  };
}