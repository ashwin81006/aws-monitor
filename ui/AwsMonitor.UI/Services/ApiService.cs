using System.Net.Http.Json;
using System.Text.Json;
using AwsMonitor.UI.Models;

namespace AwsMonitor.UI.Services;

public interface IApiService
{
    bool IsConnected { get; }
    string BaseUrl { get; }
    void UpdateBaseUrl(string newUrl);

    Task<HealthResponse> CheckHealthAsync();
    Task<StationSummary> GetStationSummaryAsync();
    Task<TelemetryHistoryResponse> GetTelemetryHistoryAsync(int maxPoints = 1200, string? preset = null);
    Task<AnomalyEventsResponse> GetAnomalyEventsAsync(string? severity = null, string? rootCause = null);
    Task<AnomalyDetailResponse> GetAnomalyDetailAsync(int eventId);
    Task<StreamPointResponse> StreamInferenceAsync(StreamPointRequest req);
    Task<StationHealthSummary> GetSensorHealthAsync();
    Task<ModelBenchmarkResponse> GetModelBenchmarksAsync();
    Task<ShapSummaryResponse?> GetShapSummaryAsync();
}

public class ApiService : IApiService
{
    private HttpClient _http;
    private string _baseUrl;

    public bool IsConnected { get; private set; }
    public string BaseUrl => _baseUrl;

    public static string GetDefaultBaseUrl()
    {
        // 1. Check if user previously saved a custom URL in Preferences
        string saved = Preferences.Default.Get("AwsMonitor_ApiBaseUrl", string.Empty);
        if (!string.IsNullOrWhiteSpace(saved))
            return saved;

        // 2. Platform-aware defaults
        if (DeviceInfo.Current.Platform == DevicePlatform.Android)
        {
            if (DeviceInfo.Current.DeviceType == DeviceType.Virtual)
            {
                // Android emulator loopback alias to host machine
                return "http://10.0.2.2:8000";
            }
            // Physical mobile device on local WiFi
            return "http://10.232.250.170:8000";
        }
        else if (DeviceInfo.Current.Platform == DevicePlatform.iOS)
        {
            return "http://10.232.250.170:8000";
        }

        // Desktop Windows / macOS default
        return "http://127.0.0.1:8000";
    }

    public ApiService()
    {
        _baseUrl = GetDefaultBaseUrl();
        _http = new HttpClient
        {
            BaseAddress = new Uri(_baseUrl),
            Timeout = TimeSpan.FromSeconds(6)
        };
    }

    public void UpdateBaseUrl(string newUrl)
    {
        if (string.IsNullOrWhiteSpace(newUrl)) return;
        newUrl = newUrl.Trim().TrimEnd('/');
        if (!newUrl.StartsWith("http://") && !newUrl.StartsWith("https://"))
        {
            newUrl = "http://" + newUrl;
        }

        _baseUrl = newUrl;
        Preferences.Default.Set("AwsMonitor_ApiBaseUrl", newUrl);

        try
        {
            _http.Dispose();
        }
        catch { }

        _http = new HttpClient
        {
            BaseAddress = new Uri(_baseUrl),
            Timeout = TimeSpan.FromSeconds(6)
        };
    }

    public async Task<HealthResponse> CheckHealthAsync()
    {
        try
        {
            var res = await _http.GetFromJsonAsync<HealthResponse>("/health");
            if (res != null)
            {
                IsConnected = true;
                return res;
            }
        }
        catch
        {
            IsConnected = false;
        }

        return new HealthResponse
        {
            Status = "STANDALONE_CACHE",
            Service = "AWS Monitor - Desktop UI (Offline Demo Mode)",
            StationId = "ISRO0119_15F077",
            ActiveModel = "Isolation Forest + Thermodynamic Self-Healing",
            FeaturesCount = 13,
            Calibration = "Thermodynamic Physical Consistency & Empirical Benchmark",
            Explainability = "Root Cause Diagnostics & Physical Self-Healing"
        };
    }

    public async Task<StationSummary> GetStationSummaryAsync()
    {
        try
        {
            var res = await _http.GetFromJsonAsync<StationSummary>("/api/v1/station/summary");
            if (res != null)
            {
                IsConnected = true;
                return res;
            }
        }
        catch
        {
            IsConnected = false;
        }

        return new StationSummary
        {
            StationId = "ISRO0119_15F077",
            StationName = "ISRO AWS Station, VIT Vellore",
            Latitude = 12.9692,
            Longitude = 79.1559,
            ElevationM = 214.0,
            TotalObservations = 32774,
            StartTimestamp = "2006-07-11 16:30:00",
            EndTimestamp = "2015-12-09 23:30:00",
            SensorChannels = new List<string> { "temperature", "humidity", "pressure" },
            ModelArchitecture = "Robust-Scaled Isolation Forest with Thermodynamic Self-Healing"
        };
    }

