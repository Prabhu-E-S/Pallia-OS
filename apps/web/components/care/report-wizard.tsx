"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, MessageSquare, Mic, SlidersHorizontal, X, Zap } from "lucide-react";
import { reportsApi } from "@/lib/api/reports";
import { ApiErrorResponse } from "@/lib/api/client";
import type {
  CaregiverReport,
  CaregiverReportMode,
  ExtractedObservation,
  ObservationConfirmPayload,
  PatientSummary,
} from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { Badge } from "@/components/ui/badge";
import { VoiceRecorder } from "@/components/care/voice-recorder";
import {
  OBSERVATION_LABELS,
  REPORT_STATUS_LABELS,
  SOURCE_LABELS,
} from "@/lib/constants";

type Step = "mode" | "manual" | "voice" | "processing" | "review" | "done";

interface ReviewItem {
  type: ExtractedObservation["type"];
  value: string | null;
  unit: string | null;
  confidence: number | null;
  note: string | null;
  included: boolean;
}

function parseExtraction(report: CaregiverReport | null | undefined): ReviewItem[] {
  const raw = report?.extraction as
    | {
        observations?: {
          type: string;
          value: string | null;
          unit: string | null;
          confidence: number | null;
          note: string | null;
        }[]
      }
    | undefined;
  if (report?.extraction && Array.isArray(raw?.observations)) {
    return raw.observations.map((item) => ({
      type: item.type as ExtractedObservation["type"],
      value: item.value,
      unit: item.unit,
      confidence: item.confidence,
      note: item.note,
      included: true,
    }));
  }
  return [];
}

const MODES: {
  mode: CaregiverReportMode;
  title: string;
  description: string;
  icon: typeof Zap;
}[] = [
  {
    mode: "QUICK_STATUS",
    title: "Quick status",
    description: "Pain and a short note, in seconds.",
    icon: Zap,
  },
  {
    mode: "STRUCTURED",
    title: "Structured",
    description: "Sleep, food, mood and more in one pass.",
    icon: SlidersHorizontal,
  },
  {
    mode: "TEXT",
    title: "Free text",
    description: "Describe today in your own words.",
    icon: MessageSquare,
  },
  {
    mode: "VOICE",
    title: "Voice update",
    description: "Speak it — we transcribe and draft it.",
    icon: Mic,
  },
];

const SLEEP_OPTIONS = ["3", "4", "5", "6", "7", "8", "more than 8"];
const FOOD_OPTIONS = ["ate well", "ate a little", "not eating", "nourishing drinks only"];
const MOBILITY_OPTIONS = ["up and about", "moved to a chair", "stayed in bed"];
const MOOD_OPTIONS = ["calm", "happy", "low", "anxious", "irritable"];
const BREATHING_OPTIONS = ["comfortable", "short of breath", "laboured"];
const ENERGY_OPTIONS = ["energetic", "moderate", "tired", "low energy"];

