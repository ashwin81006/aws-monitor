using System.Text.Json.Serialization;

namespace AwsMonitor.UI.Models;

public class HealthResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "OFFLINE";

    [JsonPropertyName("service")]
    public string Service { get; set; } = string.Empty;

    [JsonPropertyName("station_id")]
    public string StationId { get; set; } = string.Empty;

    [JsonPropertyName("active_model")]
    public string ActiveModel { get; set; } = string.Empty;

    [JsonPropertyName("features_count")]
    public int FeaturesCount { get; set; }

    [JsonPropertyName("calibration")]
    public string Calibration { get; set; } = string.Empty;

    [JsonPropertyName("explainability")]
    public string Explainability { get; set; } = string.Empty;
}

public class StationSummary
{
    [JsonPropertyName("station_id")]
    public string StationId { get; set; } = "AGROMET04_15F105";

    [JsonPropertyName("station_name")]
    public string StationName { get; set; } = "Junagadh Agricultural University, Junagadh";

    [JsonPropertyName("location")]
    public string Location { get; set; } = "Gujarat, India";

    [JsonPropertyName("coordinates")]
    public Dictionary<string, double>? Coordinates { get; set; }

    [JsonPropertyName("latitude")]
    public double Latitude { get; set; } = 21.5035;

    [JsonPropertyName("longitude")]
    public double Longitude { get; set; } = 70.4428;

    [JsonPropertyName("elevation_m")]
    public double ElevationM { get; set; } = 61.0;

    [JsonPropertyName("total_observations")]
    public int TotalObservations { get; set; } = 23807;

    [JsonPropertyName("start_time")]
    public string StartTime { get; set; } = "2015-09-04 13:30:00";

    [JsonPropertyName("end_time")]
    public string EndTime { get; set; } = "2017-08-01 23:30:00";

    [JsonPropertyName("start_timestamp")]
    public string StartTimestamp { get => StartTime; set => StartTime = value; }

    [JsonPropertyName("end_timestamp")]
    public string EndTimestamp { get => EndTime; set => EndTime = value; }

    [JsonPropertyName("probable_faults_count")]
    public int ProbableFaultsCount { get; set; } = 625;

    [JsonPropertyName("possible_extremes_count")]
    public int PossibleExtremesCount { get; set; } = 91;

    [JsonPropertyName("uncertain_warnings_count")]
    public int UncertainWarningsCount { get; set; } = 217;

    [JsonPropertyName("overall_reliability_pct")]
    public double OverallReliabilityPct { get; set; } = 98.8;

    [JsonPropertyName("station_status")]
    public string StationStatus { get; set; } = "HEALTHY_ONLINE";

    [JsonPropertyName("sensor_channels")]
    public List<string> SensorChannels { get; set; } = new();

    [JsonPropertyName("model_architecture")]
    public string ModelArchitecture { get; set; } = "Isolation Forest (31 Meteorological Features)";

    public double ResolvedLatitude => Coordinates != null && Coordinates.TryGetValue("latitude", out var lat) ? lat : (Latitude != 0 ? Latitude : 21.5035);
    public double ResolvedLongitude => Coordinates != null && Coordinates.TryGetValue("longitude", out var lon) ? lon : (Longitude != 0 ? Longitude : 70.4428);
}

public class TelemetryPoint
{
    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = string.Empty;

    [JsonPropertyName("temp_2m")]
    public double? Temp2m { get; set; }

    [JsonPropertyName("temp_4m")]
    public double? Temp4m { get; set; }

    [JsonPropertyName("temp_8m")]
    public double? Temp8m { get; set; }

    [JsonPropertyName("rh_2m")]
    public double? Rh2m { get; set; }

    [JsonPropertyName("rh_4m")]
    public double? Rh4m { get; set; }

    [JsonPropertyName("rh_8m")]
    public double? Rh8m { get; set; }

    [JsonPropertyName("pressure")]
    public double? Pressure { get; set; }

    [JsonPropertyName("battery_voltage")]
    public double? BatteryVoltage { get; set; }

    [JsonPropertyName("rainfall")]
    public double? Rainfall { get; set; }

    [JsonPropertyName("wind_speed_10m")]
    public double? WindSpeed10m { get; set; }

    [JsonPropertyName("is_anomaly")]
    public bool IsAnomaly { get; set; }

    [JsonPropertyName("severity")]
    public string Severity { get; set; } = "NORMAL";

    [JsonPropertyName("fused_score")]
    public double FusedScore { get; set; }
}

public class TelemetryHistoryResponse
{
    [JsonPropertyName("station_id")]
    public string StationId { get; set; } = string.Empty;

    [JsonPropertyName("total_points")]
    public int TotalPoints { get; set; }

    [JsonPropertyName("total_points_in_db")]
    public int TotalPointsInDb { get; set; }

    [JsonPropertyName("points_returned")]
    public int PointsReturned { get; set; }

    [JsonPropertyName("downsample_factor")]
    public int DownsampleFactor { get; set; }

    [JsonPropertyName("decimation_applied")]
    public bool DecimationApplied { get; set; }

    [JsonPropertyName("series")]
    public List<TelemetryPoint> Series { get; set; } = new();

    [JsonPropertyName("points")]
    public List<TelemetryPoint> Points { get; set; } = new();

    [JsonIgnore]
    public List<TelemetryPoint> AllPoints => Series.Count > 0 ? Series : Points;
}

public class DatasetUploadResult
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("filename")]
    public string Filename { get; set; } = string.Empty;

    [JsonPropertyName("rows_received")]
    public int RowsReceived { get; set; }

    [JsonPropertyName("columns_received")]
    public int ColumnsReceived { get; set; }

    [JsonPropertyName("date_range")]
    public string DateRange { get; set; } = string.Empty;

    [JsonPropertyName("sensors_detected")]
    public List<string> SensorsDetected { get; set; } = new();

    [JsonPropertyName("flagged_faults_count")]
    public int FlaggedFaultsCount { get; set; }

    [JsonPropertyName("quality_score_pct")]
    public double QualityScorePct { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;
}