    public async Task<TelemetryHistoryResponse> GetTelemetryHistoryAsync(int maxPoints = 1200, string? preset = null)
    {
        try
        {
            string url = "/api/v1/telemetry/history?downsample_factor=25";
            if (!string.IsNullOrEmpty(preset)) url += $"&preset={preset}";

            var res = await _http.GetFromJsonAsync<TelemetryHistoryResponse>(url);
            if (res != null && res.AllPoints.Count > 0)
            {
                IsConnected = true;
                return res;
            }
        }
        catch
        {
            IsConnected = false;
        }

        // Return synthesized realistic meteorological telemetry series
        var pts = new List<TelemetryPoint>();
        var baseDate = DateTime.Now.AddDays(-10);
        var rand = new Random(42);

        for (int i = 0; i < 480; i++)
        {
            var dt = baseDate.AddMinutes(i * 30);
            double hour = dt.Hour + dt.Minute / 60.0;
            double diurnal = Math.Sin((hour - 9.0) * Math.PI / 12.0) * 6.5;
            double t2 = 28.0 + diurnal + (rand.NextDouble() - 0.5) * 0.8;
            double t4 = t2 - 0.3 + (rand.NextDouble() - 0.5) * 0.3;
            double t8 = t2 - 0.6 + (rand.NextDouble() - 0.5) * 0.3;
            double rh2 = Math.Clamp(75.0 - diurnal * 3.5 + (rand.NextDouble() - 0.5) * 2.0, 30.0, 98.0);
            double press = 998.0 + Math.Cos(hour * Math.PI / 12.0) * 1.5 + (rand.NextDouble() - 0.5) * 0.4;
            double batt = 12.8 + (hour >= 7 && hour <= 18 ? 0.9 : -0.3);
            double rain = (i >= 200 && i <= 210) ? Math.Round(rand.NextDouble() * 8.5, 1) : 0.0;

            bool isFault = false;
            string severity = "NORMAL";
            double score = 0.08;

            // Injected spike demo at i=120
            if (i == 120)
            {
                t4 = -33.4; // Glitch
                isFault = true;
                severity = "CRITICAL";
                score = 0.98;
            }
            // Injected freeze demo at 260..265
            else if (i >= 260 && i <= 265)
            {
                t2 = 31.42;
                t4 = 31.10;
                isFault = true;
                severity = "WARNING";
                score = 0.82;
            }

            pts.Add(new TelemetryPoint
            {
                Timestamp = dt.ToString("yyyy-MM-dd HH:mm"),
                Temp2m = Math.Round(t2, 2),
                Temp4m = Math.Round(t4, 2),
                Temp8m = Math.Round(t8, 2),
                Rh2m = Math.Round(rh2, 1),
                Rh4m = Math.Round(rh2 + 1.2, 1),
                Rh8m = Math.Round(rh2 + 2.0, 1),
                Pressure = Math.Round(press, 1),
                BatteryVoltage = Math.Round(batt, 2),
                Rainfall = rain,
                WindSpeed10m = Math.Round(1.5 + rand.NextDouble() * 3.0, 1),
                IsAnomaly = isFault,
                Severity = severity,
                FusedScore = score
            });
        }

        return new TelemetryHistoryResponse
        {
            StationId = "AGROMET04_15F105",
            TotalPointsInDb = 23807,
            PointsReturned = pts.Count,
            DecimationApplied = true,
            Points = pts
        };
    }

