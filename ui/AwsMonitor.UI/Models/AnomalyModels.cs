using System.Text.Json.Serialization;

namespace AwsMonitor.UI.Models;

public class StreamPointRequest
{
    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = string.Empty;

    [JsonPropertyName("temperature")]
    public double Temperature { get; set; } = 28.5;

    [JsonPropertyName("humidity")]
    public double Humidity { get; set; } = 65.0;

    [JsonPropertyName("pressure")]
    public double Pressure { get; set; } = 998.5;

    [JsonPropertyName("temp_2m")]
    public double Temp2m { get => Temperature; set => Temperature = value; }

    [JsonPropertyName("temp_4m")]
    public double Temp4m { get => Temperature; set => Temperature = value; }

    [JsonPropertyName("temp_8m")]
    public double Temp8m { get => Temperature; set => Temperature = value; }

    [JsonPropertyName("rh_2m")]
    public double Rh2m { get => Humidity; set => Humidity = value; }

    [JsonPropertyName("rh_4m")]
    public double Rh4m { get => Humidity; set => Humidity = value; }

    [JsonPropertyName("rh_8m")]
    public double Rh8m { get => Humidity; set => Humidity = value; }

    [JsonPropertyName("battery_voltage")]
    public double BatteryVoltage { get; set; } = 12.8;

    [JsonPropertyName("wind_speed_10m")]
    public double WindSpeed10m { get; set; } = 0.0;

    [JsonPropertyName("rainfall")]
    public double Rainfall { get; set; } = 0.0;
}

public class StreamPointResponse
{
    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = string.Empty;

    [JsonPropertyName("fused_anomaly_score")]
    public double FusedAnomalyScore { get; set; }

    [JsonPropertyName("anomaly_probability")]
    public double AnomalyProbability { get; set; }

    public double ResolvedScore => AnomalyProbability > 0 ? AnomalyProbability : FusedAnomalyScore;

    [JsonPropertyName("classification")]
    public string Classification { get; set; } = "NORMAL";

    [JsonPropertyName("severity")]
    public string Severity { get; set; } = "NORMAL";

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; } = 0.95;

    [JsonPropertyName("root_cause")]
    public string? RootCauseRaw { get; set; }

    [JsonPropertyName("probable_root_cause")]
    public string? ProbableRootCause { get; set; }

    private string? _rootCause;
    public string RootCause
    {
        get => !string.IsNullOrEmpty(_rootCause) ? _rootCause : (!string.IsNullOrEmpty(ProbableRootCause) ? ProbableRootCause : (!string.IsNullOrEmpty(RootCauseRaw) ? RootCauseRaw : "NORMAL_OPERATION"));
        set => _rootCause = value;
    }

    [JsonPropertyName("affected_sensors")]
    public List<string> AffectedSensors { get; set; } = new();

    [JsonPropertyName("explanation")]
    public string Explanation { get; set; } = string.Empty;

    [JsonPropertyName("if_score")]
    public double IfScore { get; set; }

    [JsonPropertyName("ml_isolation_forest_score")]
    public double MlIsolationForestScore { get; set; }

    [JsonPropertyName("rule_flags")]
    public List<string> RuleFlags { get; set; } = new();

    [JsonPropertyName("is_anomaly")]
    public bool IsAnomaly { get; set; }

    [JsonPropertyName("corrected_temperature")]
    public double? CorrectedTemperature { get; set; }

    [JsonPropertyName("corrected_humidity")]
    public double? CorrectedHumidity { get; set; }

    [JsonPropertyName("corrected_pressure")]
    public double? CorrectedPressure { get; set; }

    [JsonPropertyName("is_healed")]
    public bool IsHealed { get; set; }

    [JsonPropertyName("healing_method")]
    public string? HealingMethod { get; set; }
}

public class AnomalyEvent
{
    [JsonPropertyName("event_id")]
    public int EventId { get; set; }

    [JsonPropertyName("start_time")]
    public string StartTime { get; set; } = string.Empty;

    [JsonPropertyName("end_time")]
    public string EndTime { get; set; } = string.Empty;

    [JsonPropertyName("observations_count")]
    public int ObservationsCount { get; set; }

    [JsonPropertyName("observations")]
    public int? Observations { get; set; }

    [JsonPropertyName("peak_fused_score")]
    public double PeakFusedScore { get; set; }

    [JsonPropertyName("candidate_class")]
    public string? CandidateClass { get; set; }

    [JsonPropertyName("event_classification")]
    public string? EventClassification { get; set; }

    [JsonPropertyName("probable_root_cause")]
    public string? ProbableRootCause { get; set; }

    [JsonPropertyName("target_sensor")]
    public string? TargetSensor { get; set; }

    [JsonPropertyName("severity")]
    public string? Severity { get; set; }

    [JsonPropertyName("confidence")]
    public double? Confidence { get; set; }

