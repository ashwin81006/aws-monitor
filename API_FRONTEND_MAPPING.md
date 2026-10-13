# AWS Monitor — Route-to-Screen Integration Mapping

This document provides a trace for every endpoint in the system, mapping its backend implementation to its presentation in the .NET MAUI frontend.

---

## Endpoint Mapping Matrix

| # | HTTP Method & Path | Backend Implementation & Response Schema | MAUI Service Method (`ApiService.cs`) | ViewModel Property (`MainViewModel.cs`) | UI Control / Chart (`MainPage.xaml`) | Data Source Nature | Integration Status |
|---|---|---|---|---|---|---|---|
| **1** | `GET /health`<br>`GET /api/v1/health` | `routes/health.py`<br>`Dict[str, Any]` | `CheckHealthAsync()` | `IsConnected`, `ConnectionStatusText`, `ConnectionStatusColor` | Top Status Chip:<br>`ConnectionStatusText` | Live when reachable; cached fallback with visible warning when offline | **Verified & Active**: Explicit production vs. offline demo mode badge rendered in header. |
| **2** | `GET /api/v1/station/summary` | `services/health_service.py`<br>`StationSummaryResponse` | `GetStationSummaryAsync()` | `StationId`, `StationName`, `LocationText`, `TotalReadingsCount`, `HealthScore`, `DateRangeText` | Header card & Summary cards in Overview Tab | Live when reachable; fallback when offline | **Verified & Active** |
| **3** | `GET /api/v1/telemetry/history` | `services/telemetry_service.py`<br>`TelemetryHistoryResponse` | `GetTelemetryHistoryAsync()` | `_allHistoryPoints` | Historical data stream buffer & interactive channel charts | Live when reachable; fallback when offline | **Verified & Active** |
| **4** | `GET /api/v1/anomalies/events` | `services/anomaly_service.py`<br>`AnomalyEventsResponse` | `GetAnomalyEventsAsync()` | `EventsList`, `ProblemIncidentsCount`, `IncidentChartSeries`, `IncidentYAxes` | Incidents List CollectionView & Failure Category Chart | Live when reachable; fallback when offline | **Verified & Active**: Dynamically binds `CountsByCategory` to `IncidentChartSeries` and labels; zero hardcoding. |
| **5** | `GET /api/v1/anomalies/events/{event_id}` | `services/anomaly_service.py`<br>`AnomalyEventDetail` | `GetAnomalyDetailAsync(int eventId)` | `SelectedEventDetailExplanation`, `SelectedEventRuleFlags`, `SelectedEventAffectedSensors` | Selected Incident Deep Dive Card in Incidents Tab | Live when incident is selected | **Verified & Active**: Automatically queries event details upon tapping any incident. |
| **6** | `GET /api/v1/sensors/health` | `services/health_service.py`<br>`SensorHealthResponse` | `GetSensorHealthAsync()` | `SensorsList`, `HealthScore`, `OverallStatusText` | Sensor Health 3-Column Card Grid in Incidents Tab | Live when reachable; fallback when offline | **Verified & Active**: Schema deserializes both list and dictionary representations seamlessly. |
| **7** | `GET /api/v1/models/benchmark` | `services/health_service.py`<br>`ModelBenchmarkResponse` | `GetModelBenchmarksAsync()` | `BenchmarkList`, `BenchmarkChartSeries`, `BenchmarkYAxes` | Throughput Row Chart & Model Cards in AI Models Tab | Live when reachable; fallback when offline | **Verified & Active**: Dynamically binds throughputs and labels from benchmark response. |
| **8** | `GET /api/v1/models/shap` | `ml/explain_shap.py`<br>`ShapSummaryResponse` | `GetShapSummaryAsync()` | `ShapChartSeries`, `ShapPrimaryInsight` | Horizontal Bar Chart & Insight Banner in AI Models Tab | Live dynamic TreeSHAP | **Verified & Active** |
| **9** | `POST /api/v1/models/shap/explain` | `ml/explain_shap.py`<br>`List[Dict[str, Any]]` | `ExplainObservationAsync(payload)` | `LocalShapList` | Local SHAP Feature Impact Card in Simulator Tab | Live per-observation TreeSHAP attributions | **Verified & Active**: Dynamically computes and displays top local feature impacts upon diagnostic execution. |
| **10** | `POST /api/v1/telemetry/stream-point` | `services/inference_service.py`<br>`TelemetryInferenceResponse` | `StreamInferenceAsync()` | `ResultAnomalyScore`, `ResultFaultType`, `HealedTemperature`, `ReconstructionDetailsText`, etc. | Diagnostic Results Card & Self-Healing Panel in Simulator Tab | Live inference when reachable; fallback when offline | **Verified & Active**: Seamless multi-model classification, self-healing, and local SHAP explanation. |

---

## Disconnects Resolved

1. **Schema Mismatch on Sensor Health**:
   - `DiagnosticModels.cs` updated to bind `List<SensorChannelHealth>` directly while exposing dictionary mappings.
2. **Incident Category Chart Hardcoding**:
   - `MainViewModel.cs` now dynamically creates `RowSeries` and `Axis.Labels` directly from `CountsByCategory`.
3. **Missing Local SHAP and Incident Details**:
   - `GetAnomalyDetailAsync` wired to incident tap gesture.
   - `ExplainObservationAsync` wired to simulator execution with dedicated UI attributions panel.