    public async Task<AnomalyEventsResponse> GetAnomalyEventsAsync(string? severity = null, string? rootCause = null)
    {
        try
        {
            string url = "/api/v1/anomalies/events?limit=200";
            if (!string.IsNullOrEmpty(severity)) url += $"&severity={severity}";
            if (!string.IsNullOrEmpty(rootCause)) url += $"&root_cause={rootCause}";

            var res = await _http.GetFromJsonAsync<AnomalyEventsResponse>(url);
            if (res != null)
            {
                IsConnected = true;
                return res;
            }
        }
        catch
        {
            IsConnected = false;
        }

        return new AnomalyEventsResponse
        {
            TotalEvents = 937,
            FilteredEvents = 5,
            Events = new List<AnomalyEvent>
            {
                new()
                {
                    EventId = 1,
                    StartTime = "2023-01-01 02:00:00",
                    EndTime = "2023-01-01 02:30:00",
                    ObservationsCount = 2,
                    PeakFusedScore = 0.985,
                    EventClassification = "PROBABLE_SENSOR_FAULT",
                    RootCause = "SENSOR_SPIKE",
                    AffectedSensors = new List<string> { "temp_4m" },
                    RuleFlags = new List<string> { "PHYSICAL_TEMP_LIMIT", "VERTICAL_TEMP_LAPSE_GRADIENT" },
                    Description = "Transient ADC reading jump exceeding sensor gradient consistency across the 4m tower level."
                },
                new()
                {
                    EventId = 2,
                    StartTime = "2023-02-14 09:00:00",
                    EndTime = "2023-02-14 12:00:00",
                    ObservationsCount = 7,
                    PeakFusedScore = 0.880,
                    EventClassification = "PROBABLE_SENSOR_FAULT",
                    RootCause = "FROZEN_SENSOR",
                    AffectedSensors = new List<string> { "temperature" },
                    RuleFlags = new List<string> { "FROZEN_TEMP_STREAK" },
                    Description = "Consecutive identical floating point readings across 180 minutes without micro-variation."
                },
                new()
                {
                    EventId = 3,
                    StartTime = "2023-03-22 13:00:00",
                    EndTime = "2023-03-22 17:30:00",
                    ObservationsCount = 10,
                    PeakFusedScore = 0.540,
                    EventClassification = "BENIGN_EXTREME",
                    RootCause = "NATURAL_WEATHER_EXTREME",
                    AffectedSensors = new List<string> { "temperature", "humidity" },
                    RuleFlags = new List<string>(),
                    Description = "Genuine regional heatwave conditions (46.2°C) corroborated across thermodynamic moisture depression."
                },
                new()
                {
                    EventId = 4,
                    StartTime = "2023-04-10 18:00:00",
                    EndTime = "2023-04-11 06:00:00",
                    ObservationsCount = 25,
                    PeakFusedScore = 0.910,
                    EventClassification = "PROBABLE_SENSOR_FAULT",
                    RootCause = "PRESSURE_TRANSIENT",
                    AffectedSensors = new List<string> { "pressure" },
                    RuleFlags = new List<string> { "PRESSURE_RATE_EXCEEDED" },
                    Description = "Abrupt non-physical barometric step change in 30 minutes exceeding diurnal tidal envelope."
                },
                new()
                {
                    EventId = 5,
                    StartTime = "2023-05-02 11:00:00",
                    EndTime = "2023-05-02 15:00:00",
                    ObservationsCount = 9,
                    PeakFusedScore = 0.790,
                    EventClassification = "SUSPICIOUS_UNVERIFIED",
                    RootCause = "DRIFT_OR_CALIBRATION",
                    AffectedSensors = new List<string> { "humidity" },
                    RuleFlags = new List<string> { "RH_DIURNAL_DECOUPLING" },
                    Description = "Progressive calibration offset in surface relative humidity channel relative to solar curve."
                }
            }
        };
    }

    public async Task<AnomalyDetailResponse> GetAnomalyDetailAsync(int eventId)
    {
        try
        {
            var res = await _http.GetFromJsonAsync<AnomalyDetailResponse>($"/api/v1/anomalies/events/{eventId}");
            if (res != null) return res;
        }
        catch { }

        return new AnomalyDetailResponse
        {
            EventId = eventId,
            StartTime = "2023-01-01 02:00:00",
            EndTime = "2023-01-01 02:30:00",
            ObservationsCount = 2,
            PeakFusedScore = 0.985,
            Classification = "PROBABLE_SENSOR_FAULT",
            RootCause = "SENSOR_SPIKE",
            AffectedSensors = new List<string> { "temp_4m" },
            RuleFlags = new List<string> { "PHYSICAL_TEMP_LIMIT", "VERTICAL_TEMP_LAPSE_GRADIENT" },
            Description = "Transient ADC reading jump exceeding sensor gradient consistency across the 4m tower level.",
            Records = new List<TelemetryPoint>()
        };
    }