    [JsonPropertyName("affected_sensors")]
    public List<string> AffectedSensors { get; set; } = new();

    [JsonPropertyName("rule_flags")]
    public List<string> RuleFlags { get; set; } = new();

    private string _rootCause = string.Empty;
    [JsonPropertyName("root_cause")]
    public string RootCause
    {
        get => !string.IsNullOrEmpty(_rootCause) ? _rootCause : (!string.IsNullOrEmpty(ProbableRootCause) ? ProbableRootCause.Replace("_", " ") : "Sensor Anomaly");
        set => _rootCause = value;
    }

    private string _description = string.Empty;
    [JsonPropertyName("description")]
    public string Description
    {
        get => !string.IsNullOrEmpty(_description) ? _description : $"{Severity ?? "High"} severity condition flagged in {TargetSensor ?? "core sensors"} with {PeakFusedScore * 100:F0}% confidence.";
        set => _description = value;
    }

    public Color SeverityColor => Severity == "CRITICAL"
        ? Color.FromArgb("#EF4444")
        : (Severity == "HIGH" ? Color.FromArgb("#F97316") : (Severity == "MODERATE" ? Color.FromArgb("#3B82F6") : Color.FromArgb("#F59E0B")));

    public string PeakScoreText => $"{PeakFusedScore * 100:F0}% Anomaly Score";

    public string ShortDescription => !string.IsNullOrEmpty(RootCause) ? RootCause : (!string.IsNullOrEmpty(Description) ? Description : "Sensor Anomaly");
}

public class AnomalyEventsResponse
{
    [JsonPropertyName("total_events")]
    public int TotalEvents { get; set; }

    [JsonPropertyName("limit")]
    public int Limit { get; set; }

    [JsonPropertyName("offset")]
    public int Offset { get; set; }

    [JsonPropertyName("counts_by_category")]
    public Dictionary<string, int>? CountsByCategory { get; set; }

    [JsonPropertyName("counts_by_severity")]
    public Dictionary<string, int>? CountsBySeverity { get; set; }

    [JsonPropertyName("filtered_events")]
    public int FilteredEvents { get; set; }

    [JsonPropertyName("events")]
    public List<AnomalyEvent> Events { get; set; } = new();
}

public class AnomalyDetailResponse
{
    [JsonPropertyName("event_id")]
    public int EventId { get; set; }

    [JsonPropertyName("start_time")]
    public string StartTime { get; set; } = string.Empty;

    [JsonPropertyName("end_time")]
    public string EndTime { get; set; } = string.Empty;

    [JsonPropertyName("duration_minutes")]
    public double DurationMinutes { get; set; }

    [JsonPropertyName("observations")]
    public int Observations { get; set; }

    [JsonPropertyName("observations_count")]
    public int ObservationsCountRaw { get; set; }

    private int? _observationsCount;
    public int ObservationsCount
    {
        get => _observationsCount ?? (Observations > 0 ? Observations : (ObservationsCountRaw > 0 ? ObservationsCountRaw : 1));
        set => _observationsCount = value;
    }

    [JsonPropertyName("peak_fused_score")]
    public double PeakFusedScore { get; set; }

    [JsonPropertyName("mean_fused_score")]
    public double MeanFusedScore { get; set; }

    [JsonPropertyName("candidate_class")]
    public string? CandidateClass { get; set; }

    [JsonPropertyName("classification")]
    public string? ClassificationRaw { get; set; }

    private string? _classification;
    public string Classification
    {
        get => !string.IsNullOrEmpty(_classification) ? _classification : (!string.IsNullOrEmpty(ClassificationRaw) ? ClassificationRaw : (!string.IsNullOrEmpty(CandidateClass) ? CandidateClass : "PROBABLE_SENSOR_FAULT"));
        set => _classification = value;
    }

    [JsonPropertyName("probable_root_cause")]
    public string? ProbableRootCause { get; set; }

    [JsonPropertyName("root_cause")]
    public string? RootCauseRaw { get; set; }

    private string? _rootCause;
    public string RootCause
    {
        get => !string.IsNullOrEmpty(_rootCause) ? _rootCause : (!string.IsNullOrEmpty(RootCauseRaw) ? RootCauseRaw : (!string.IsNullOrEmpty(ProbableRootCause) ? ProbableRootCause : "Sensor Anomaly"));
        set => _rootCause = value;
    }

    [JsonPropertyName("affected_sensors")]
    public List<string> AffectedSensors { get; set; } = new();

    [JsonPropertyName("rule_flags")]
    public List<string> RuleFlags { get; set; } = new();

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("explanation")]
    public string? Explanation { get; set; }

    public string ResolvedExplanation => !string.IsNullOrEmpty(Explanation) ? Explanation : (!string.IsNullOrEmpty(Description) ? Description : "Identified sensor inconsistency.");

    [JsonPropertyName("records")]
    public List<TelemetryPoint> Records { get; set; } = new();
}