export function ReportWizard({
  patient,
  presetReport,
  presetMode,
  onClose,
  onSaved,
}: {
  patient: PatientSummary;
  presetReport?: CaregiverReport;
  presetMode?: CaregiverReportMode;
  onClose: () => void;
  onSaved: () => void;
}) {
  const router = useRouter();
  const isReview = Boolean(presetReport && presetReport.status === "REVIEW_REQUIRED");

  const [step, setStep] = useState<Step>(
    isReview
      ? "review"
      : presetMode
        ? presetMode === "VOICE"
          ? "voice"
          : "manual"
        : "mode",
  );
  const [mode, setMode] = useState<CaregiverReportMode>(
    presetMode ?? (isReview ? "VOICE" : "QUICK_STATUS"),
  );
  const [painLevel, setPainLevel] = useState<string>("");
  const [sleepHours, setSleepHours] = useState("");
  const [foodIntake, setFoodIntake] = useState("");
  const [mobility, setMobility] = useState("");
  const [mood, setMood] = useState("");
  const [breathing, setBreathing] = useState("");
  const [energy, setEnergy] = useState("");
  const [generalConcern, setGeneralConcern] = useState("");
  const [notes, setNotes] = useState("");
  const [typedTranscript, setTypedTranscript] = useState("");
  const [useManualTranscript, setUseManualTranscript] = useState(false);

  const [reportId, setReportId] = useState<string | null>(presetReport?.id ?? null);
  const [report, setReport] = useState<CaregiverReport | null>(presetReport ?? null);
  const [transcript, setTranscript] = useState<string | null>(
    presetReport?.transcript ?? null,
  );
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>(() =>
    parseExtraction(presetReport),
  );
  const [notMentioned, setNotMentioned] = useState<string[]>(() => {
    const value = (presetReport?.extraction as { not_mentioned?: string[] } | undefined)
      ?.not_mentioned;
    return Array.isArray(value) ? value : [];
  });
  const [aiProvider, setAiProvider] = useState<string | null>(
    presetReport?.provider ?? null,
  );
  const [aiModelVersion, setAiModelVersion] = useState<string | null>(
    presetReport?.model_version ?? null,
  );
  const [aiConfidence, setAiConfidence] = useState<number | null>(
    presetReport?.confidence ?? null,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasManualContent = useMemo(() => {
    if (mode === "QUICK_STATUS") return painLevel !== "" || notes.trim() !== "";
    if (mode === "STRUCTURED") {
      return Boolean(
        sleepHours ||
          foodIntake ||
          mobility ||
          mood ||
          breathing ||
          energy ||
          generalConcern.trim() ||
          notes.trim(),
      );
    }
    return notes.trim() !== "";
  }, [mode, painLevel, notes, sleepHours, foodIntake, mobility, mood, breathing, energy, generalConcern]);

  async function ensureReport(): Promise<string> {
    if (reportId) return reportId;
    const created = await reportsApi().create(patient.id, {
      patient_id: patient.id,
      mode: "VOICE",
    });
    setReportId(created.id);
    setReport(created);
    return created.id;
  }

  async function submitManual() {
    setBusy(true);
    setError(null);
    try {
      await reportsApi().create(patient.id, {
        patient_id: patient.id,
        mode,
        pain_level: painLevel === "" ? null : Number(painLevel),
        sleep_hours: sleepHours || null,
        food_intake: foodIntake || null,
        mobility: mobility || null,
        mood: mood || null,
        breathing: breathing || null,
        energy: energy || null,
        general_concern: generalConcern.trim() || null,
        notes: notes.trim() || null,
      });
      setStep("done");
      onSaved();
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Unable to submit the report.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCaptured(blob: Blob) {
    setBusy(true);
    setError(null);
    setStep("processing");
    try {
      const id = await ensureReport();
      const result = await reportsApi().transcribe(patient.id, id, blob);
      setTranscript(result.transcript);
      await runExtraction(id);
    } catch (err) {
      if (err instanceof ApiErrorResponse && err.code === "VOICE_SERVICE_UNAVAILABLE") {
        setUseManualTranscript(true);
        setStep("voice");
      } else {
        setError(err instanceof ApiErrorResponse ? err.message : "Transcription failed.");
        setStep("voice");
      }
    } finally {
      setBusy(false);
    }
  }

  async function runExtraction(id: string) {
    const result = await reportsApi().extract(patient.id, id);
    setReport(result.report);
    setReportId(result.report.id);
    setNotMentioned(result.not_mentioned);
    setAiProvider(result.ai.provider);
    setAiModelVersion(result.ai.model_version);
    setAiConfidence(result.ai.confidence);
    setReviewItems(
      result.observations.map((item) => ({
        type: item.type,
        value: item.value,
        unit: item.unit,
        confidence: item.confidence,
        note: item.note,
        included: true,
      })),
    );
    setStep("review");
  }

  async function continueWithTypedTranscript() {
    setBusy(true);
    setError(null);
    try {
      const id = await ensureReport();
      await reportsApi().update(patient.id, id, { transcript: typedTranscript });
      setTranscript(typedTranscript);
      await runExtraction(id);
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Extraction failed.");
    } finally {
      setBusy(false);
    }
  }

  async function confirmReview() {
    const observations = reviewItems
      .filter((item) => item.included)
      .map((item) => ({
        type: item.type,
        value: item.value || null,
        unit: item.unit || null,
        confidence: item.confidence,
      }));
    const payload: ObservationConfirmPayload = {
      report_id: reportId as string,
      observations,
    };
    setBusy(true);
    setError(null);
    try {
      await reportsApi().confirm(patient.id, payload);
      setStep("done");
      onSaved();
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Confirmation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function cancelReport() {
    if (!reportId) {
      onClose();
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await reportsApi().cancel(patient.id, reportId);
      setStep("done");
      onSaved();
    } catch (err) {
      setError(err instanceof ApiErrorResponse ? err.message : "Cancellation failed.");
    } finally {
      setBusy(false);
    }
  }

  function updateItem(index: number, patch: Partial<ReviewItem>) {
    setReviewItems((items) =>
      items.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)),
    );
  }

  function close() {
    if (busy) return;
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Caregiver report">
      <div className="absolute inset-0 bg-slate-900/40" onClick={close} aria-hidden />
      <div className="absolute inset-x-0 bottom-0 top-auto max-h-[94vh] w-full overflow-y-auto rounded-t-2xl bg-surface shadow-xl sm:inset-0 sm:mx-auto sm:my-auto sm:max-h-none sm:h-fit sm:w-full sm:max-w-xl sm:rounded-xl">
        <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-3.5">
          <div className="flex min-w-0 items-center gap-2">
            {step === "manual" || step === "review" ? (
              <button
                type="button"
                onClick={() => setStep(isReview ? "mode" : "mode")}
                className="inline-flex h-7 w-7 items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                aria-label="Back"
              >
                <ArrowLeft className="h-4 w-4" aria-hidden />
              </button>
            ) : null}
            <h2 className="truncate text-sm font-semibold text-slate-900">
              {step === "done" ? "Report submitted" : `Care update for ${patient.full_name}`}
            </h2>
            {transcript ? (
              <Badge tone="teal" className="hidden sm:inline-flex">
                {REPORT_STATUS_LABELS[report?.status ?? "DRAFT"] ?? report?.status}
              </Badge>
            ) : null}
          </div>
          {!busy ? (
            <button
              type="button"
              onClick={close}
              className="inline-flex h-7 w-7 items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-800"
              aria-label="Close"
            >
              <X className="h-4 w-4" aria-hidden />
            </button>
          ) : null}
        </div>

        <div className="space-y-4 p-5">
          {error ? (
            <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800" role="alert">
              {error}
            </p>
          ) : null}

          {step === "mode" && (
            <div className="space-y-4">
              <p className="text-sm text-muted">How would you like to record today&apos;s update?</p>
              <div className="grid gap-3 sm:grid-cols-2">
                {MODES.map((option) => (
                  <button
                    key={option.mode}
                    type="button"
                    onClick={() => {
                      setMode(option.mode);
                      setStep("manual");
                      if (option.mode === "VOICE") setStep("voice");
                    }}
                    className="group rounded-lg border border-line-strong bg-surface p-4 text-left transition-colors hover:border-brand-400 hover:bg-brand-50/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                  >
                    <option.icon className="h-5 w-5 text-brand-600" aria-hidden />
                    <p className="mt-2 text-sm font-semibold text-slate-900">{option.title}</p>
                    <p className="mt-0.5 text-xs text-muted">{option.description}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === "manual" && (
            <form
              className="space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                void submitManual();
              }}
            >
              {mode === "QUICK_STATUS" ? (
                <QuickStatusFields painLevel={painLevel} setPainLevel={setPainLevel} setNotes={setNotes} notes={notes} />
              ) : null}
              {mode === "STRUCTURED" ? (
                <StructuredFields
                  sleepHours={sleepHours}
                  setSleepHours={setSleepHours}
                  foodIntake={foodIntake}
                  setFoodIntake={setFoodIntake}
                  mobility={mobility}
                  setMobility={setMobility}
                  mood={mood}
                  setMood={setMood}
                  breathing={breathing}
                  setBreathing={setBreathing}
                  energy={energy}
                  setEnergy={setEnergy}
                  generalConcern={generalConcern}
                  setGeneralConcern={setGeneralConcern}
                  notes={notes}
                  setNotes={setNotes}
                />
              ) : null}
              {mode === "TEXT" ? (
                <Field label="What happened today?" htmlFor="care-note">
                  <Textarea
                    id="care-note"
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                    placeholder="Describe how the day went — meals, sleep, how they felt…"
                  />
                </Field>
              ) : null}
              <div className="flex items-center justify-end gap-2 pt-1">
                <Button variant="ghost" onClick={() => setStep("mode")}>
                  Back
                </Button>
                <Button type="submit" disabled={busy || !hasManualContent}>
                  {busy ? "Submitting…" : "Submit update"}
                </Button>
              </div>
            </form>
          )}

          {step === "voice" && (
            <div className="space-y-4">
              {!useManualTranscript ? (
                <VoiceRecorder
                  onCaptured={(blob) => void handleCaptured(blob)}
                  onUnsupported={() => setUseManualTranscript(true)}
                  onError={(message) => setError(message)}
                />
              ) : null}
              {useManualTranscript ? (
                <div className="space-y-3">
                  <p className="text-sm text-muted">
                    No microphone available or speech-to-text is not configured here. Type what you
                    would like to record instead.
                  </p>
                  <Field label="Typed update" htmlFor="care-transcript">
                    <Textarea
                      id="care-transcript"
                      value={typedTranscript}
                      onChange={(event) => setTypedTranscript(event.target.value)}
                      placeholder="e.g. Pain is six out of ten this morning; slept about five hours."
                    />
                  </Field>
                  <Button
                    onClick={() => void continueWithTypedTranscript()}
                    disabled={busy || typedTranscript.trim() === ""}
                  >
                    {busy ? "Working…" : "Continue"}
                  </Button>
                </div>
              ) : (
                <p className="text-xs text-muted">
                  After recording, we&apos;ll transcribe it and draft the observations for your
                  review. Nothing is added to the record until you confirm it.
                </p>
              )}
              <div className="flex items-center justify-end gap-2">
                <Button variant="ghost" onClick={() => setStep("mode")}>
                  Back
                </Button>
              </div>
            </div>
          )}

          {step === "processing" && (
            <div className="py-10 text-center">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" aria-hidden />
              <p className="mt-3 text-sm text-muted">Transcribing and extracting observations…</p>
            </div>
          )}

          {step === "review" && (
            <ReviewStep
              transcript={transcript}
              items={reviewItems}
              notMentioned={notMentioned}
              provider={aiProvider}
              version={aiModelVersion}
              confidence={aiConfidence}
              updateItem={updateItem}
              onConfirm={() => void confirmReview()}
              onCancel={() => void cancelReport()}
              busy={busy}
            />
          )}

          {step === "done" && (
            <div className="py-8 text-center">
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                <Check className="h-6 w-6" aria-hidden />
              </span>
              <h3 className="mt-4 text-base font-semibold text-slate-900">
                {report?.status === "CONFIRMED" || !isReview
                  ? "Update confirmed"
                  : report?.status === "CANCELLED"
                    ? "Update cancelled"
                    : "Update submitted"}
              </h3>
              <p className="mx-auto mt-1 max-w-sm text-sm text-muted">
                {report?.status === "CANCELLED"
                  ? "The draft was cancelled and will not appear on the patient's record."
                  : "It is now part of the patient's record and timeline."}
              </p>
              <div className="mt-5 flex items-center justify-center gap-2">
                <Button onClick={close}>Done</Button>
                <Button variant="secondary" onClick={() => router.push(`/patients/${patient.id}`)}>
                  Open patient
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function QuickStatusFields({
  painLevel,
  setPainLevel,
  notes,
  setNotes,
}: {
  painLevel: string;
  setPainLevel: (value: string) => void;
  notes: string;
  setNotes: (value: string) => void;
}) {
  return (
    <div className="space-y-4">
      <Field label="Pain right now (0 = none, 10 = worst)" htmlFor="care-pain">
        <Select id="care-pain" value={painLevel} onChange={(event) => setPainLevel(event.target.value)}>
          <option value="">Not mentioned</option>
          {Array.from({ length: 11 }, (_, value) => (
            <option key={value} value={String(value)}>
              {value} — {value === 0 ? "no pain" : value === 10 ? "worst possible" : "mild to severe"}
            </option>
          ))}
        </Select>
      </Field>
      <Field label="Anything to add?" htmlFor="care-note">
        <Textarea
          id="care-note"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Optional short note, e.g. 'warm compress helped after dinner'"
        />
      </Field>
    </div>
  );
}

function StructuredFields({
  sleepHours,
  setSleepHours,
  foodIntake,
  setFoodIntake,
  mobility,
  setMobility,
  mood,
  setMood,
  breathing,
  setBreathing,
  energy,
  setEnergy,
  generalConcern,
  setGeneralConcern,
  notes,
  setNotes,
}: {
  sleepHours: string;
  setSleepHours: (value: string) => void;
  foodIntake: string;
  setFoodIntake: (value: string) => void;
  mobility: string;
  setMobility: (value: string) => void;
  mood: string;
  setMood: (value: string) => void;
  breathing: string;
  setBreathing: (value: string) => void;
  energy: string;
  setEnergy: (value: string) => void;
  generalConcern: string;
  setGeneralConcern: (value: string) => void;
  notes: string;
  setNotes: (value: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Sleep (hours)" htmlFor="care-sleep">
          <Select id="care-sleep" value={sleepHours} onChange={(event) => setSleepHours(event.target.value)}>
            <option value="">Not mentioned</option>
            {SLEEP_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value === "more than 8" ? "More than 8" : `${value} hours`}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Food intake" htmlFor="care-food">
          <Select id="care-food" value={foodIntake} onChange={(event) => setFoodIntake(event.target.value)}>
            <option value="">Not mentioned</option>
            {FOOD_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Mobility" htmlFor="care-mobility">
          <Select id="care-mobility" value={mobility} onChange={(event) => setMobility(event.target.value)}>
            <option value="">Not mentioned</option>
            {MOBILITY_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Mood" htmlFor="care-mood">
          <Select id="care-mood" value={mood} onChange={(event) => setMood(event.target.value)}>
            <option value="">Not mentioned</option>
            {MOOD_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Breathing" htmlFor="care-breathing">
          <Select id="care-breathing" value={breathing} onChange={(event) => setBreathing(event.target.value)}>
            <option value="">Not mentioned</option>
            {BREATHING_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Energy" htmlFor="care-energy">
          <Select id="care-energy" value={energy} onChange={(event) => setEnergy(event.target.value)}>
            <option value="">Not mentioned</option>
            {ENERGY_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <Field label="Any concern to flag?" htmlFor="care-concern">
        <Textarea
          id="care-concern"
          value={generalConcern}
          onChange={(event) => setGeneralConcern(event.target.value)}
          placeholder="Optional"
        />
      </Field>
      <Field label="Notes" htmlFor="care-notes">
        <Textarea
          id="care-notes"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Optional"
        />
      </Field>
    </div>
  );
}

function ReviewStep({
  transcript,
  items,
  notMentioned,
  provider,
  version,
  confidence,
  updateItem,
  onConfirm,
  onCancel,
  busy,
}: {
  transcript: string | null;
  items: ReviewItem[];
  notMentioned: string[];
  provider: string | null;
  version: string | null;
  confidence: number | null;
  updateItem: (index: number, patch: Partial<ReviewItem>) => void;
  onConfirm: () => void;
  onCancel: () => void;
  busy: boolean;
}) {
  return (
    <div className="space-y-4">
      {transcript ? (
        <div className="rounded-md border border-line bg-slate-50 px-3 py-2.5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Transcript</p>
          <p className="mt-1 text-sm text-slate-800">{transcript}</p>
        </div>
      ) : null}

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Drafted observations — review before confirming
        </p>
        {items.length === 0 ? (
          <p className="text-sm text-muted">
            Nothing measurable was extracted. Confirming will record the update without observations
            (the transcript is kept on the report).
          </p>
        ) : (
          <ul className="space-y-2">
            {items.map((item, index) => (
              <li
                key={`${item.type}-${index}`}
                className={`rounded-md border px-3 py-2.5 ${
                  item.included ? "border-line-strong" : "border-dashed border-line bg-slate-50 opacity-60"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-800">
                      {OBSERVATION_LABELS[item.type] ?? item.type}
                    </p>
                    {item.note ? <p className="mt-0.5 text-xs text-muted">{item.note}</p> : null}
                    {item.confidence !== null ? (
                      <p className="mt-1 text-xs text-slate-400">
                        Confidence {(item.confidence * 100).toFixed(0)}%
                      </p>
                    ) : null}
                  </div>
                  <label className="flex shrink-0 items-center gap-1.5 text-xs text-muted">
                    <input
                      type="checkbox"
                      checked={item.included}
                      onChange={(event) => updateItem(index, { included: event.target.checked })}
                      className="h-4 w-4 rounded border-line-strong accent-brand-600"
                    />
                    Include
                  </label>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <Field label="Value" className="col-span-2 sm:col-span-1">
                    <Input
                      value={item.value ?? ""}
                      onChange={(event) => updateItem(index, { value: event.target.value })}
                      disabled={!item.included}
                    />
                  </Field>
                  <Field label="Unit" className="col-span-2 sm:col-span-1">
                    <Input
                      value={item.unit ?? ""}
                      onChange={(event) => updateItem(index, { unit: event.target.value })}
                      disabled={!item.included}
                      placeholder="e.g. scale 0-10"
                    />
                  </Field>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {notMentioned.length > 0 ? (
        <div>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Not mentioned in the update
          </p>
          <div className="flex flex-wrap gap-1.5">
            {notMentioned.map((type) => (
              <Badge key={type} tone="neutral">
                {OBSERVATION_LABELS[type] ?? type}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      {provider || version ? (
        <p className="text-xs text-slate-400">
          Drafted by {provider ?? "AI"} ({SOURCE_LABELS.CAREGIVER_VOICE})
          {version ? ` · model v${version}` : ""}
          {confidence !== null ? ` · confidence ${(confidence * 100).toFixed(0)}%` : ""}
        </p>
      ) : null}

      <div className="flex items-center justify-between gap-2 border-t border-line pt-4">
        <Button variant="ghost" onClick={onCancel} disabled={busy}>
          Discard
        </Button>
        <Button onClick={onConfirm} disabled={busy}>
          {busy ? "Confirming…" : "Confirm for patient record"}
        </Button>
      </div>
    </div>
  );
}