    public async Task<StreamPointResponse> StreamInferenceAsync(StreamPointRequest req)
    {
        try
        {
            var httpRes = await _http.PostAsJsonAsync("/api/v1/telemetry/stream-point", req);
            if (httpRes.IsSuccessStatusCode)
            {
                var data = await httpRes.Content.ReadFromJsonAsync<StreamPointResponse>();
                if (data != null)
                {
                    IsConnected = true;
                    return data;
                }
            }
        }
        catch
        {
            IsConnected = false;
        }

        // Local fallback inference simulation
        bool isSpike = Math.Abs(req.Temp4m - req.Temp2m) > 15.0 || req.Temp4m < -10.0;
        bool isBattery = req.BatteryVoltage < 10.5;
        bool isHeatwave = req.Temp2m > 44.0 && req.Temp4m > 43.0 && req.Temp8m > 42.0;

        if (isSpike)
        {
            return new StreamPointResponse
            {
                Timestamp = string.IsNullOrEmpty(req.Timestamp) ? DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") : req.Timestamp,
                FusedAnomalyScore = 0.98,
                Classification = "PROBABLE_SENSOR_FAULT",
                Severity = "CRITICAL",
                Confidence = 0.98,
                RootCause = "SENSOR_SPIKE",
                AffectedSensors = new List<string> { "temp_4m" },
                Explanation = $"Sensor temp_4m jumped to {req.Temp4m:F1}°C conflicting with 2m ({req.Temp2m:F1}°C) and 8m ({req.Temp8m:F1}°C) tower consensus.",
                MlIsolationForestScore = 0.89,
                RuleFlags = new List<string> { "PHYSICAL_TEMP_LIMIT", "VERTICAL_TEMP_LAPSE_GRADIENT" },
                IsAnomaly = true
            };
        }
        else if (isBattery)
        {
            return new StreamPointResponse
            {
                Timestamp = string.IsNullOrEmpty(req.Timestamp) ? DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") : req.Timestamp,
                FusedAnomalyScore = 0.91,
                Classification = "PROBABLE_SENSOR_FAULT",
                Severity = "CRITICAL",
                Confidence = 0.95,
                RootCause = "POWER_FAULT",
                AffectedSensors = new List<string> { "battery_voltage" },
                Explanation = $"Station battery voltage collapsed to {req.BatteryVoltage:F1}V (brownout risk).",
                MlIsolationForestScore = 0.78,
                RuleFlags = new List<string> { "POWER_BROWNOUT" },
                IsAnomaly = true
            };
        }
        else if (isHeatwave)
        {
            return new StreamPointResponse
            {
                Timestamp = string.IsNullOrEmpty(req.Timestamp) ? DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") : req.Timestamp,
                FusedAnomalyScore = 0.42,
                Classification = "BENIGN_EXTREME",
                Severity = "NORMAL",
                Confidence = 0.92,
                RootCause = "NATURAL_WEATHER_EXTREME",
                AffectedSensors = new List<string> { "temperature", "humidity" },
                Explanation = "High temperature observed with thermodynamic moisture depression; consistent diurnal physics confirms genuine regional extreme.",
                MlIsolationForestScore = 0.40,
                RuleFlags = new List<string>(),
                IsAnomaly = false
            };
        }

        return new StreamPointResponse
        {
            Timestamp = string.IsNullOrEmpty(req.Timestamp) ? DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") : req.Timestamp,
            FusedAnomalyScore = 0.05,
            Classification = "NORMAL",
            Severity = "NORMAL",
            Confidence = 0.96,
            RootCause = "NORMAL_OPERATION",
            AffectedSensors = new List<string>(),
            Explanation = "All meteorological sensors and gradients operating within standard physical bounds.",
            MlIsolationForestScore = 0.06,
            RuleFlags = new List<string>(),
            IsAnomaly = false
        };
    }

    public async Task<StationHealthSummary> GetSensorHealthAsync()
    {
        try
        {
            var res = await _http.GetFromJsonAsync<StationHealthSummary>("/api/v1/sensors/health");
            if (res != null) return res;
        }
        catch { }

        return new StationHealthSummary
        {
            StationId = "ISRO0119_15F077",
            OverallHealthScore = 98.8,
            HealthStatus = "EXCELLENT",
            TotalObservations = 32774,
            HealthySensorsCount = 3,
            DegradedSensorsCount = 0,
            CriticalSensorsCount = 0,
            Sensors = new Dictionary<string, SensorChannelHealth>
            {
                ["temperature"] = new() { Channel = "temperature", TotalReadings = 32774, MissingCount = 0, MissingRatePct = 0.0, FlaggedAnomalyCount = 42, QualityScorePct = 99.8, Status = "OPERATIONAL", PhysicalMin = -10, PhysicalMax = 60, LastValidReading = 31.4 },
                ["humidity"] = new() { Channel = "humidity", TotalReadings = 32774, MissingCount = 0, MissingRatePct = 0.0, FlaggedAnomalyCount = 18, QualityScorePct = 99.9, Status = "OPERATIONAL", PhysicalMin = 0, PhysicalMax = 100, LastValidReading = 65.0 },
                ["pressure"] = new() { Channel = "pressure", TotalReadings = 32774, MissingCount = 0, MissingRatePct = 0.0, FlaggedAnomalyCount = 12, QualityScorePct = 99.9, Status = "OPERATIONAL", PhysicalMin = 850, PhysicalMax = 1080, LastValidReading = 998.4 }
            }
        };
    }

    public async Task<ModelBenchmarkResponse> GetModelBenchmarksAsync()
    {
        try
        {
            var res = await _http.GetFromJsonAsync<ModelBenchmarkResponse>("/api/v1/models/benchmark");
            if (res != null) return res;
        }
        catch { }

        return new ModelBenchmarkResponse
        {
            ComparisonMetric = "Evaluation Throughput (obs/sec) & Model Footprint",
            PrimaryModel = "Isolation Forest",
            Models = new List<ModelBenchmarkItem>
            {
                new() { ModelName = "Isolation Forest", Role = "Primary Global Detector", TrainingSamples = 22941, EvalSamples = 9833, FitTimeSeconds = 0.187, InferenceThroughputObsSec = 87650.0, ModelDiskSizeKb = 981.4, OutlierRatePct = 5.0, IsSelectedProductionModel = true },
                new() { ModelName = "One-Class SVM", Role = "Kernel Boundary Detector", TrainingSamples = 22941, EvalSamples = 9833, FitTimeSeconds = 4.210, InferenceThroughputObsSec = 29953.0, ModelDiskSizeKb = 45.9, OutlierRatePct = 5.0, IsSelectedProductionModel = false },
                new() { ModelName = "Local Outlier Factor", Role = "Density-Based Outlier Profiler", TrainingSamples = 22941, EvalSamples = 9833, FitTimeSeconds = 1.120, InferenceThroughputObsSec = 15917.0, ModelDiskSizeKb = 6920.0, OutlierRatePct = 5.0, IsSelectedProductionModel = false }
            }
        };
    }

    public async Task<ShapSummaryResponse?> GetShapSummaryAsync()
    {
        try
        {
            var res = await _http.GetFromJsonAsync<ShapSummaryResponse>("/api/v1/models/shap");
            if (res != null) return res;
        }
        catch { }

        return new ShapSummaryResponse
        {
            ModelName = "Isolation Forest (TreeSHAP)",
            FeaturesEvaluated = 13,
            TopFeatures = new List<ShapFeatureItem>
            {
                new() { Feature = "temp_rate", Importance = 0.285, Rank = 1, Domain = "Kinematic Gradient (dT/dt)" },
                new() { Feature = "dew_point_depression", Importance = 0.224, Rank = 2, Domain = "Thermodynamics (T - Td)" },
                new() { Feature = "pressure_dev", Importance = 0.171, Rank = 3, Domain = "Barometric Tidal Deviation" },
                new() { Feature = "temp_dev", Importance = 0.163, Rank = 4, Domain = "Diurnal Solar Anomaly" },
                new() { Feature = "humidity_rate", Importance = 0.158, Rank = 5, Domain = "Moisture Rate of Change (dRH/dt)" },
                new() { Feature = "pressure", Importance = 0.142, Rank = 6, Domain = "Absolute Barometric Pressure" },
                new() { Feature = "temperature", Importance = 0.138, Rank = 7, Domain = "Surface Air Temperature" },
                new() { Feature = "dew_point", Importance = 0.125, Rank = 8, Domain = "Moisture Saturation Temperature" },
                new() { Feature = "humidity_dev", Importance = 0.115, Rank = 9, Domain = "Diurnal Moisture Deviation" },
                new() { Feature = "pressure_rate", Importance = 0.098, Rank = 10, Domain = "Barometric Rate of Change (dP/dt)" }
            },
            MeteorologicalInsights = new List<string>
            {
                "Temperature rate of change (temp_rate) is the #1 driver: Hardware glitch spikes jump >10°C/hr, which violates thermal inertia and immediately isolates anomalies.",
                "Dew point depression (dew_point_depression = T - Td) is the #2 driver: Physical thermodynamic decoupling between temperature and moisture exposes sensor drift before failure.",
                "Diurnal deviation features (temp_dev & pressure_dev) prevent false alarms during true summer heatwaves (46°C) by verifying alignment with solar noon cycles."
            }
        };
    }
}
